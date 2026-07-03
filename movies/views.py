from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Movie, Review
from .forms import ReviewForm, ProfileEditForm
from django.db.models import Avg


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
    movies = Movie.objects.annotate(avg_rating=Avg('reviews__rating'))

    genre = request.GET.get('genre')
    decade = request.GET.get('decade')

    if genre:
        movies = movies.filter(genre__icontains=genre)
    if decade:
        decade_start = int(decade)
        decade_end = decade_start + 9
        movies = movies.filter(release_year__gte=decade_start, release_year__lte=decade_end)

    genres = Movie.objects.values_list('genre', flat=True).distinct()
    decades = [1980, 1990, 2000, 2010, 2020]

    return render(request, 'movies/movie_list.html', {
        'movies': movies,
        'genres': genres,
        'decades': decades,
        'selected_genre': genre,
        'selected_decade': decade,
    })


def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    reviews = movie.reviews.all()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.movie = movie
            review.user = request.user
            review.save()
            return redirect('movie_detail', movie_id=movie.id)
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
