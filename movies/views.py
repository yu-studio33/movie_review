from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count
from .forms import ReviewForm, ProfileEditForm
from .sentiment import predict_sentiment
from django.http import JsonResponse
from .models import Movie, Review, Favorite
from .tmdb import search_movies, get_popular_movies, get_movie_details, get_now_playing_movies, discover_movies, \
    get_genre_id_by_name


class SignUpForm(UserCreationForm):
    class Meta:
        model = UserCreationForm.Meta.model
        fields = ('username',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].max_length = 20
        self.fields['username'].help_text = '半角英数字で入力してください（20文字以内）'
        self.fields['password1'].help_text = '8文字以上のパスワードを入力してください'
        self.fields['password2'].help_text = '確認のため、同じパスワードを入力してください'


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

    sort = request.GET.get('sort', 'new')
    if sort == 'high':
        reviews = movie.reviews.all().order_by('-rating', '-created_at')
    elif sort == 'low':
        reviews = movie.reviews.all().order_by('rating', '-created_at')
    else:
        sort = 'new'
        reviews = movie.reviews.all().order_by('-created_at')

    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    is_favorited = request.user.is_authenticated and movie.favorited_by.filter(user=request.user).exists()

    # 並び替えのAjaxリクエスト時は、レビュー部分だけ返す
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'movies/movie_review_items.html', {
            'reviews': reviews,
            'sort': sort,
        })

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.movie = movie
            review.user = request.user
            review.sentiment = predict_sentiment(review.comment)
            review.save()
            return redirect('movie_detail', tmdb_id=movie.tmdb_id)
    else:
        form = ReviewForm()

    return render(request, 'movies/movie_detail.html', {
        'movie': movie,
        'reviews': reviews,
        'form': form,
        'avg_rating': avg_rating,
        'sort': sort,
        'is_favorited': is_favorited,
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
    favorite_movies = Movie.objects.filter(favorited_by__user=request.user).annotate(
        avg_rating=Avg('reviews__rating')
    )

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'プロフィールを変更しました')
            return redirect('my_page')
    else:
        form = ProfileEditForm(instance=request.user)

    return render(request, 'movies/my_page.html', {
        'reviews': reviews,
        'form': form,
        'favorite_movies': favorite_movies,
    })


def movie_list(request):
    query = request.GET.get('query', '')
    page = int(request.GET.get('page', 1))
    favorite_ids = get_favorite_ids(request.user)

    if query:
        movies, total_pages = search_movies(query, page=page)
        heading = f'「{query}」の検索結果'
    else:
        movies, total_pages = get_popular_movies(page=page)
        heading = '人気の映画'

    tmdb_ids = [m['tmdb_id'] for m in movies]
    local_movies = Movie.objects.filter(tmdb_id__in=tmdb_ids).annotate(
        avg_rating=Avg('reviews__rating')
    )
    rating_map = {m.tmdb_id: m.avg_rating for m in local_movies}
    for m in movies:
        m['avg_rating'] = rating_map.get(m['tmdb_id'])

    has_next = page < total_pages

    # 「もっと見る」クリック時(Ajax)は一覧部分だけ返す
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'movies/movie_list_items.html', {
            'movies': movies,
            'favorite_ids': favorite_ids,
        })

    # --- 協調フィルタリングによるおすすめ(ログイン時のみ、検索していない時のみ) ---
    recommended_movies = None
    recommend_heading = 'あなたへのおすすめ'
    if request.user.is_authenticated and not query:
        my_positive_movie_ids = Review.objects.filter(
            user=request.user, sentiment='positive'
        ).values_list('movie_id', flat=True)

        similar_user_ids = Review.objects.filter(
            movie_id__in=my_positive_movie_ids, sentiment='positive'
        ).exclude(user=request.user).values_list('user_id', flat=True).distinct()

        my_reviewed_movie_ids = Review.objects.filter(
            user=request.user
        ).values_list('movie_id', flat=True)

        recommended_movies = Movie.objects.filter(
            reviews__user_id__in=similar_user_ids,
            reviews__sentiment='positive'
        ).exclude(
            id__in=my_reviewed_movie_ids
        ).annotate(
            recommend_score=Count('id'),
            avg_rating=Avg('reviews__rating')
        ).order_by('-recommend_score')[:10]

        # レビュー実績が少なく、協調フィルタリングの結果が空の場合は人気映画で代替
        if not recommended_movies:
            fallback_movies, _ = get_popular_movies(page=1)
            fallback_movies = fallback_movies[:10]

            fallback_tmdb_ids = [m['tmdb_id'] for m in fallback_movies]
            fallback_local = Movie.objects.filter(tmdb_id__in=fallback_tmdb_ids).annotate(
                avg_rating=Avg('reviews__rating')
            )
            fallback_rating_map = {m.tmdb_id: m.avg_rating for m in fallback_local}
            for m in fallback_movies:
                m['avg_rating'] = fallback_rating_map.get(m['tmdb_id'])

            recommended_movies = fallback_movies
            recommend_heading = '今期注目の映画'

    # --- 新着映画(検索していない時のみ、1ページ目のみ表示) ---
    now_playing_movies = None
    if not query:
        now_playing_movies, _ = get_now_playing_movies(page=1)
        now_playing_movies = now_playing_movies[:10]

        now_playing_ids = [m['tmdb_id'] for m in now_playing_movies]
        now_playing_local = Movie.objects.filter(tmdb_id__in=now_playing_ids).annotate(
            avg_rating=Avg('reviews__rating')
        )
        now_playing_rating_map = {m.tmdb_id: m.avg_rating for m in now_playing_local}
        for m in now_playing_movies:
            m['avg_rating'] = now_playing_rating_map.get(m['tmdb_id'])

    return render(request, 'movies/movie_list.html', {
        'movies': movies,
        'heading': heading,
        'query': query,
        'page': page,
        'has_next': has_next,
        'recommended_movies': recommended_movies,
        'recommend_heading': recommend_heading,
        'now_playing_movies': now_playing_movies,
        'favorite_ids': favorite_ids,
    })


def get_favorite_ids(user):
    """ログインユーザーがお気に入り登録してる映画のtmdb_idをsetで返す"""
    if user.is_authenticated:
        return set(Favorite.objects.filter(user=user).values_list('movie__tmdb_id', flat=True))
    return set()


@login_required
def favorite_list(request):
    favorite_movies = Movie.objects.filter(favorited_by__user=request.user).annotate(
        avg_rating=Avg('reviews__rating')
    )
    favorite_ids = get_favorite_ids(request.user)

    return render(request, 'movies/favorite_list.html', {
        'favorite_movies': favorite_movies,
        'favorite_ids': favorite_ids,
    })


def popular_movies(request):
    page = int(request.GET.get('page', 1))
    favorite_ids = get_favorite_ids(request.user)

    movies, total_pages = get_popular_movies(page=page)

    tmdb_ids = [m['tmdb_id'] for m in movies]
    local_movies = Movie.objects.filter(tmdb_id__in=tmdb_ids).annotate(
        avg_rating=Avg('reviews__rating')
    )
    rating_map = {m.tmdb_id: m.avg_rating for m in local_movies}
    for m in movies:
        m['avg_rating'] = rating_map.get(m['tmdb_id'])

    has_next = page < total_pages

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'movies/movie_list_items.html', {
            'movies': movies,
            'favorite_ids': favorite_ids,
        })

    return render(request, 'movies/popular_movies.html', {
        'movies': movies,
        'page': page,
        'has_next': has_next,
        'favorite_ids': favorite_ids,
    })


def now_playing_page(request):
    page = int(request.GET.get('page', 1))
    favorite_ids = get_favorite_ids(request.user)

    movies, total_pages = get_now_playing_movies(page=page)

    tmdb_ids = [m['tmdb_id'] for m in movies]
    local_movies = Movie.objects.filter(tmdb_id__in=tmdb_ids).annotate(
        avg_rating=Avg('reviews__rating')
    )
    rating_map = {m.tmdb_id: m.avg_rating for m in local_movies}
    for m in movies:
        m['avg_rating'] = rating_map.get(m['tmdb_id'])

    has_next = page < total_pages

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'movies/movie_list_items.html', {
            'movies': movies,
            'favorite_ids': favorite_ids,
        })

    return render(request, 'movies/now_playing_page.html', {
        'movies': movies,
        'page': page,
        'has_next': has_next,
        'favorite_ids': favorite_ids,
    })


@login_required
def toggle_favorite(request, tmdb_id):
    movie = get_object_or_404(Movie, tmdb_id=tmdb_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, movie=movie)

    if not created:
        favorite.delete()
        is_favorited = False
    else:
        is_favorited = True

    return JsonResponse({'is_favorited': is_favorited})


def genre_movies(request, genre_name):
    page = int(request.GET.get('page', 1))
    genre_id = get_genre_id_by_name(genre_name)
    favorite_ids = get_favorite_ids(request.user)

    if genre_id:
        movies, total_pages = discover_movies(genre_id=genre_id, page=page)
    else:
        movies, total_pages = [], 1

    tmdb_ids = [m['tmdb_id'] for m in movies]
    local_movies = Movie.objects.filter(tmdb_id__in=tmdb_ids).annotate(
        avg_rating=Avg('reviews__rating')
    )
    rating_map = {m.tmdb_id: m.avg_rating for m in local_movies}
    for m in movies:
        m['avg_rating'] = rating_map.get(m['tmdb_id'])

    has_next = page < total_pages

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'movies/movie_list_items.html', {
            'movies': movies,
            'favorite_ids': favorite_ids,
        })

    return render(request, 'movies/genre_movies.html', {
        'movies': movies,
        'genre_name': genre_name,
        'page': page,
        'has_next': has_next,
        'favorite_ids': favorite_ids,
    })


def era_movies(request, year_from, year_to):
    page = int(request.GET.get('page', 1))
    favorite_ids = get_favorite_ids(request.user)

    span = year_to - year_from

    if span >= 20:
        # 「それ以前」ページ:範囲が広すぎるのでプルダウンなし
        decade_label = f'{year_to}年以前'
        decade_start = None
        decade_end = None
        year_options = None
    else:
        # 10年区切りの範囲を割り出す(例：1988年だけ選ばれてても、1980年代の範囲を復元する)
        decade_start = (year_from // 10) * 10
        decade_end = decade_start + 9
        decade_label = f'{decade_start}年代'
        year_options = range(decade_start, decade_end + 1)

    movies, total_pages = discover_movies(year_from=year_from, year_to=year_to, page=page)

    tmdb_ids = [m['tmdb_id'] for m in movies]
    local_movies = Movie.objects.filter(tmdb_id__in=tmdb_ids).annotate(
        avg_rating=Avg('reviews__rating')
    )
    rating_map = {m.tmdb_id: m.avg_rating for m in local_movies}
    for m in movies:
        m['avg_rating'] = rating_map.get(m['tmdb_id'])

    has_next = page < total_pages

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'movies/movie_list_items.html', {
            'movies': movies,
            'favorite_ids': favorite_ids,
        })

    return render(request, 'movies/era_movies.html', {
        'movies': movies,
        'year_from': year_from,
        'year_to': year_to,
        'decade_label': decade_label,
        'decade_start': decade_start,
        'decade_end': decade_end,
        'year_options': year_options,
        'page': page,
        'has_next': has_next,
        'favorite_ids': favorite_ids,
    })


@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            review = form.save(commit=False)
            review.sentiment = predict_sentiment(review.comment)
            review.save()
            messages.success(request, 'レビューを更新しました')
            return redirect('my_page')
    else:
        form = ReviewForm(instance=review)

    return render(request, 'movies/edit_review.html', {
        'form': form,
        'review': review,
    })


@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)

    if request.method == 'POST':
        review.delete()
        messages.success(request, 'レビューを削除しました')

    return redirect('my_page')
