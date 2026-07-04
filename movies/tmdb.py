import os
import requests

TMDB_API_KEY = os.environ.get('TMDB_API_KEY')
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/w500'


def search_movies(query):
    """TMDBで映画を検索し、結果のリストを返す"""
    url = f'{TMDB_BASE_URL}/search/movie'
    params = {
        'api_key': TMDB_API_KEY,
        'query': query,
        'language': 'ja-JP',
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    results = []
    for movie in data.get('results', []):
        results.append({
            'tmdb_id': movie.get('id'),
            'title': movie.get('title'),
            'overview': movie.get('overview'),
            'release_date': movie.get('release_date'),
            'poster_path': movie.get('poster_path'),
            'poster_url': f"{TMDB_IMAGE_BASE_URL}{movie.get('poster_path')}" if movie.get('poster_path') else '',
        })
    return results
