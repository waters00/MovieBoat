#!/usr/bin/env python
# -*- coding: utf-8 -*-


from datetime import datetime
from uuid import uuid1

from passlib.context import CryptContext
from flask_login import UserMixin

from app import db

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "sha256_crypt", "sha512_crypt"],
    deprecated="auto",
)


class User(UserMixin, db.Model):
    id = db.Column(db.String(32), primary_key=True)
    username = db.Column(db.String(64), unique=True)
    password_hash = db.Column(db.String(512), nullable=False)

    balance = db.Column(db.Float, default=0.0)
    avatar = db.Column(db.String(1024))
    phone_number = db.Column(db.String(16), unique=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = uuid1().hex

    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, password):
        self.password_hash = pwd_context.hash(password)

    def validate_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def __str__(self):
        return self.username


class Comment(db.Model):
    id = db.Column(db.String(32), primary_key=True)

    user_id = db.Column(db.String(32), db.ForeignKey('user.id', ondelete='cascade'), doc='用户ID')
    user = db.relationship('User', backref=db.backref('u_comments', lazy='dynamic'))

    movie_id = db.Column(db.String(32), db.ForeignKey('movie.id', ondelete='cascade'))
    movie = db.relationship('Movie', backref=db.backref('comments', lazy='dynamic'))

    comment_time = db.Column(db.DateTime, nullable=False)
    content = db.Column(db.Text)
    point = db.Column(db.Integer, nullable=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = uuid1().hex

    def __repr__(self):
        return '<Comment {}>'.format(self.id)


class Reply(db.Model):
    id = db.Column(db.String(32), primary_key=True)

    user_id = db.Column(db.String(32), db.ForeignKey('user.id', ondelete='cascade'), doc='用户ID')
    user = db.relationship('User', backref=db.backref('comments', lazy='dynamic'))

    to_comment_id = db.Column(db.String(32), db.ForeignKey('comment.id', ondelete='cascade'), nullable=True, doc='评论ID')
    to_comment = db.relationship('Comment', backref=db.backref('replies', lazy='dynamic'), foreign_keys=[to_comment_id])

    reply_time = db.Column(db.DateTime, nullable=False)
    content = db.Column(db.Text)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = uuid1().hex

    def __repr__(self):
        return '<Reply {}>'.format(self.id)


class Movie(db.Model):
    id = db.Column(db.String(32), primary_key=True)
    title = db.Column(db.String(128), nullable=False, unique=True)
    brief_id = db.Column(db.Integer, unique=True)
    cover = db.Column(db.String(1024), nullable=False)
    info = db.Column(db.String(128), nullable=False)
    summary = db.Column(db.Text)
    video_uri = db.Column(db.String(1024), nullable=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = uuid1().hex

    def __repr__(self):
        return '<Movie {}>'.format(self.title)

    def __str__(self):
        return self.title


class MoviePrice(db.Model):
    __tablename__ = 'movie_price'
    movie_id = db.Column(db.String(32), db.ForeignKey('movie.id', ondelete='cascade'), primary_key=True)
    movie = db.relationship('Movie', backref=db.backref('movie_price', lazy='dynamic'))
    price = db.Column(db.Float, nullable=False)


class ConsumeRecord(db.Model):
    id = db.Column(db.String(32), primary_key=True)
    consume_time = db.Column(db.DateTime, nullable=False, doc='消费时间')

    consumer_id = db.Column(db.String(32), db.ForeignKey('user.id', ondelete='cascade'), doc='消费的消费者id')
    consumer = db.relationship('User', backref=db.backref('consume_records', lazy='dynamic'))

    movie_id = db.Column(db.String(32), db.ForeignKey('movie.id', ondelete='cascade'))
    movie = db.relationship('Movie', backref=db.backref('consume_records', lazy='dynamic'))

    money = db.Column(db.Float, nullable=False, default=0.0, doc='消费金额')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = uuid1().hex
        self.consume_time = datetime.now()

    def __repr__(self):
        return '<ConsumeRecord {}>'.format(self.id)


class ChargeRecord(db.Model):
    id = db.Column(db.String(32), primary_key=True, doc='id主键')

    user_id = db.Column(db.String(32), db.ForeignKey('user.id', ondelete='cascade'), doc='消费的消费者id')
    user = db.relationship('User', backref=db.backref('charge_records', lazy='dynamic'))

    charge_time = db.Column(db.DateTime, nullable=False, doc='充值时间')
    money = db.Column(db.Float, nullable=False, default=0.0, doc='充值金额')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = uuid1().hex
        self.charge_time = datetime.now()

    def __repr__(self):
        return '<ChargeRecord {}>'.format(self.id)
