from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(50))
    name = db.Column(db.String(50))
    elo = db.Column(db.Integer)


class Match(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name1 = db.Column(db.Integer, db.ForeignKey('user.name'))
    name2 = db.Column(db.Integer, db.ForeignKey('user.name'))
    score1 = db.Column(db.Integer)
    score2 = db.Column(db.Integer)
    date = db.Column(db.DateTime)
