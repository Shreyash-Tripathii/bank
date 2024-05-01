from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt

app = Flask(__name__)
SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="satyamyadav",
    password="sameersatyam",
    hostname="satyamyadav.mysql.pythonanywhere-services.com",
    databasename="satyamyadav$bank",
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.secret_key="d37fcd6e-c667-40d3-a8c4-edccc5ed8fa0"
login_manager=LoginManager()
login_manager.init_app(app)
bcrypt=Bcrypt(app)

from flask_app import routes, models, utils