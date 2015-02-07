# -*- coding: utf-8 -*-
from functools import wraps
from weakref import WeakKeyDictionary

from flask import Response, request
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import RoomsMixin
from facebook import GraphAPI, GraphAPIError
from sqlalchemy import not_
from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound
from simplejson import dumps

from pager.app import app
from pager.libs.flask_ import templated
from pager.libs.facebook_ import parse_signed_request
from pager.libs.timezone import now
from pager.models import db, User, FacebookAccount, ChatRoom, Message, MessageLog

GLOBAL_NAMESPACE = ''

class FlaskNamespace(BaseNamespace, RoomsMixin):
	def process_packet(self, *args, **kwargs):
		with app.request_context(self.environ):
			try:
				return super(FlaskNamespace, self).process_packet(*args, **kwargs)
			except NoResultFound:
				return 404,

	def users_in_room(self, room):
		room_name = self._get_room_name(room)
		user_ids = []
		for sessionid, socket in self.socket.server.sockets.iteritems():
			if 'rooms' not in socket.session:
				continue
			if room_name in socket.session['rooms']:
				user_id = socket.session.get('user_id', None)
				if user_id:
					user_ids.append(user_id)
		return user_ids

	@property
	def facebook_access_token(self):
		access_token = self.session.get('facebook_access_token', None)
		expires_at = self.session.get('facebook_access_token_expires_at', None)
		print expires_at, now(), expires_at <= now()
		if not (access_token and expires_at) or expires_at < now():
			return None

	@facebook_access_token.setter
	def facebook_access_token(self, (access_token, expires_at)):
		self.session['facebook_access_token'], \
		self.session['facebook_access_token_expires_at'] = \
			access_token, expires_at


def authored(f):
	@wraps(f)
	def decorated(self, *args, **kwargs):
		user_id = self.session.get('user_id', None)
		user = user_id and User.get(user_id) or None
		if not user:
			return 403, 
		kwargs['user'] = user
		return f(self, *args, **kwargs)
	return decorated


class GlobalNS(FlaskNamespace):
	online_users = WeakKeyDictionary()

	def on_authenticate(self, *args, **kwargs):
		return 1, 2, {'a': 1}

	def on_authenticate_facebook(self, response):
		try:
			access_token, expires_in = \
				response['accessToken'], response['expiresIn']
			signed_request = parse_signed_request(
				response['signedRequest'], app.config['FACEBOOK_SECRET'],
				expires_in
			)
			if not signed_request:
				return None, None
			graph = GraphAPI(access_token)
			profile = graph.get_object('me')
			user = User.get_by_facebook(profile['id'])
			if not user or user.status == User.NOT_REGISTERED_YET:
				if not user:
					user = User()
					user.facebook_account = FacebookAccount()
				user.email = profile['email']
				user.facebook_account.name = user.nickname = profile['name']
				user.facebook_account.uid = profile['id']
				user.status = User.NORMAL
				db.session.add(user)
				db.session.commit()
			self.online_users[self] = self.session['user_id'] = user.id
			self.facebook_access_token = access_token, signed_request['expires_at']
			return None, user.to_json()
		except GraphAPIError, e:
			return {'_type': 'GraphAPIError', 'msg': str(GraphAPIError)},

	def on_unauthenticate(self):
		self.session.pop('user_id', None)
		self.online_users.pop(self, None)
		return True,

	@authored
	def on_touched_friends(self, user):
		# TODO
		return tuple(),

	@authored
	def on_check_facebook_user_registerd(self, friend_uids, user):
		query = db.session\
			.query(User.id, FacebookAccount.uid,)\
			.join(FacebookAccount)\
			.filter(User.status==User.NORMAL)\
			.filter(FacebookAccount.uid.in_(friend_uids))
		online_users = self.get_online_users()
		user_ids = tuple((id, uid, id in online_users) for id, uid in query)
		return user_ids,

	@authored
	def on_create_room(self, raw_attendees, user):
		chat_room = ChatRoom()
		chat_room.creator = user
		for raw_attendee in raw_attendees:
			attendee_id = raw_attendee.get('id', None)
			if attendee_id:
				attendee = User.get(attendee_id)
			elif raw_attendee['type'] == 'facebook':
				# TODO race condition may occurs need cacth exceptions
				attendee = User.get_by_facebook(raw_attendee['uid'])
				if not attendee:
					attendee = User()
					facebook_account = attendee.facebook_account =\
						FacebookAccount()
					facebook_account.name = attendee.nickname =\
						raw_attendee['nickname']
					attendee.email = raw_attendee.get('email', None)
					facebook_account.uid = raw_attendee['uid']
					db.session.add(attendee)
					db.session.commit()
			else:
				# TODO email account?
				pass
			chat_room.users.append(attendee)
		db.session.add(chat_room)
		db.session.commit()
		json = chat_room.to_json()
		json['message'] = chat_room.messages.first()
		return None, chat_room.to_json()

	@authored
	def on_leave_chat_room(self, room_id, user):
		chat_room = ChatRoom.get(room_id)
		chat_room.users.remove(user)
		db.session.commit()

	@authored
	def on_list_chat_rooms(self, user):
		rooms = []
		for room in user.chat_rooms:
			json = room.to_json()
			message = room.messages.order_by(Message.created.desc()).first()
			if message:
				json['message'] = message.to_json()
			rooms.append(json)
			self.join(str(room.id))
		return None, rooms

	@authored
	def on_list_notes(self, room_id, user):
		room = ChatRoom.get(room_id)
		if not room:
			return '채팅방을 찾을수 없습니다.',
		if user not in room.users:
			return '채팅방에 참여하지 않았습니다.',
		return\
			None,\
			tuple(
				n.to_json() \
					for n in room.messages.order_by(Message.created.desc())
			)

	@authored
	def on_new_note(self, note, user):
		room = ChatRoom.get(note['id'])
		if not room:
			return '채팅방을 찾을수 없습니다.',
		if user not in room.users:
			return '채팅방에 참여하지 않았습니다.',

		message = Message()
		message.user = user
		message.message = note['message']
		message.color = note['color']
		for u in room.users:
			log = MessageLog()
			log.user = u
			if u is user:
				log.status |= MessageLog.READ
			message.logs.append(log)
		room.messages.append(message)
		db.session.commit()
		print message.logs.all()
		json = message.to_json()
		self.emit_to_room(str(room.id), 'new note', json)
		online_users = self.users_in_room(str(room.id))
		q = room.users.filter(User.status==User.NORMAL)
		if online_users:
			q = q.filter(not_(User.id.in_(online_users)))
		for offline_user in q:
			pass
		return None, json

	@authored
	def on_read_notes(self, message_ids, user):
		MessageLog.update_status(message_ids, MessageLog.READ, user.id)
		return

	@authored
	def on_notified_notes(self, message_ids, user):
		MessageLog.update_status(message_ids, MessageLog.NOTIFIED, user.id)
		return

	@classmethod
	def get_online_users(cls):
		return set(cls.online_users.values())

@app.url_value_preprocessor
def process_params(endpoint, values):
    try:
    	if values:
	        if 'user_id' in values:
	        	id = values.pop('user_id', None)
	        	if id:
	        		user = User.query.filter_by(id=id).one()
	        	else:
	        		user = User()
	        	values['user'] = user
	       	if 'message' in values:
	       		id = values.get('message', None)
	       		if id:
	       			message = Message.query.filter_by(id=id).one()
	       		else:
	       			message = Message()
	       		values['message'] = message
    except NoResultFound:
        abort(404)

@app.route('/')
@templated
def index():
	return dict()

@app.route('/email')
@templated
def email():
	return dict()

@app.route('/korean')
@templated
def korean_index():
	return dict()

@app.route('/beta/')
@templated
def pager():
	return {}

@app.route('/socket.io/<path:remaining>')
def socketio(remaining):
	socketio_manage(
		request.environ, {GLOBAL_NAMESPACE: GlobalNS}
	)
	return Response()
