from flask import Flask, jsonify, redirect
from flasgger import Swagger, swag_from
import os
from src.auth import auth
from src.bookmarks import bookmarks
from src.constants.http_status_code import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from src.database import db
from src.models.User import User
from src.models.Bookmark import Bookmark
from flask_jwt_extended import JWTManager
from src.config.swagger import template, swagger_config
from flask.json import jsonify


def create_app(test_config=None):
    # Declare app
    app = Flask(__name__,instance_relative_config=True)

    # If we are not in testing mode
    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=os.environ.get("SECRET_KEY"),
            SQLALCHEMY_DATABASE_URI=os.environ.get("SQLALCHEMY_DB_URI"),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY"),

            SWAGGER={
                'title': "Flask Starter Pack",
                'uiversion': 3
            }
        )
    else:
        # Launch tests
        app.config.from_mapping(test_config)

    # Register db
    db.app=app
    db.init_app(app)

    # Add JWT middleware
    JWTManager(app)
    # ---------- START OF ROUTES -------------#

    # Register blueprints
    app.register_blueprint(auth)
    app.register_blueprint(bookmarks)

    Swagger(app, config=swagger_config, template=template)

    # ---------- END OF ROUTES ---------------#


    # Very specific to exemple, do not care about it
    # We can use this kind of function to redirect user or app to specific url from abbreviated or custom urls
    @app.get('/<short_url>')
    @swag_from('./docs/short_url.yaml')
    def redirect_to_url(short_url):
        bookmark = Bookmark.query.filter_by(short_url=short_url).first_or_404()

        if bookmark:
            bookmark.visits = bookmark.visits + 1
            db.session.commit()

            # We can redirect with flask
            return redirect(bookmark.url)

    # Handle all 404 errors
    @app.errorhandler(HTTP_404_NOT_FOUND)
    def handle_404(e):
        return jsonify({'error' : 'Not found'}), HTTP_404_NOT_FOUND

    # Handle all 500 errors
    # Nice to handle code errors 
    @app.errorhandler(HTTP_500_INTERNAL_SERVER_ERROR)
    def handle_505(e):
        return jsonify({'error' : 'Something went wrong, we are working on it'}), HTTP_500_INTERNAL_SERVER_ERROR

    return app



