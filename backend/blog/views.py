from django.shortcuts import render,HttpResponse,get_object_or_404, redirect
from django.http import JsonResponse
from . import models
from . import forms
from django.forms.models import model_to_dict
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import re
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from PIL import Image, ImageDraw, ImageFont
import random
import string
import requests
from django.db.models import Q
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import IntegrityError, OperationalError
from .serializers import PostSerializer

def generate_random_string(length=5):
    """生成一个随机字符串，用于验证码"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def get_captcha(request):
    # 生成随机字符串
    captcha_str = generate_random_string()

    # 保存到session中，稍后用于验证
    request.session['captcha'] = captcha_str

    # 使用Pillow创建一个图像并将随机字符串写入图像
    img = Image.new('RGB', (120, 50), color = (73, 109, 137))
    d = ImageDraw.Draw(img)
    fnt = ImageFont.truetype('/static/tff/CASTELAR.TTF', 25)  # 路径需要指向一个实际的.ttf字体文件
    d.text((10,10), captcha_str, font=fnt, fill=(255, 255, 0))

    # 将图像保存为PNG并发送到客户端
    response = HttpResponse(content_type='image/png')
    img.save(response, 'PNG')
    return response



def convert_img_src_to_absolute(request, html_content):
    def replacer(match):
        # 获取匹配到的相对路径
        relative_path = match.group(1)
        
        # 使用build_absolute_uri转换为绝对路径
        absolute_path = request.build_absolute_uri(relative_path)
        return f'src="{absolute_path}"'

    # 使用正则表达式替换所有的<img>标签中的src属性值
    return re.sub(r'src="(/[^"]+)"', replacer, html_content)

# Create your views here.
def index(request):

    posts = models.Post.objects.filter(comfirmed=True).order_by('-publish_date').annotate(
    like_count=Count('like'),
    favorite_count=Count('favorite'),
    comment_count=Count('comment')
    )
    
    # 分页部分
    per_page = 8
    page = request.GET.get('page', 1)
    paginator = Paginator(posts, per_page)

    try:
        current_page_posts = paginator.page(page)
    except PageNotAnInteger:
        # 如果页数不是整数，返回第一页。
        current_page_posts = paginator.page(1)
    except EmptyPage:
        # 如果页数超出范围，返回最后一页。
        current_page_posts = paginator.page(paginator.num_pages)
    
    # 检查是否还有更多的页面
    has_more = True if int(page) < paginator.num_pages else False


    data = [
        {
            **{k: v if k != 'author' else post.author.username for k, v in model_to_dict(post).items() if k != 'mask'}, 
            'mask_url': request.build_absolute_uri(post.mask.url) if post.mask else None,
            'like_count': post.like_count,
            'favorite_count': post.favorite_count,
            'comment_count': post.comment_count,
        }
        for post in current_page_posts
    ]
    response_data = {
        "results": data,
        "has_more": has_more,
    }
    return JsonResponse(response_data, safe=True)

@csrf_exempt
def search(request):
    if request.method == 'POST':
        try:
            user_id = request.POST['userId']
            search = request.POST['query']
            results = models.Post.objects.filter(Q(content__icontains=search))
            history=models.History(query=search, user_id=user_id)
            history.save()
            serialized_data = PostSerializer(results, many=True).data
            return JsonResponse({'success': True,'data': serialized_data}, status=200)
        except models.Post.DoesNotExist:
            return JsonResponse({'error': 'Post not found'}, status=404)
        except models.User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
            
            

def detail(request,post_id):
    detail = get_object_or_404(models.Post, id=post_id)
    # comment = get_object_or_404(models.Comment, post_id=post_id)
    post_data = model_to_dict(detail)
    post_data['content']=convert_img_src_to_absolute(request, post_data['content'])
    post_data['author_name']=detail.author.username
    post_data['mask_url']= request.build_absolute_uri(detail.mask.url) if detail.mask else None
    del post_data['mask']
    return JsonResponse(post_data)

def profile(request):
    user_id = request.GET.get('userId')
    user = get_object_or_404(models.User, id=user_id)
    avatar_url = get_object_or_404(models.UserProfile, user_id=user_id)
    return JsonResponse({
                     'success': True,
                     'user': {
                         'id': user.id,
                         'username': user.username,
                         'email': user.email,
                        #  'avatar':avatar_url.avatar.url,
                         'avatar':request.build_absolute_uri(avatar_url.avatar.url),
                     }
                })

def my_posts(request):
    user_id = request.GET.get('userId')
    posts = models.Post.objects.filter(comfirmed=True,author_id=1).order_by('-publish_date').annotate(like_count=Count('like'),
    favorite_count=Count('favorite'),
    comment_count=Count('comment'))
    data = [
        {
            **{k: v if k != 'author' else post.author.username for k, v in model_to_dict(post).items() if k != 'mask'}, 
            'mask_url': request.build_absolute_uri(post.mask.url) if post.mask else None,
            'like_count': post.like_count,
            'favorite_count': post.favorite_count,
            'comment_count': post.comment_count,
        }
        for post in posts
    ]
    
    return JsonResponse(data, safe=False)
         
def my_favorites(request):
    user_id = request.GET.get('userId')
    fav_post_ids=models.Favorite.objects.filter(user_id=1).order_by('-created_at').values_list('post_id',flat=True)
    fav_posts = models.Post.objects.filter(id__in=fav_post_ids,comfirmed=True).annotate(
        like_count=Count('like'),
        favorite_count=Count('favorite'),
        comment_count=Count('comment')
    )
    data = [
        {
            **{k: v if k != 'author' else post.author.username for k, v in model_to_dict(post).items() if k != 'mask'}, 
            'mask_url': request.build_absolute_uri(post.mask.url) if post.mask else None,
            'like_count': post.like_count,
            'favorite_count': post.favorite_count,
            'comment_count': post.comment_count,
        }
        for post in fav_posts
    ]
    
    return JsonResponse(data, safe=False)

def my_likes(request):
    user_id = request.GET.get('userId')
    liked_post_ids=models.Like.objects.filter(user_id=1).order_by('-created_at').values_list('post_id',flat=True)
    liked_posts = models.Post.objects.filter(id__in=liked_post_ids,comfirmed=True).annotate(
        like_count=Count('like'),
        favorite_count=Count('favorite'),
        comment_count=Count('comment')
    )
    
    data = [
        {
            **{k: v if k != 'author' else post.author.username for k, v in model_to_dict(post).items() if k != 'mask'}, 
            'mask_url': request.build_absolute_uri(post.mask.url) if post.mask else None,
            'like_count': post.like_count,
            'favorite_count': post.favorite_count,
            'comment_count': post.comment_count,
        }
        for post in liked_posts
    ]
    
    return JsonResponse(data, safe=False)   
    
    
def get_comments_by_post(request, post_id):
    page_size = 5
    page_num = request.GET.get('page', 1)
    comments = models.Comment.objects.select_related('author__profile').filter(post_id=post_id).order_by('-created_at')
    paginator = Paginator(comments, page_size)
    current_page = paginator.page(page_num)
    has_more = current_page.has_next()
    comments_data = []
    for comment in current_page:
      comment_dict = model_to_dict(comment)
      comment_dict["author_name"] = comment.author.username
      comment_dict["created_at"] = comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
      comment_dict["author_avatar"] = request.build_absolute_uri(comment.author.profile.avatar.url) if comment.author.profile.avatar else None  # 根据你的模型实际情况调整
      comments_data.append(comment_dict)

    response_data = {
     'comments': comments_data,
     'has_more': has_more
    }
    return JsonResponse(response_data, safe=False) 
     

def register(request):
    return HttpResponse('注册')

@csrf_exempt
def login(request):
    if request.method == "POST":
        try:
            # 获取登录信息
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            recaptcha_response = data.get('captchaResponse')
            # 通过 Google 进行验证
            result = requests.post('https://www.google.com/recaptcha/api/siteverify', data={
                 'secret': '6LdjBtEoAAAAAHsViydgDVRZ_FnWBljni_V84RJd',  # 替换为你的 reCAPTCHA 密钥
                 'response': recaptcha_response
            })
             # 将响应解析为 JSON
            result_json = result.json()
            # 检查是否成功
            if result_json.get('success'):
                # reCAPTCHA 验证成功
                # 获取对应的用户
                user = models.User.objects.get(username=username)
                # avatar_url = models.UserProfile.objects.get(user_id=user.id)
                if user.check_password(password):
                    refresh = RefreshToken.for_user(user)
                    return JsonResponse({
                     'success': True,
                    #  'refresh_token': str(refresh),
                     'access_token': str(refresh.access_token),
                     'user': {
                         'id': user.id,
                        #  'username': user.username,
                        #  'email': user.email,
                        #  'avatar':request.build_absolute_uri(avatar_url.avatar.url),
                     }
                })
                else:
                    return JsonResponse({'error': 'password is wrong'})
            else:
                # reCAPTCHA 验证失败
                return JsonResponse({'error': result_json.get('error-codes')[0]})
        except models.User.DoesNotExist:
            return JsonResponse({'error': 'User not found'})
        except models.UserProfile.DoesNotExist:
            return JsonResponse({'error': 'UserProfile not found'})
        except Exception as e:
            return JsonResponse({'error': str(e)})
    else:
        return JsonResponse({'error': 'Invalid request method'})



@csrf_exempt
def add_like(request,post_id,comment_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            author_id = data.get('user')
            # 创建新的like
            user = get_object_or_404(models.User, id=author_id)
            post = get_object_or_404(models.Post, id=post_id)
            comment = None
            if comment_id:
                comment = get_object_or_404(models.Comment, id=comment_id)
            like = models.Like(user=user, post=post, comment=comment)
            like.save()
            return JsonResponse({'success': True}, status=200)

        except models.Post.DoesNotExist:
            return JsonResponse({'error': 'Post not found'}, status=404)
        except models.User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except models.Comment.DoesNotExist:
            return JsonResponse({'error': 'Parent comment not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

def my_favorite(request,user_id):
    return HttpResponse('user_id的收藏')



@csrf_exempt
# @login_required
def add_comment(request, post_id):
    if request.method == "POST":
        try:
            # 获取评论文本和parent_id
            data = json.loads(request.body)
            content = data.get('text', '').strip()
            author_id = data.get('user')
            parent_id = data.get('parent', None)
            #获取userprofile中的头像
            userprofile= models.UserProfile.objects.get(user_id=author_id)
            avatar = request.build_absolute_uri(userprofile.avatar.url)
            # 创建新的评论
            comment = models.Comment(content=content, author_id=author_id, post_id=post_id, parent_id=parent_id)
            comment.save()
            response_data = {
            'author': author_id,
            'author_avatar': avatar,
            'author_name': comment.author.username,
            'content': content,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'id': comment.id,
            'parent': parent_id,
            'post': post_id,
        }

            # 返回新评论的数据
            return JsonResponse({
                'success': True,'response_data': response_data}, status=200)

        except models.Post.DoesNotExist:
            return JsonResponse({'error': 'Post not found'}, status=404)
        except models.User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except models.Comment.DoesNotExist:
            return JsonResponse({'error': 'Parent comment not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
@csrf_exempt
def change_avatar(request):
    if request.method == "POST":
        user_id = request.POST['userId']
        try:
            profile = get_object_or_404(models.UserProfile, user_id=user_id)
            profile.avatar = request.FILES['avatar']
            profile.save()
            return JsonResponse({"success": True, "message": "Avatar updated successfully!"})
        except models.UserProfile.DoesNotExist:
            return JsonResponse({'error':'User not found'},status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)



@csrf_exempt
def add_posts(request):
    
    if request.method == 'POST':
        try:
            
            # 获取数据
            user_id = request.POST.get('userId')
            title = request.POST.get('title')
            content = request.POST.get('content')
            is_public = request.POST.get('isPublic').lower() == "true"  # 前端只会是字符串，==是判断
            image = request.FILES.get('image')
            
            post = models.Post(title=title,content=content,author_id=user_id,mask=image,comfirmed=is_public)
            post.save()
            return JsonResponse({"success":True,"message":'帖子已成功发布！'},status=200)
            
        except IntegrityError:
                return JsonResponse({'error': '数据完整性错误'}, status=500)
        except OperationalError:
                return JsonResponse({'error': '数据库操作错误'}, status=500)
        except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        
    else:
        return JsonResponse({'error': '错误的请求方法'}, status=400)
