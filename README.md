# Movie Review Site
Django製の映画レビューサイトです。TMDB(The Movie Database)と連携し、最新の人気映画や検索結果をリアルタイムに表示。ユーザー登録・ログイン後、映画に対して星評価付きのレビューを投稿できます。

## 主な機能
- TMDB API連携による映画情報のリアルタイム取得(人気映画一覧・キーワード検索)
- トップページはグリッドレイアウトでポスター一覧表示
- 映画詳細ページの初回アクセス時に自動でDBへ保存(get_or_create)
- ユーザー登録・ログイン・ログアウト
- マイページ(プロフィール編集・投稿レビュー一覧)
- レビュー投稿(1〜5段階の星評価＋コメント)
- レビューの平均評価を自動計算・一覧/詳細ページの両方に表示
- レビューの並び替え(新着順・評価が高い順・評価が低い順、Ajaxによる非同期切り替え)
- 「もっと見る」ボタンによるページネーション(Ajaxで追加読み込み)

## 使用技術
- Python 3.13
- Django 6.0.6
- SQLite3
- HTML / CSS / JavaScript(Fetch API)
- TMDB API(映画情報の取得)
- python-dotenv(環境変数管理)

## デザイン
黒を基調としたダークテーマに、ピンク(#FF7FD4)をアクセントカラーとして使用しています。シックな黒背景に映えるビビッドなピンクを差し色にすることで、洗練された印象を目指しました。フォントはPoppins(見出し)とNoto Sans JP(本文)を組み合わせ、エディトリアルで上質な雰囲気を演出しています。

## セットアップ方法
```bash
# リポジトリをクローン
git clone https://github.com/yu-studio33/movie_review.git
cd movie_review

# 仮想環境を作成・有効化
python3 -m venv movie_review_env
source movie_review_env/bin/activate

# 必要なパッケージをインストール
pip install django python-dotenv Pillow requests

# .envファイルを作成し、SECRET_KEYとTMDB_API_KEYを設定
echo "SECRET_KEY=your-secret-key-here" > .env
echo "DEBUG=True" >> .env
echo "TMDB_API_KEY=your-tmdb-api-key-here" >> .env

# マイグレーションを実行
python manage.py migrate

# 管理者アカウントを作成(あなた専用のログイン情報を新規作成します)
python manage.py createsuperuser

# サーバーを起動
python manage.py runserver
```

※ TMDB_API_KEYは[TMDB公式サイト](https://www.themoviedb.org/)でアカウント登録後、無料で取得できます。

## 今後の実装予定
- オリジナルロゴの作成
- 日本語レビューの感情分析による推薦機能(Janome + scikit-learn)

## 作者
[Yu](https://github.com/yu-studio33)
