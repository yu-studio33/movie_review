from django.urls import path
from . import views

urlpatterns = [
    path('', views.movie_list, name='movie_list'),
    path('signup/', views.signup, name='signup'),
    path('mypage/', views.my_page, name='my_page'),
    path('favorites/', views.favorite_list, name='favorite_list'),
    path('popular/', views.popular_movies, name='popular_movies'),
    path('now-playing/', views.now_playing_page, name='now_playing_page'),
    path('genre/<str:genre_name>/', views.genre_movies, name='genre_movies'),
    path('era/<int:year_from>/<int:year_to>/', views.era_movies, name='era_movies'),
    path('favorite/<int:tmdb_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('review/<int:review_id>/edit/', views.edit_review, name='edit_review'),
    path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    path('<int:tmdb_id>/', views.movie_detail, name='movie_detail'),
]
