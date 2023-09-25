
from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('index/',views.index,name='index'),
    path('get_captcha/',views.get_captcha,name='get_captcha'),
    path('login/',views.login,name='login'),
    path('profile/',views.profile,name='profile'),
    path('detail/<int:post_id>',views.detail,name='detail'),
    path('comment/<int:post_id>',views.get_comments_by_post,name='get_comments_by_post'),
    path('add_comment/<int:post_id>',views.add_comment,name='add_comment'),
]
