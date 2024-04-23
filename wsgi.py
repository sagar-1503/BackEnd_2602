import click, pytest, sys
from flask import Flask
from flask.cli import with_appcontext, AppGroup

import json

from App.database import db, get_migrate
from App.main import create_app
from App.controllers import ( create_user, get_all_users_json, get_all_users )

# Temp Imports
from App import *
from flask.cli import FlaskGroup
import requests

# Movie API Auth


# Perfom an auth on the Movie List API 
authUrl = "https://api.themoviedb.org/3/authentication"

authHeaders = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI3ZDcyMThmOTE2Yzk2MWEyNjc3ZmI1ZTdjMjFmZmNjNyIsInN1YiI6IjY2MThkM2VlMGYwZGE1MDE3Y2RmNWI3YyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.MhyHjQ2gXlSLm0zjI5dEwX7nwQQ58hzd25wnCKC3fjo"
}

authResponse = requests.get(authUrl, headers=authHeaders)
# End of auth

# This commands file allow you to create convenient CLI commands for testing controllers

app = create_app()
migrate = get_migrate(app)

# This command creates and initializes the database
@app.cli.command("init", help="Creates and initializes the database")
def initialize():
    db.drop_all()
    db.create_all()
    create_user('BobTheBuilder', 'bob', 'bobpass')

    # Import movie files from API

    genre_url = "https://api.themoviedb.org/3/genre/movie/list"
    genre_headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI3ZDcyMThmOTE2Yzk2MWEyNjc3ZmI1ZTdjMjFmZmNjNyIsInN1YiI6IjY2MThkM2VlMGYwZGE1MDE3Y2RmNWI3YyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.MhyHjQ2gXlSLm0zjI5dEwX7nwQQ58hzd25wnCKC3fjo"
        }

    genre_response = requests.get(genre_url, headers=genre_headers)
    movie_genres = genre_response.json().get("genres", [])

    for page in range(1,501):
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

    print('database initialized')

'''
User Commands
'''

cli = FlaskGroup(create_app=create_app)

# Define a function to run the initialize command
def run_initialize_command():
    cli.invoke(initialize)

if __name__ == "__main__":
    # Run the initialize command
    run_initialize_command()

# Commands can be organized using groups

# create a group, it would be the first argument of the comand
# eg : flask user <command>
user_cli = AppGroup('user', help='User object commands') 

# Then define the command and any parameters and annotate it with the group (@)
@user_cli.command("create", help="Creates a user")
@click.argument("username", default="rob")
@click.argument("password", default="robpass")
def create_user_command(display_name, username, password):
    create_user(display_name, username, password)
    print(f'{username} created!')

# this command will be : flask user create bob bobpass

@user_cli.command("list", help="Lists users in the database")
@click.argument("format", default="string")
def list_user_command(format):
    if format == 'string':
        print(get_all_users())
    else:
        print(get_all_users_json())

app.cli.add_command(user_cli) # add the group to the cli

'''
Test Commands
'''

test = AppGroup('test', help='Testing commands') 

@test.command("user", help="Run User tests")
@click.argument("type", default="all")
def user_tests_command(type):
    if type == "unit":
        sys.exit(pytest.main(["-k", "UserUnitTests"]))
    elif type == "int":
        sys.exit(pytest.main(["-k", "UserIntegrationTests"]))
    else:
        sys.exit(pytest.main(["-k", "App"]))
    

app.cli.add_command(test)
