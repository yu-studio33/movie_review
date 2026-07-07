from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from movies.models import Movie, Review
from movies.tmdb import get_popular_movies, get_movie_details
from movies.sentiment import predict_sentiment


class Command(BaseCommand):
    help = 'デモ用のテストユーザーとレビューを投入する'

    def handle(self, *args, **options):
        # ① テスト用ユーザーを作成
        test_usernames = ['Daisy', 'Lily', 'Nate', 'Leo']
        users = []
        for username in test_usernames:
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password('testpass123')
                user.save()
            users.append(user)
            self.stdout.write(f'ユーザー準備完了: {username}')

        # ② TMDBから人気映画を取得してDBに保存
        movies_data, _ = get_popular_movies(page=1)
        saved_movies = []
        for m in movies_data[:6]:  # 上位6件を使う
            movie, created = Movie.objects.get_or_create(
                tmdb_id=m['tmdb_id'],
                defaults={
                    'title': m['title'],
                    'description': m['overview'],
                    'release_year': m['release_date'][:4] if m['release_date'] else 2000,
                    'genre': m['genre'],
                    'poster_url': m['poster_url'],
                }
            )
            saved_movies.append(movie)
            self.stdout.write(f'映画準備完了: {movie.title}')

        # ③ レビューのサンプルデータ(映画インデックス, ユーザーインデックス, 評価, コメント)
        review_data = [
            (0, 0, 5, '最高に面白かった!何度でも見たくなる作品'),
            (0, 1, 4, 'ストーリーがしっかりしてて引き込まれた'),
            (1, 0, 5, '映像美がすごい、感動した'),
            (1, 2, 4, '期待以上の出来で満足'),
            (2, 1, 5, '笑いあり涙ありの神作品だった'),
            (2, 2, 4, 'テンポが良くて最後まで楽しめた'),
            (3, 0, 2, '正直微妙だった、期待外れ'),
            (4, 1, 5, '伏線回収が見事すぎる、感動した'),
            (5, 2, 5, 'キャストの演技が素晴らしかった'),
        ]

        for movie_idx, user_idx, rating, comment in review_data:
            movie = saved_movies[movie_idx]
            user = users[user_idx]

            review, created = Review.objects.get_or_create(
                movie=movie,
                user=user,
                defaults={
                    'rating': rating,
                    'comment': comment,
                    'sentiment': predict_sentiment(comment),
                }
            )
            if created:
                self.stdout.write(f'レビュー投稿: {user.username} → {movie.title} ({rating}) [{review.sentiment}]')

        self.stdout.write(self.style.SUCCESS('デモ用データの投入が完了しました!'))
