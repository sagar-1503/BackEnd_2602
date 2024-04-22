import os
from flask import Flask, render_template, jsonify
from flask_uploads import DOCUMENTS, IMAGES, TEXT, UploadSet, configure_uploads
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage

from App.database import init_db
from App.config import load_config

from App.controllers import (
    setup_jwt,
    add_auth_context
)

from App.views import views

#Temp imports
from App.models import Movie, User, Review, Movie_Review
from flask import request, redirect, url_for, flash
from sqlalchemy import func
import random, json
from flask_jwt_extended import jwt_required, get_jwt_identity, current_user, unset_jwt_cookies, set_access_cookies


def add_views(app):
    for view in views:
        app.register_blueprint(view)

def create_app(overrides={}):
    app = Flask(__name__, static_url_path='/static')
    load_config(app, overrides)
    CORS(app)
    add_auth_context(app)
    photos = UploadSet('photos', TEXT + DOCUMENTS + IMAGES)
    configure_uploads(app, photos)
    add_views(app)
    init_db(app)
    jwt = setup_jwt(app)
    
    @jwt.invalid_token_loader
    @jwt.unauthorized_loader
    def custom_unauthorized_response(error):
        return render_template('401.html', error=error), 401

    # =================Temp Routes================

    # Home Page
    @app.route('/home', methods=['GET'])
    def home_page():
        random_movie = Movie.query.order_by(func.random()).first()

        while (random_movie.thumbnail == "Movie_Thumbnail_Link"):
            random_movie = Movie.query.order_by(func.random()).first()

        return render_template('home_page.html', random_movie=random_movie)

    # Movies Page
    @app.route('/movies', methods=['GET'])
    def movies_page_view ():
        movieSearch = request.args.get('s')
        page = request.args.get('page', 1, type=int)
        
        per_page = 25
        
        if movieSearch:
            movies = Movie.query.filter(Movie.title.ilike(f'%{movieSearch}%')).paginate(page=page, per_page=per_page)
        else:
            movies = Movie.query.paginate(page=page, per_page=per_page)
        
        total = movies.total

        return render_template('movies_page.html', movies=movies, total=total, page_count=per_page, current_page=page)
    
    # Movie Review Page
    @app.route('/<href>/review')
    @jwt_required(optional=True)
    def review_page_view(href):
        current_movie = Movie.query.filter_by(href=href).first()
        if current_user:
            user = User.query.filter_by(username=current_user.username).first()

        if current_movie:
            all_movies = Movie.query.all()
            movie_data = []

            has_reviewed = False

            if current_user:
                movie_reviews = user.movie_reviews

            review = None

            if current_user:
                for movie_review in movie_reviews:
                    if movie_review.movie_id == current_movie.id:
                        has_reviewed = True
                        review = Review.query.filter_by(id=movie_review.review_id).first()

            current_movie_index = all_movies.index(current_movie)
            next_movies = all_movies[current_movie_index + 1: current_movie_index + 26]

            for movie in next_movies:
                # Add movies to the list
                movie_data.append({
                    'id': movie.id,
                    'title': movie.title,
                    'release_date': movie.release_date,
                    'genres': movie.genres,
                    'thumbnail': movie.thumbnail,
                    'href': movie.href
                })

            return render_template('review_page.html', movies=movie_data, current_movie=current_movie, review=review, has_reviewed=has_reviewed)
        else:
            return jsonify({'error': 'Movie not found!'}) 

    # Route allowing the user to submit and save their review to their account
    @app.route('/review', methods=['POST'])
    @jwt_required()
    def submit_review_view():
        user = User.query.filter_by(username=current_user.username).first()

        if user:
            try:
                rating = request.form['rating']
                text = request.form['text']
                movie_id = request.form['movie_id']
                
                if not all([rating, text, movie_id]):
                    return jsonify(message="Missing Value(s)"), 400
                else:
                    new_review = user.add_movie_review(rating=rating, text=text, movie_id=movie_id)

                    if new_review:
                        return redirect(url_for('movie_reviews_page_view'))
                    else:
                        return jsonify(message="Review already exists for this movie and user"), 400

            except KeyError as e:
                # Change this to return you back to the previous page and flash a message instead
                return jsonify(error=f"Missing required field: {e.args[0]}"), 400

    # Route allowing deletion of the review from the user's account
    @app.route('/reviews/<int:review_id>', methods=['DELETE'])
    @jwt_required()
    def remove_review_view(review_id):
        user = User.query.filter_by(username=current_user.username).first()

        if user:
            if user.remove_movie_review(review_id):
                flash('Review removed successfully', 'success')
                return redirect(url_for('home_page'))
            else:
                flash('Review not found or you are not authorized to remove it', 'error')
        else:
            flash('User not found', 'error')

        return redirect(url_for('movie_reviews_page_view'))

    # Review Page showing the listing of reviews from the user
    @app.route('/reviews')
    @jwt_required()
    def movie_reviews_page_view():
        user = User.query.filter_by(username=current_user.username).first()

        if user:
            movie_reviews = user.movie_reviews
            reviews = []
            movies = []

            for movie_review in movie_reviews:
                movies.append(Movie.query.get(movie_review.movie_id))
                reviews.append(Review.query.get(movie_review.review_id))

            # Variables for page numbers
            page = request.args.get('page', 1, type=int)
            per_page = 25

            total = len(reviews)

        return render_template('user_reviews_page.html', reviews=reviews, movies=movies, total=total, page_count=per_page, current_page=page)

    # Route to add movies to user watchlist
    @app.route('/watchlist', methods=['POST'])
    @jwt_required()
    def add_watchlist_view():
        user = User.query.filter_by(username=current_user.username).first()

        if user:
            try:
                movie_id = request.form['movie_id']
                
                if not all([movie_id]):
                    return jsonify(message="Missing Value(s)"), 400
                else:
                    user = user.add_watchlist(movie_id=movie_id)
                    return redirect(url_for('watchlist_page_view'))

            except KeyError as e:
                # Change this to return you back to the previous page and flash a message instead
                return jsonify(error=f"Missing required field: {e.args[0]}"), 400

    # Route allowing deletion of a movie from the user's watchlist
    @app.route('/watchlist/<int:movie_id>', methods=['DELETE'])
    @jwt_required()
    def remove_watchlist_view(movie_id):
        user = User.query.filter_by(username=current_user.username).first()

        if user:
            if user.remove_watchlist(movie_id):
                flash('Movie removed successfully from watchlist', 'success')
                return redirect('/watchlist')
            else:
                flash('Movie not found or you are not authorized to remove it', 'error')
        else:
            flash('User not found', 'error')

        return redirect(url_for('watchlist_page_view'))


    # Watchlist Page
    @app.route('/watchlist', methods=['GET'])
    @jwt_required()
    def watchlist_page_view():
        user = User.query.filter_by(username=current_user.username).first()

        if user:
            # movie_reviews = user.movie_reviews
            watchlist = user.watchlist[0]

            reviews = []
            movies = []

            for movie in watchlist.movies:
                movies.append(Movie.query.get(movie.id))
                # reviews.append(Review.query.get(movie_review.review_id))

            recent_movies = []
            for movie in movies[-8:]:
                recent_movies.append(movie)

        return render_template('watchlist_page.html', recent_movies=recent_movies, movies=movies, watchlist=watchlist)

    # Watchlist share route
    @app.route('/<string:display_name>/<string:watchlist_id>/share')
    def wishlist_share_view(display_name, watchlist_id):
        user = User.query.filter_by(display_name=display_name).first()

        if user:
            watchlist = user.watchlist[0]

            if watchlist.id == watchlist_id:
                reviews = []
                movies = []

                for movie in watchlist.movies:
                    movies.append(Movie.query.get(movie.id))

                recent_movies = []
                for movie in movies[-8:]:
                    recent_movies.append(movie)

                return render_template('watchlist_page.html', recent_movies=recent_movies, movies=movies, watchlist=watchlist, current_user=user)
        
        return redirect('/home')

    # Review Page showing the list of all reviews for a particular movie
    @app.route('/<href>/reviews/all', methods=['GET'])
    def all_reviews_view(href):
        current_movie = Movie.query.filter_by(href=href).first()
        all_movie_reviews = Movie_Review.query.filter_by(movie_id=current_movie.id).all()

        users = []
        reviews = []

        for movie_review in all_movie_reviews:
            reviews.append(Review.query.filter_by(id=movie_review.review_id).first())
            users.append(User.query.filter_by(id=movie_review.user_id).first())
            # The order in which they are added reflects who added what review

        return render_template('total_movie_reviews_page.html', movie=current_movie, users=users, reviews=reviews)
    
    app.app_context().push()
    return app

