from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Movie, Review
from .forms import ReviewForm, ProfileEditForm
from django.db.models import Avg
from .tmdb import search_movies, get_popular_movies, get_movie_details


class SignUpForm(UserCreationForm):
    class Meta:
        model = UserCreationForm.Meta.model
        fields = ('username',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = '半角英数字で入力してください（150文字以内）'
        self.fields['password1'].help_text = '8文字以上のパスワードを入力してください'
        self.fields['password2'].help_text = '確認のため、同じパスワードを入力してください'


def movie_list(request):
    query = request.GET.get('query', '')

    if query:
        movies = search_movies(query)
        heading = f'「{query}」の検索結果'
    else:
        movies = get_popular_movies()
        heading = '人気の映画'

    return render(request, 'movies/movie_list.html', {
        'movies': movies,
        'heading': heading,
        'query': query,
    })


def movie_detail(request, tmdb_id):
    movie, created = Movie.objects.get_or_create(
        tmdb_id=tmdb_id,
        defaults={'title': '', 'description': '', 'release_year': 2000, 'genre': '未設定'}
    )

    if created:
        details = get_movie_details(tmdb_id)
        if details:
            movie.title = details['title']
            movie.description = details['overview']
            movie.release_year = details['release_date'][:4] if details['release_date'] else 2000
            movie.genre = details['genre']
            movie.poster_url = details['poster_url']
            movie.save()

    reviews = movie.reviews.all().order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.movie = movie
            review.user = request.user
            review.save()
            return redirect('movie_detail', tmdb_id=movie.tmdb_id)
    else:
        form = ReviewForm()

    return render(request, 'movies/movie_detail.html', {
        'movie': movie,
        'reviews': reviews,
        'form': form,
        'avg_rating': avg_rating,
    })


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('movie_list')
    else:
        form = SignUpForm()
    return render(request, 'movies/signup.html', {'form': form})


@login_required
def my_page(request):
    reviews = Review.objects.filter(user=request.user).order_by('-created_at')

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'プロフィールを変更しました')
            return redirect('my_page')
    else:
        form = ProfileEditForm(instance=request.user)

    return render(request, 'movies/my_page.html', {'reviews': reviews, 'form': form})
