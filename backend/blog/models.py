from django.contrib.auth.models import User
from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
from ckeditor.fields import RichTextField
import os
from datetime import datetime
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to='avatars/', default='default.jpg')


def timestamped_upload_to(instance, filename):
    """
    Produces a timestamped filename for uploaded files.
    """
    # 获取文件扩展名
    extension = os.path.splitext(filename)[1].lower()
    # 使用当前的时间戳作为文件名
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
    # 返回新的文件名
    return f"uploads/{timestamp}{extension}"

class Post(models.Model):
    title = models.CharField(verbose_name='title',max_length=200)
    mask = models.ImageField(upload_to=timestamped_upload_to, blank=False, null=False,default='masks/default.jpg')
    content = RichTextUploadingField()
    author = models.ForeignKey(User, on_delete=models.CASCADE,verbose_name='author')
    comfirmed = models.BooleanField(default=False)
    publish_date = models.DateTimeField(auto_now_add=True,verbose_name='publish time')
    update_time = models.DateTimeField(auto_now_add=True,verbose_name='update_time')
     
    def __str__(self):
        return f"{self.author}—{self.title}"

class Comment(MPTTModel):
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    # parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)  # 自关联到自己
    created_at = models.DateTimeField(auto_now_add=True)
    
    class MPTTMeta:
        order_insertion_by = ['content']

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE,null=True,blank=True) 
    post = models.ForeignKey(Post, on_delete=models.CASCADE) 
    created_at = models.DateTimeField(auto_now_add=True)

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
