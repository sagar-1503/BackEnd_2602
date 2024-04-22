from werkzeug.security import check_password_hash, generate_password_hash
from App.database import db

#Temp Imports
from .movie import *
from .review import *
from .movie_review import *
from .watchlist import *
import random
import uuid

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    display_name = db.Column(db.String(120), nullable=False, unique=True)
    username = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)

    # Relationships
    movie_reviews = db.relationship('Movie_Review', backref='user', lazy=True)
    watchlist = db.relationship('Watchlist', backref='user', lazy=True)

    # Review Class Methods

    def add_movie_review(self, rating, text, movie_id):
        movie = Movie.query.get(movie_id)

        if movie:
            # Check if a review was already added for the given movie

            for movie_review in self.movie_reviews:
                if movie_review.movie_id == movie_id:
                    return None  # Review already exists for this movie and user

            # Create a new review
            new_review = Review(rating=rating, text=text)
            db.session.add(new_review)
            db.session.commit()

            # Create a new movie review associated with the current user
            new_movie_review = Movie_Review(movie_id=movie_id, review_id=new_review.id, user_id=self.id)
            db.session.add(new_movie_review)
            db.session.commit()

            return new_review  # Return the newly created review
        else:
            print({"error": 'Movie not found.'})

    def remove_movie_review(self, review_id):
        user_movie_review = next((review for review in self.movie_reviews if review.id == review_id), None)
    
        if user_movie_review:
            review = Review.query.filter_by(id=user_movie_review.id).first()

            db.session.delete(user_movie_review)
            db.session.commit()

            db.session.delete(review)
            db.session.commit()
            return True
        else:
            return False


    # **********************

    # Watchlist Class Methods

    def add_watchlist(self, movie_id):
        watchlist = self.watchlist

        if watchlist:
            self.watchlist[0].insert_movie(movie_id=movie_id)

            db.session.add(self.watchlist[0])
            db.session.commit()
            return self

    def remove_watchlist(self, movie_id):
        user_watchlist = self.watchlist[0]
    
        if user_watchlist:
            self.watchlist[0].remove_movie(movie_id)
            return True
        else:
            return False

    # **********************

    def __init__(self, display_name, username, password):
        self.username = username
        self.set_password(password)

        tag = random.randint(1000, 9999)
        self.display_name = display_name + "-" + str(tag)

        new_watchlist = Watchlist(user_id=self.id)
        self.watchlist = [new_watchlist]

        db.session.add(new_watchlist)
        db.session.commit()

    def get_json(self):
        return{
            'id': self.id,
            'username': self.username
        }

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)
