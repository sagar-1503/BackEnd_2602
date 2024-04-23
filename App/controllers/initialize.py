from .user import create_user
from App.database import db


# Temp Imports
from App.models import db, Movie, User
from flask.cli import FlaskGroup
import json
import requests

last_fetched_page = 1

def initialize():
    # db.drop_all()
    db.create_all()

    user = User.query.filter_by(username="bob").first()

    if not user:
        create_user('BobTheBuilder', 'bob', 'bobpass')

    # Perfom an auth on the Movie List API 
    authUrl = "https://api.themoviedb.org/3/authentication"
    
    authHeaders = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI3ZDcyMThmOTE2Yzk2MWEyNjc3ZmI1ZTdjMjFmZmNjNyIsInN1YiI6IjY2MThkM2VlMGYwZGE1MDE3Y2RmNWI3YyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.MhyHjQ2gXlSLm0zjI5dEwX7nwQQ58hzd25wnCKC3fjo"
    }
    
    authResponse = requests.get(authUrl, headers=authHeaders)

    # Import movie files from API

    genre_url = "https://api.themoviedb.org/3/genre/movie/list"
    genre_headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI3ZDcyMThmOTE2Yzk2MWEyNjc3ZmI1ZTdjMjFmZmNjNyIsInN1YiI6IjY2MThkM2VlMGYwZGE1MDE3Y2RmNWI3YyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.MhyHjQ2gXlSLm0zjI5dEwX7nwQQ58hzd25wnCKC3fjo"
        }

    genre_response = requests.get(genre_url, headers=genre_headers)
    movie_genres = genre_response.json().get("genres", [])

    movie_test = Movie.query.first()

    if movie_test:
        print('database already initialized')
    else:
        for page in range(last_fetched_page, 501):
            url = "https://api.themoviedb.org/3/discover/movie"
            params = {
                "include_adult": "false",
                "include_video": "true",
                "language": "en-US",
                "page": str(page),
                "sort_by": "popularity.desc"
            }

            headers = {
                "accept": "application/json",
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI3ZDcyMThmOTE2Yzk2MWEyNjc3ZmI1ZTdjMjFmZmNjNyIsInN1YiI6IjY2MThkM2VlMGYwZGE1MDE3Y2RmNWI3YyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.MhyHjQ2gXlSLm0zjI5dEwX7nwQQ58hzd25wnCKC3fjo"
            }

            response = requests.get(url, params=params, headers=headers)
            movies = response.json().get('results', [])

            for movie in movies:
                existing_movie = Movie.query.filter_by(id=movie.get('id')).first()
                if existing_movie:
                    # If a movie with the same ID already exists, skip adding it
                    continue

                # Get genre names corresponding to the genre IDs
                genre_names = [genre['name'] for genre in movie_genres if genre['id'] in movie.get('genre_ids', [])]
                formatted_genre_names = ", ".join(genre_names)

                new_movie = Movie(
                    # Set generic values if unable to attain a value
                    id=movie.get('id', 0),
                    title=movie.get('title', 'Movie_Title'), 
                    release_date=movie.get('release_date', 'Movie_Date'),
                    language=movie.get('original_language', 'Movie_Language'),
                    genres=formatted_genre_names,
                    description=movie.get('overview', 'Movie_Description'), 
                    thumbnail=movie.get('poster_path', 'Movie_Thumbnail_Link'), 
                    backdrop=movie.get('backdrop_path', 'Movie_Backdrop_Link'),
                    hasVideo=movie.get('video', False)
                )
                new_movie.href = new_movie.title.replace(" ", "_") + "_(film)" + "_" + str(new_movie.id)

                base_url = "https://image.tmdb.org/t/p/original"
                poster_path = str(new_movie.thumbnail)
                backdrop_path = str(new_movie.backdrop)

                new_movie.thumbnail = base_url + poster_path
                new_movie.backdrop = base_url + backdrop_path

                if (new_movie.has_video):
                    # Perform query for the particular movie
                    video_URL = "https://api.themoviedb.org/3/movie/" + str(new_movie.id) + "/videos?language=en-US"

                    headers = {
                        "accept": "application/json",
                        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI3ZDcyMThmOTE2Yzk2MWEyNjc3ZmI1ZTdjMjFmZmNjNyIsInN1YiI6IjY2MThkM2VlMGYwZGE1MDE3Y2RmNWI3YyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.MhyHjQ2gXlSLm0zjI5dEwX7nwQQ58hzd25wnCKC3fjo"
                    }

                    video_response = requests.get(url, headers=headers)
                    videos = response.json().get('results', [])

                    # Take only the first response
                    new_movie.video_name = videos[0].get('name', "Video_Name")

                    site = videos[0].get('site', 'YouTube')
                    if (site == "YouTube"):
                        new_movie.video_URL = "https://www.youtube.com/watch?v=" + videos[0].key
                    if (site == "Vimeo"):
                        new_movie.video_URL = "https://vimeo.com/" + videos[0].key
                    if (site == "Dailymotion"):
                        new_movie.video_URL = "https://www.dailymotion.com/video/" + videos[0].key

                db.session.add(new_movie)
            db.session.commit()
            last_fetched_page = page  # Update the last fetched page

        print('database initialized')

