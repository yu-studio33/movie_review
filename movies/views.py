from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Movie, Review
from .forms import ReviewForm, ProfileEditForm
from django.db.models import Avg
from .tmdb import search_movies, get_popular_movies, get_movie_details
from .sentiment import predict_sentiment
from django.db.models import Count


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


def movie_list(request):
    query = request.GET.get('query', '')
    page = int(request.GET.get('page', 1))

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
        })

    return render(request, 'movies/movie_list.html', {
        'movies': movies,
        'heading': heading,
        'query': query,
        'page': page,
        'has_next': has_next,
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

    sort = request.GET.get('sort', 'new')
    if sort == 'high':
        reviews = movie.reviews.all().order_by('-rating', '-created_at')
    elif sort == 'low':
        reviews = movie.reviews.all().order_by('rating', '-created_at')
    else:
        sort = 'new'
        reviews = movie.reviews.all().order_by('-created_at')

    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']

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

    # --- 協調フィルタリングによるおすすめ ---
    # ① 自分がpositive評価した映画
    my_positive_movie_ids = Review.objects.filter(
        user=request.user, sentiment='positive'
    ).values_list('movie_id', flat=True)

    # ② それらの映画をpositive評価している他のユーザー
    similar_user_ids = Review.objects.filter(
        movie_id__in=my_positive_movie_ids, sentiment='positive'
    ).exclude(user=request.user).values_list('user_id', flat=True).distinct()

    # ③ 自分が既にレビュー済みの映画(除外対象)
    my_reviewed_movie_ids = Review.objects.filter(
        user=request.user
    ).values_list('movie_id', flat=True)

    # ④ 似た好みのユーザーがpositive評価している、自分が未レビューの映画を集計
    recommended_movies = Movie.objects.filter(
        reviews__user_id__in=similar_user_ids,
        reviews__sentiment='positive'
    ).exclude(
        id__in=my_reviewed_movie_ids
    ).annotate(
        recommend_score=Count('id')
    ).order_by('-recommend_score')[:10]

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
        'recommended_movies': recommended_movies,
    })
