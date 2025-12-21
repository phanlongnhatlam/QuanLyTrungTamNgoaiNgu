from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)
app.secret_key = "^%^&%^(*^^&^&^(*^&^&^&^"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:abcd@localhost/trungtamngoaingu_db?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 20
db = SQLAlchemy(app)
login = LoginManager(app)