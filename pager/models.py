import os, gevent
from psycogreen.gevent import patch_psycopg
if os.fork is gevent.fork:
    patch_psycopg()
from datetime import timedelta
from sqlalchemy.orm import joinedload
from flask.ext.sqlalchemy import SQLAlchemy

from pager.config import config
from pager.app import app
from pager.libs import extend
from pager.libs.timezone import now

db = SQLAlchemy(app)

class Mixins(object):
    id = db.Column(db.Integer, primary_key=True)

    created = db.Column(db.DateTime(True), default=now, nullable=False)
    updated = db.Column(
        db.DateTime(True), default=now, onupdate=now, nullable=False
    )

    @property
    def is_new(self):
        return id is None

    def to_json(self):
        created = self.created and self.created.isoformat() or None
        updated = self.updated and self.updated.isoformat() or None
        return {'id': self.id, 'created': created, 'updated': updated}

    @classmethod
    def get(cls, id):
        return cls.query.filter(cls.id==id).first()

    @classmethod
    def get_or_create(cls, id):
        obj = cls.get(id)
        if not obj:
            obj = cls()
            db.session.add(obj)
        return obj


class User(Mixins, db.Model):
    __tablename__ = 'users'

    # status
    NORMAL = 1
    # lineup in database and invited, but not yet registered by user
    NOT_REGISTERED_YET = 0

    nickname = db.Column(db.String(256))
    email = db.Column(db.String(256), unique=True)
    status = db.Column(
        db.Integer, default=NOT_REGISTERED_YET, index=True, nullable=False
    )

    facebook_account = db.relationship(
        lambda: FacebookAccount, backref='user', uselist=False, lazy='joined'
    )

    message_logs = db.relationship(
        lambda: MessageLog, lazy='dynamic'
    )

    absence_mail_message_logs = db.relationship(
        lambda: MessageLog, primaryjoin=lambda: db.and_(
            MessageLog.user_id == User.id, MessageLog.ABSENCE_MAIL_CONDITION
        ),
        lazy='dynamic'
    )

    def to_json(self):
        json = super(User, self).to_json()
        if self.facebook_account:
            facebook_account = self.facebook_account.to_json()
        else:
            facebook_account = None
        user = {
            'nickname': self.nickname, 'email': self.email,
            'facebook_account': facebook_account, 'status': self.status
        }
        return extend(json, user)

    @property
    def profile_image_url(self):
        return \
            "http://graph.facebook.com/%s/picture?type=square" % (
                self.facebook_account.uid
            )

    @property
    def registered(self):
        return self.status == self.NORMAL

    @classmethod
    def get_by_facebook(cls, facebook_id):
        return cls.query\
            .join(FacebookAccount)\
            .filter(FacebookAccount.uid==str(facebook_id))\
            .first()

    @classmethod
    def query_has_absence_mail_message_logs(cls):
        query = cls.query.filter(
            cls.status==cls.NORMAL, cls.absence_mail_message_logs.any(),
        )
        return query


class FacebookAccount(Mixins, db.Model):
    __tablename__ = 'facebook_accounts'
    uid = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(256), nullable=False)

    user_id = db.Column(
        db.Integer, db.ForeignKey(User.id), unique=True, nullable=False, index=True
    )

    def to_json(self):
        json = super(FacebookAccount, self).to_json()
        return extend(json, {'uid': self.uid, 'name': self.name})


class ChatRoom(Mixins, db.Model):
    __tablename__ = 'chat_rooms'

    creator_id = db.Column(
        db.Integer, db.ForeignKey(User.id), index=True, nullable=False
    )

    users = db.relationship(
        User, secondary=lambda: users_in_chat_room, backref='chat_rooms',
        lazy='dynamic'
    )
    messages = db.relationship(
        lambda: Message, backref='chat_room', lazy='dynamic'
    )
    creator = db.relationship(User, uselist=False)

    def to_json(self):
        json = super(ChatRoom, self).to_json()
        return extend(
            json, {
                'users': [
                    u.to_json() for u in\
                        self.users.order_by(users_in_chat_room.c.created)
                ],
                'creator': self.creator.to_json(),
            }
        )

users_in_chat_room = db.Table(
    'users_in_chat_room', db.Model.metadata,
    db.Column(
        'chat_room_id', db.Integer, db.ForeignKey(ChatRoom.id),
        nullable=False, index=True, primary_key=True
    ),
    db.Column(
        'user_id', db.Integer, db.ForeignKey(User.id),
        nullable=False, index=True, primary_key=True
    ),
    db.Column(
        'created', db.DateTime(True), default=now, nullable=False
    ),
)


class Message(Mixins, db.Model):
    __tablename__ = 'messages'
    
    color = db.Column(db.Integer, index=True, nullable=False)
    message = db.Column(db.String(280), default='', nullable=False)
    user_id = db.Column(
        db.Integer, db.ForeignKey(User.id), index=True, nullable=False
    )
    chat_room_id = db.Column(
        db.Integer, db.ForeignKey(ChatRoom.id), index=True, nullable=False
    )

    user = db.relationship(User)
    logs = db.relationship(lambda: MessageLog, lazy='dynamic')

    def to_json(self):
        json = super(Message, self).to_json()
        return extend(
            json, {
                'id': self.id, 'message': self.message, 'color': self.color,
                'chat_room_id': self.chat_room_id, 'user': self.user.to_json()
            }
        )

    @property
    def css_color(self):
        return '#' + hex(self.color)[2:]


class MessageLog(Mixins, db.Model):
    __tablename__ = 'message_logs'
    INIT = 0
    NOTIFIED = 0b01
    READ = 0b10
    NOT_NEED_NOTIFIED = NOTIFIED | READ

    status = db.Column(db.Integer, index=True, nullable=False, default=INIT)
    user_id = db.Column(
        db.Integer, db.ForeignKey(User.id), index=True, nullable=False
    )
    message_id = db.Column(
        db.Integer, db.ForeignKey(Message.id), index=True, nullable=False
    )

    user = db.relationship(User)
    message = db.relationship(Message)

    # TODO change to hybrid property
    STATUS_NEED_NOTIFIED = status.op('&')(NOT_NEED_NOTIFIED) == 0

    def __init__(self):
        self.status = self.INIT

    def mark_notified(self):
        self.status = MessageLog.status.op('|')(MessageLog.NOTIFIED)

    @classmethod
    def update_status(cls, message_ids, status, user_id):
        cls.query.filter(
            cls.message_id.in_(message_ids),
            cls.user_id==user_id,
            cls.status.op('&')(status) == 0
        ).update(dict(status=cls.status.op('|')(status)), synchronize_session=False)
        db.session.commit()

MessageLog.ABSENCE_MAIL_CONDITION = db.and_(
    MessageLog.STATUS_NEED_NOTIFIED,
    (db.func.now() - MessageLog.created) > config.ABSECE_MAIL_HOLD_DOWN
)