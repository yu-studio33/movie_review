# Movie Review Site

Django製の映画レビューサイトです。ユーザー登録・ログイン後、映画に対して星評価付きのレビューを投稿できます。

## 主な機能

- ユーザー登録・ログイン・ログアウト
- 映画一覧・詳細ページ表示
- レビュー投稿（1〜5段階の星評価＋コメント）
- レビューの平均評価を自動計算・表示
- ジャンル・公開年代での検索・絞り込み
- マイページ（プロフィール編集・投稿レビュー一覧）

## 使用技術

- Python 3.13
- Django 6.0.6
- SQLite3
- HTML / CSS
- python-dotenv（環境変数管理）

## デザイン

黒を基調としたダークテーマに、ピンク（#FF7FD4）をアクセントカラーとして使用しています。シックな黒背景に映えるビビッドなピンクを差し色にすることで、洗練された印象を目指しました。フォントはPoppins（見出し）とNoto
Sans JP（本文）を組み合わせ、エディトリアルで上質な雰囲気を演出しています。

## セットアップ方法

```bash
# リポジトリをクローン
git clone https://github.com/yu-studio33/movie_review.git
cd movie_review

# 仮想環境を作成・有効化
python3 -m venv movie_review_env
source movie_review_env/bin/activate

# 必要なパッケージをインストール
pip install django python-dotenv Pillow

# .envファイルを作成し、SECRET_KEYを設定
echo "SECRET_KEY=your-secret-key-here" > .env
echo "DEBUG=True" >> .env

# マイグレーションを実行
python manage.py migrate

# 管理者アカウントを作成（あなた専用のログイン情報を新規作成します）
python manage.py createsuperuser

# サーバーを起動
python manage.py runserver
```

## 今後の実装予定

- TMDB APIとの連携（映画情報の自動取得）
- レビューの並び替え・ページネーション
- オリジナルロゴの作成

## 作者

[Yu](https://github.com/yu-studio33)
