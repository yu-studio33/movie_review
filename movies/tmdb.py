import os
import requests

TMDB_API_KEY = os.environ.get('TMDB_API_KEY')
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/w500'

_genre_map = None


def get_genre_map():
    """TMDBのジャンルID→ジャンル名の変換表を取得（キャッシュして再利用）"""
    global _genre_map
    if _genre_map is not None:
        return _genre_map

    url = f'{TMDB_BASE_URL}/genre/movie/list'
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'ja-JP',
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    _genre_map = {genre['id']: genre['name'] for genre in data.get('genres', [])}
    return _genre_map


def search_movies(query, page=1):
    genre_map = get_genre_map()

    url = f'{TMDB_BASE_URL}/search/movie'
    params = {
        'api_key': TMDB_API_KEY,
        'query': query,
        'language': 'ja-JP',
        'page': page,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    results = []
    for movie in data.get('results', []):
        genre_ids = movie.get('genre_ids', [])
        genre_names = [genre_map.get(gid, '') for gid in genre_ids]
        genre_names = [name for name in genre_names if name]

        results.append({
            'tmdb_id': movie.get('id'),
            'title': movie.get('title'),
            'overview': movie.get('overview'),
            'release_date': movie.get('release_date'),
            'poster_path': movie.get('poster_path'),
            'poster_url': f"{TMDB_IMAGE_BASE_URL}{movie.get('poster_path')}" if movie.get('poster_path') else '',
            'genre': ' / '.join(genre_names) if genre_names else '未設定',
        })
    return results, data.get('total_pages', 1)


def get_popular_movies(page=1):
    genre_map = get_genre_map()

    url = f'{TMDB_BASE_URL}/movie/popular'
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'ja-JP',
        'page': page,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    results = []
    for movie in data.get('results', []):
        genre_ids = movie.get('genre_ids', [])
        genre_names = [genre_map.get(gid, '') for gid in genre_ids]
        genre_names = [name for name in genre_names if name]

        results.append({
            'tmdb_id': movie.get('id'),
            'title': movie.get('title'),
            'overview': movie.get('overview'),
            'release_date': movie.get('release_date'),
            'poster_path': movie.get('poster_path'),
            'poster_url': f"{TMDB_IMAGE_BASE_URL}{movie.get('poster_path')}" if movie.get('poster_path') else '',
            'genre': ' / '.join(genre_names) if genre_names else '未設定',
        })
    return results, data.get('total_pages', 1)


def get_movie_details(tmdb_id):
    """TMDBから特定の映画の詳細情報を取得する"""
    genre_map = get_genre_map()

    url = f'{TMDB_BASE_URL}/movie/{tmdb_id}'
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'ja-JP',
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return None

    movie = response.json()
    genres = movie.get('genres', [])
    genre_names = [g['name'] for g in genres]

    return {
        'tmdb_id': movie.get('id'),
        'title': movie.get('title'),
        'overview': movie.get('overview'),
        'release_date': movie.get('release_date'),
        'poster_url': f"{TMDB_IMAGE_BASE_URL}{movie.get('poster_path')}" if movie.get('poster_path') else '',
        'genre': ' / '.join(genre_names) if genre_names else '未設定',
    }


def get_now_playing_movies(page=1):
    """TMDBの現在上映中の映画一覧を取得する"""
    genre_map = get_genre_map()

    url = f'{TMDB_BASE_URL}/movie/now_playing'
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'ja-JP',
        'page': page,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    results = []
    for movie in data.get('results', []):
        genre_ids = movie.get('genre_ids', [])
        genre_names = [genre_map.get(gid, '') for gid in genre_ids]
        genre_names = [name for name in genre_names if name]

        results.append({
            'tmdb_id': movie.get('id'),
            'title': movie.get('title'),
            'overview': movie.get('overview'),
            'release_date': movie.get('release_date'),
            'poster_path': movie.get('poster_path'),
            'poster_url': f"{TMDB_IMAGE_BASE_URL}{movie.get('poster_path')}" if movie.get('poster_path') else '',
            'genre': ' / '.join(genre_names) if genre_names else '未設定',
        })
    return results, data.get('total_pages', 1)
