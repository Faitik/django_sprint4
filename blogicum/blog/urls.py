from django.urls import path
from . import views
from django.views.generic import DetailView
from  blog.models import Post  



app_name = 'blog'

urlpatterns = [
    path('', views.index, name='index'),                             #1
    path(
        'posts/<int:id>/', views.PostDetailView.as_view(),
        name='post_detail'
    ),                                                               #2
    path(
        'category/<slug:category_slug>/',
        views.category_posts, name='category_posts'),                #3
    path('posts/create/', views.post_create, name='create_post'),

    path(
        'posts/<int:post_id>/edit/',
        views.EditPostViews.as_view(),                                #4
        name='edit_post',
    ),
    path(
        'posts/<int:post_id>/delete/',
        views.DeletePostView.as_view(),                               #5
        name='delete_post',
    ),
    path(
        'posts/<int:post_id>/edit_comment/', 
        views.CreateView.as_view(),                                   #6
        name='edit_comment',
    ),
    path(
        'profile/<str:username>',
        views.ProfileDetailView.as_view(),                            #7
        name='profile'
    ),
    path(
        'posts/<post_id>/comment/',
        views.CommentCreateView.as_view(),                            #8
        name='comment'
    ),

    path(
        'profile/edit/',
        views.ProfileUpdateView.as_view(),                            #9
        name='edit_profile'
    ),
    path(
        'posts/<post_id>/edit_comment/<comment_id>/',
        views.CommentUpdateView.as_view(),                            #10
        name='edit_comment'
    ),

    path(
        'posts/<post_id>/delete_comment/<comment_id>/',
        views.CommentDeleteView.as_view(),                            #11
        name='delete_comment'
    ),

]
