
from settings import *

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64))
    public_key = db.Column(db.String(64))
    challenge = db.Column(db.String(32), unique=True)
    bad_attempts = db.Column(db.Integer)
    created = db.Column(db.DateTime, default=db.func.current_timestamp())
    verified = db.Column(db.DateTime)
    deleted = db.Column(db.DateTime)
    modified = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, username, public_key, challenge=None, bad_attempts=0):
        self.username = username 
        self.public_key = public_key
        self.challenge = challenge 
        self.bad_attempts = bad_attempts

    def __repr__(self):
        return '<User %r>' % self.public_key

class Follow(db.Model):
    __tablename__ = 'follows'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    user_id2 = db.Column(db.Integer)
    uri = db.Column(db.String(1024))
    value = db.Column(db.Integer)
    created = db.Column(db.DateTime, default=db.func.current_timestamp())
    deleted = db.Column(db.DateTime)
    modified = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, user_id, uri, value):
        self.user_id = user_id
        self.uri = uri
        self.value = value

    def __repr__(self):
        return "<Rating %r>" % self.id

class Rating(db.Model):
    __tablename__ = 'ratings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    uri = db.Column(db.String(1024))
    value = db.Column(db.Integer)
    created = db.Column(db.DateTime, default=db.func.current_timestamp())
    deleted = db.Column(db.DateTime)
    modified = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, user_id, uri, value):
        self.user_id = user_id
        self.uri = uri
        self.value = value

    def __repr__(self):
        return "<Rating %r>" % self.id
