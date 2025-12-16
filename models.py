from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    is_finished = db.Column(db.Boolean, default=False)
    mode = db.Column(db.String(50), nullable=False, default='round_robin') # 'round_robin', 'knockout', etc.
    matches = db.relationship('Match', backref='tournament', cascade="all, delete-orphan")
    players = db.relationship('Player', backref='tournament', cascade="all, delete-orphan")

    def __repr__(self):
        return '<Tournament %r>' % self.name

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)

    def __repr__(self):
        return '<Player %r>' % self.name

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    player1_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=True)
    player2_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=True) # Null for bye
    player1 = db.relationship('Player', foreign_keys=[player1_id], backref='matches_as_player1')
    player2 = db.relationship('Player', foreign_keys=[player2_id], backref='matches_as_player2')
    score_player1 = db.Column(db.Integer, default=0)
    score_player2 = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    round_number = db.Column(db.Integer, nullable=False, default=1)
    next_match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=True)
    next_match_slot = db.Column(db.Integer, nullable=True) # 1 or 2
    next_match = db.relationship('Match', remote_side=[id], backref='previous_matches')

    def __repr__(self):
        return '<Match %r vs %r (Round %d)>' % (self.player1.name, self.player2.name if self.player2 else 'BYE', self.round_number)
