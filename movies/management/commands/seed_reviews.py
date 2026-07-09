import random

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from movies.models import Movie, Review
from movies.tmdb import get_popular_movies
from movies.sentiment import predict_sentiment

# ジャンルに応じたコメント候補(ポジティブ/ネガティブ)
COMMENT_POOL = {
    'アクション': {
        'positive': [
            'アクションシーンの迫力がすごい、手に汗握った',
            'スピード感がある展開で最後まで飽きなかった',
            '主人公の戦いっぷりがかっこよかった',
            '手に汗握る展開の連続で目が離せなかった',
            'アクション演出のクオリティが高くて驚いた',
            '緊張感のある戦闘シーンが見応えあった',
        ],
        'negative': [
            'アクションは派手だけどストーリーが薄かった',
            '展開が読めすぎて盛り上がらなかった',
            'キャラクターの掘り下げが足りなかった',
        ],
    },
    'スリラー': {
        'positive': [
            '緊迫感が続いてずっと目が離せなかった',
            '伏線の張り方が丁寧で見事だった',
            '最後まで先が読めずハラハラした',
            '予想を裏切る展開に驚かされた',
            '心理描写が巧みで引き込まれた',
            'ラストの衝撃が忘れられない',
        ],
        'negative': [
            'テンポが悪くて途中で飽きてしまった',
            '結末が中途半端に感じた',
            '緊張感が続かず途中で冷めてしまった',
        ],
    },
    'コメディ': {
        'positive': [
            '何度も笑ってしまった、最高の作品',
            'テンポが軽快で見やすかった',
            'キャラクターがみんな魅力的で楽しめた',
            'くすっと笑える場面が多くて癒された',
            'ユーモアのセンスが自分好みだった',
            '軽い気持ちで楽しめる良い作品だった',
        ],
        'negative': [
            '笑いどころが少なく物足りなかった',
            'ノリが合わなくて微妙だった',
            '内容が薄く感じてしまった',
        ],
    },
    'ホラー': {
        'positive': [
            '恐怖演出が丁寧で最後まで緊張感があった',
            '音の使い方が上手くて怖かった',
            '不気味な雰囲気作りが秀逸だった',
            '想像以上に怖くて夜眠れなかった',
        ],
        'negative': [
            '怖さより不快感の方が強かった',
            '展開が単調で怖くなかった',
            '演出が過剰で逆に冷めてしまった',
        ],
    },
    'ドラマ': {
        'positive': [
            '感動して泣いてしまった、心に残る作品',
            'キャラクターの心情描写が丁寧だった',
            '何度も見返したくなる名作',
            '人間関係の描き方が繊細で良かった',
            '余韻が残る素晴らしいラストだった',
            '静かな感動があって心に響いた',
        ],
        'negative': [
            'テンポが遅く感情移入しづらかった',
            '結末がやや説明不足に感じた',
            '起伏が少なく淡々としていた',
        ],
    },
    'アニメーション': {
        'positive': [
            '映像がとても綺麗で子供から大人まで楽しめる',
            '音楽と映像の融合が素晴らしかった',
            'キャラクターデザインが魅力的だった',
            '家族みんなで楽しめる素敵な作品',
            '色彩豊かな映像美に見入ってしまった',
        ],
        'negative': [
            'ストーリーが単純すぎて物足りなかった',
            '大人向けの深みには欠けていた',
        ],
    },
    'ファミリー': {
        'positive': [
            '心温まるストーリーで家族みんなで楽しめた',
            'キャラクターがとても可愛かった',
            '子供と一緒に見て笑顔になれた',
            '安心して見られる優しい物語だった',
        ],
        'negative': [
            '大人が見ると少し物足りない内容だった',
            '展開がやや単調に感じた',
        ],
    },
    'サイエンスフィクション': {
        'positive': [
            '世界観の作り込みがすごくて引き込まれた',
            'アイデアが斬新で面白かった',
            '映像技術の進化に驚かされた',
            '未来的な設定にワクワクした',
        ],
        'negative': [
            '設定が複雑すぎて理解が追いつかなかった',
            '説明不足で置いてけぼりにされた',
        ],
    },
}

DEFAULT_COMMENTS = {
    'positive': [
        '期待以上の出来で満足した',
        'キャストの演技が素晴らしかった',
        '最後まで引き込まれる作品だった',
        '見応えのある良い作品だった',
        '友人にもおすすめしたい一本',
    ],
    'negative': [
        '正直微妙だった、期待外れ',
        '思ったより盛り上がらなかった',
        '期待していたほどではなかった',
    ],
}


def pick_comment(genre_str, sentiment, used_comments):
    """映画のジャンル文字列に合ったコメントを、まだ使っていないものからランダムに選ぶ"""
    pool = DEFAULT_COMMENTS[sentiment]
    for genre_key, genre_pool in COMMENT_POOL.items():
        if genre_key in genre_str:
            pool = genre_pool[sentiment]
            break

    available = [c for c in pool if c not in used_comments]
    if not available:
        available = pool  # 全部使い切ったら重複を許容

    comment = random.choice(available)
    used_comments.add(comment)
    return comment


class Command(BaseCommand):
    help = 'デモ用のテストユーザーとレビューを投入する'

    def handle(self, *args, **options):
        # ① テスト用ユーザーを作成(12人)
        test_usernames = [
            'Daisy', 'Lily', 'Nate', 'Leo', 'Emma', 'Jack',
            'Olivia', 'Ryan', 'Sophie', 'Mason', 'Grace', 'Ethan',
        ]
        users = []
        for username in test_usernames:
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password('testpass123')
                user.save()
            users.append(user)
            self.stdout.write(f'ユーザー準備完了: {username}')

        # ② TMDBから人気映画を取得してDBに保存(16件)
        movies_data, _ = get_popular_movies(page=1)
        saved_movies = []
        for m in movies_data[:16]:
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
            self.stdout.write(f'映画準備完了: {movie.title}({movie.genre})')

        # ③ グループごとに「好みの映画インデックス」と「評価するユーザー」を定義
        groups = [
            {'user_idxs': [0, 2, 7, 10], 'movie_idxs': [0, 1, 2, 3], 'rating': (4, 5)},
            {'user_idxs': [1, 4, 8], 'movie_idxs': [4, 5, 6], 'rating': (4, 5)},
            {'user_idxs': [3, 5, 6, 9, 11], 'movie_idxs': [7, 8, 9, 10], 'rating': (4, 5)},
        ]
        negative_pairs = [(0, 11), (1, 12), (3, 13), (5, 14), (8, 15)]
        extra_positive_pairs = [(2, 12), (4, 13), (6, 14), (10, 15)]

        created_count = 0
        used_comments_by_movie = {}

        def create_review(user_idx, movie_idx, rating, sentiment_hint):
            nonlocal created_count
            if movie_idx >= len(saved_movies):
                return
            movie = saved_movies[movie_idx]
            user = users[user_idx]

            used_comments = used_comments_by_movie.setdefault(movie_idx, set())
            comment = pick_comment(movie.genre, sentiment_hint, used_comments)

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
                created_count += 1
                self.stdout.write(
                    f'レビュー投稿: {user.username} → {movie.title} ({rating}) [{review.sentiment}] 「{comment}」'
                )

        # ポジティブなグループレビュー
        for group in groups:
            for user_idx in group['user_idxs']:
                for movie_idx in group['movie_idxs']:
                    rating = random.choice(group['rating'])
                    create_review(user_idx, movie_idx, rating, 'positive')

        # ネガティブレビュー
        for user_idx, movie_idx in negative_pairs:
            rating = random.choice([1, 2])
            create_review(user_idx, movie_idx, rating, 'negative')

        # 追加のポジティブ(散発的)
        for user_idx, movie_idx in extra_positive_pairs:
            rating = random.choice([4, 5])
            create_review(user_idx, movie_idx, rating, 'positive')

        self.stdout.write(self.style.SUCCESS(f'デモ用データの投入が完了しました!(新規レビュー: {created_count}件)'))
