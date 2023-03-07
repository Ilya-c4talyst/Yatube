from django.urls import path

from . import views

app_name = 'posts'

urlpatterns = [
    path(
        '',
        views.index,
        name='index'
    ),
    path(
        'group/<slug:slug>/',
        views.group_posts,
        name='group_list'
    ),
    path(
        'profile/<str:username>/',
        views.profile,
        name='profile'
    ),
    path(
        'posts/<int:post_id>/',
        views.post_detail,
        name='post_detail'
    ),
    path(
        'create/',
        views.post_create,
        name='post_create'
    ),
    path(
        'posts/<int:post_id>/edit/',
        views.post_edit,
        name='post_edit'
    ),
    path(
        'game/',
        views.game,
        name='game'
    ),
    path(
        'game/game_first/',
        views.game_tetris,
        name='game_first'
    ),
    path(
        'game/game_second/',
        views.game_snake,
        name='game_second'
    ),
    path(
        'posts/<int:post_id>/comment/',
        views.add_comment,
        name='add_comment'
    ),
    path(
        'follow/',
        views.follow_index,
        name='follow_index'
    ),
    path(
        'profile/<str:username>/follow/',
        views.profile_follow,
        name='profile_follow'
    ),
    path(
        'profile/<str:username>/unfollow/',
        views.profile_unfollow,
        name='profile_unfollow'
    ),
]
