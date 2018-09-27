from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

cors = CORS(app, resources={r'/*': {'origins': app.config['CORS_DESTINATION']}})

from . import views, models
