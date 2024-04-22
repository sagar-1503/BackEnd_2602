from werkzeug.security import check_password_hash, generate_password_hash
from App.database import db

import random
import uuid
from .movie import *
from .review import *

class Watchlist(db.Model):
    id = db.Column(db.String(120), primary_key=True, autoincrement=False)

    movies = db.relationship('Movie', backref='watchlist', lazy=True)

    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))

    def __init__(self, user_id):
        self.id = self.generate_uuid()
        return self

    def generate_uuid(self):
        return str(uuid.uuid4())

    def insert_movie(self, movie_id):
        movie = Movie.query.get(movie_id)

        if movie:
            self.movies.append(movie)

            db.session.add(movie)
            db.session.commit()

    def remove_movie(self, movie_id):
        movie = next((movie for movie in self.movies if movie.id == movie_id), None)

        if movie:
            db.session.delete(movie)
            db.session.commit()
