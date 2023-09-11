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

    posts = models.Post.objects.filter(comfirmed=True).order_by('publish_date').annotate(
    like_count=Count('like'),
    favorite_count=Count('favorite'),
    comment_count=Count('comment')
    )
    
    # 分页部分
    per_page = 4
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
    return JsonResponse(response_data, safe=False)


def detail(request,post_id):
    detail = get_object_or_404(models.Post, id=post_id)
    # comment = get_object_or_404(models.Comment, post_id=post_id)
    post_data = model_to_dict(detail)
    post_data['content']=convert_img_src_to_absolute(request, post_data['content'])
    post_data['author_name']=detail.author.username
    post_data['mask_url']= request.build_absolute_uri(detail.mask.url) if detail.mask else None
    del post_data['mask']
    return JsonResponse(post_data)

def get_comments_by_post(request, post_id):
    comments = models.Comment.objects.select_related('author__profile').filter(post_id=post_id)
    comments_data = []
    for comment in comments:
      comment_dict = model_to_dict(comment)
      comment_dict["author_name"] = comment.author.username
      comment_dict["author_avatar"] = request.build_absolute_uri(comment.author.profile.avatar.url) if comment.author.profile.avatar else None  # 根据你的模型实际情况调整
      comments_data.append(comment_dict)

    # comments_data = [model_to_dict(comment) for comment in comments]
    
    return JsonResponse(comments_data, safe=False)

def register(request):
    return HttpResponse('注册')

def login(request):
    return HttpResponse('登录')

def my_like(request,user_id,post_id):
    return HttpResponse('user_id对post_id的点赞')

def my_favorite(request,user_id):
    return HttpResponse('user_id的收藏')



@csrf_exempt
# @login_required
def add_comment(request, post_id):
    if request.method == "POST":
        try:
            # 获取评论文本和parent_id
            data = json.loads(request.body)
            comment_text = data.get('text', '').strip()
            parent_id = data.get('parent_id', None)

            if not comment_text:
                return JsonResponse({'error': 'Comment text is required!'}, status=400)

            # 获取对应的帖子
            post = models.Post.objects.get(id=post_id)

            parent_comment = None
            if parent_id:
                parent_comment = models.Comment.objects.get(id=parent_id)

            # 创建新的评论
            comment = models.Comment(content=comment_text, author=request.user, post=post, parent=parent_comment)
            comment.save()

            # 返回新评论的数据
            response_data = {
                'id': comment.id,
                'content': comment.content,
                'author_name': comment.author.username,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'parent_id': comment.parent.id if comment.parent else None
            }
            return JsonResponse(response_data, status=201)

        except models.Post.DoesNotExist:
            return JsonResponse({'error': 'Post not found'}, status=404)
        except models.Comment.DoesNotExist:
            return JsonResponse({'error': 'Parent comment not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


