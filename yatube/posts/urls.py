from django.urls import path
from . import views


app_name = 'posts'


urlpatterns = [
    # Главная страница
    path('', views.index, name = 'index'),

    path('group/', views.group_posts, name = 'group_posts'),

    path(
        'group/<slug:pk>/',
        views.post_detail
    ),
]