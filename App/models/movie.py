from werkzeug.security import check_password_hash, generate_password_hash
from App.database import db

import json

class Movie(db.Model):
    id = db.Column(db.Integer(), primary_key=True)

    title = db.Column(db.String(255), nullable=False)
    release_date = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    genres = db.Column(db.String(1000), nullable=True)
    description = db.Column(db.String(1000), nullable=False)
    thumbnail = db.Column(db.String(120))  # Poster image
    backdrop = db.Column(db.String(120))  # Background image
    href = db.Column(db.String(255))  # Formatted title for use in the HTML

    has_video = db.Column(db.Boolean(), default=False)
    video_URL = db.Column(db.String(255))
    video_name = db.Column(db.String(255))

    # Relationships
    reviews = db.relationship('Review', secondary='movie_review', backref=db.backref('movies'), lazy=True)
    watchlist_id = db.Column(db.String, db.ForeignKey('watchlist.id'))

    def __init__(self, id, title, release_date, language, genres, description, thumbnail, backdrop, hasVideo):
        self.id = id
        self.title = title
        self.release_date = release_date
        self.language = language
        self.genres = json.dumps(genres)
        self.description = description
        self.thumbnail = thumbnail
        self.backdrop = backdrop
        self.hasVideo = hasVideo

    def get_genres(self):
        return json.loads(self.genres)
