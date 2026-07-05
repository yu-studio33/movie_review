from django.urls import path
from . import views

urlpatterns = [
    path('', views.movie_list, name='movie_list'),
    path('signup/', views.signup, name='signup'),
    path('mypage/', views.my_page, name='my_page'),
    path('<int:tmdb_id>/', views.movie_detail, name='movie_detail'),
]
