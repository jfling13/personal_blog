
from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('index/',views.index,name='index'),
    path('get_captcha/',views.get_captcha,name='get_captcha'),
    path('login/',views.login,name='login'),
    path('add_like/<int:post_id>/<int:comment_id>',views.add_like,name="add_like"),
    path('profile/',views.profile,name='profile'),
    path('search/',views.search,name='search'),
    path('add_posts/',views.add_posts,name='add_posts'),
    path('change_avatar/',views.change_avatar,name='change_avatar'),
    path('my_posts/',views.my_posts,name='my_posts'),
    path('my_favorites/',views.my_favorites,name='my_favorites'),
    path('my_likes/',views.my_likes,name='my_likes'),
    path('detail/<int:post_id>',views.detail,name='detail'),
    path('comment/<int:post_id>',views.get_comments_by_post,name='get_comments_by_post'),
    path('add_comment/<int:post_id>',views.add_comment,name='add_comment'),
]
