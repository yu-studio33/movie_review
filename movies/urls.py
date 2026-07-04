from django.urls import path
from . import views

urlpatterns = [
    path('', views.movie_list, name='movie_list'),
    path('signup/', views.signup, name='signup'),
    path('mypage/', views.my_page, name='my_page'),
    path('tmdb-search/', views.tmdb_search, name='tmdb_search'),
    path('tmdb-import/', views.tmdb_import, name='tmdb_import'),
    path('<int:movie_id>/', views.movie_detail, name='movie_detail'),
]
