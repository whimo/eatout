from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

cors = CORS(app,
            resources={
                r'/*': {'origins': app.config['CORS_DESTINATION']}
            },
            supports_credentials=True)

from .recommender import CombinedRecommender

recommender = CombinedRecommender()
try:
    recommender.load()
except FileNotFoundError:
    print('Saved recommender not found, fitting from database...')
    recommender.fit()
    print('Complete.')

from . import views, models
