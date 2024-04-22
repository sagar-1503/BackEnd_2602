from werkzeug.security import check_password_hash, generate_password_hash
from App.database import db

class Movie_Review(db.Model):
    __tablename__ = 'movie_review'
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    movie_id = db.Column(db.Integer(), db.ForeignKey('movie.id'), nullable=False)
    review_id = db.Column(db.Integer(), db.ForeignKey('review.id'), nullable=False)

    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)

    def __init__(self, movie_id, review_id, user_id):
        self.movie_id = movie_id
        self.review_id = review_id
        self.user_id = user_id
