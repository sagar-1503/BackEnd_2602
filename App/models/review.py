from werkzeug.security import check_password_hash, generate_password_hash
from App.database import db

class Review(db.Model):
    id = db.Column(db.Integer(), primary_key=True)

    rating = db.Column(db.Integer(), nullable=False)
    text = db.Column(db.String(1000), nullable=False) # Nullable may be subject to change
    
    # Foreign Keys
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))

    def __init__ (self, rating, text):
        self.rating = rating
        self.text = text
