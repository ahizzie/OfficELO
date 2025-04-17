from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy import Index

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(128))
    name = db.Column(db.String(50), unique=True, index=True)  # Added unique
    elo = db.Column(db.Integer)
    is_admin = db.Column(db.Boolean, default=False)

    # Relationships
    matches_as_player1 = db.relationship('Match', foreign_keys='Match.player1_id', backref='player1')
    matches_as_player2 = db.relationship('Match', foreign_keys='Match.player2_id', backref='player2')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.name and self.name.lower() == "andy h":
            self.is_admin = True


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player1_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    player2_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    score1 = db.Column(db.Integer)
    score2 = db.Column(db.Integer)
    date = db.Column(db.DateTime(timezone=True), server_default=func.now())

    # Index for common query patterns
    __table_args__ = (
        Index('match_player_idx', 'player1_id', 'player2_id'),
        Index('match_date_idx', 'date'),
    )