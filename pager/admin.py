# -*- coding: utf-8 -*-
from datetime import datetime

from sqlalchemy.orm import aliased
from flask import Blueprint, request, url_for, redirect, render_template, session
from flask.ext.wtf import\
    Form, TextField, Required, PasswordField, HiddenField, DateField, IntegerField

from pager.libs.flask_ import blueprint_templated, error, success
from pager.models import db, User, Message, MessageLog
from pager.tasks import absence_email, send_notify_mail

admin = Blueprint('admin', __name__)
templated = blueprint_templated(admin.name)

def extend(dest, *sources):
    for source in sources:
        for k, v in source.iteritems():
            dest[k] = v
    return dest

class ExtForm(Form):
    def dict(self, **kwargs):
        return extend({}, self.data, kwargs)

class LoginForm(ExtForm):
    id = TextField(validators=[Required('아이디를 입력하여 주십시오.')])
    password = PasswordField(validators=[Required('비밀번호를 입력하여 주십시오.')])
    redirect = HiddenField()

class ListUsersForm(ExtForm):
    date = DateField(default=lambda: datetime.now().date())
    status = IntegerField()

@admin.route('/')
@templated
def index():
    normal_users = aliased(User)
    invited_users = aliased(User)
    q = db.session.query(
        db.func.count(User.id),
        db.func.count(normal_users.id), db.func.count(invited_users.id),
    ).outerjoin(
        normal_users, db.and_(User.id==normal_users.id, normal_users.status==User.NORMAL)
    ).outerjoin(
        invited_users, db.and_(User.id==invited_users.id, invited_users.status==User.NOT_REGISTERED_YET)
    )
    total_users = q.first()

    q = q\
        .add_column(db.func.date(User.created))\
        .order_by(db.func.date(User.created)).group_by(db.func.date(User.created))
    users = map(lambda x: (('{:%m.%d}').format(x[3]), x[0], x[1], x[2]), q)

    return dict(users=users, total_users=total_users)

@admin.route('/login', methods=['POST', 'GET'])
@templated
def login():
    form = LoginForm(request.values)
    if form.validate_on_submit():
        # 주인님? / dd skwndlsdla! (ㅇㅇ 나주인!)
        if form.id.data == '주인님?' and form.password.data == 'dd skwndls!':
            session['admin.user_id'] = 1
            return redirect(form.redirect.data or url_for('.index'))
        form.password.errors.append('정보를 확인할 수 없습니다.')
    return dict(form=form)

@admin.route('/users')
@templated
def list_users():
    form = ListUsersForm(request.values)
    form.validate()
    dates = map(
        lambda x: x[0],
        db.session\
            .query(db.func.date(User.created))\
            .group_by(db.func.date(User.created))\
            .order_by(db.func.date(User.created))\
    )
    if dates and form.date.data not in dates:
        form.date.data = dates[-1]

    users = User.query.filter(db.func.date(User.created)==form.date.data)
    if form.status.data is not None:
        users = users.filter(User.status==form.status.data)
    users = users.order_by(User.created)

    return dict(form=form, users=users, dates=dates)

@admin.route('/_test/email/absences/')
@templated
def list_absence_emails():
    test_email=request.values.get('test_email', '')
    users = User.query_has_absence_mail_message_logs()
    return dict(users=users, test_email=test_email)

@admin.route('/_test/email/absences/<int:user_id>')
def show_absence_email(user):
    title, html = absence_email(user, user.absence_mail_message_logs)
    return html

@admin.route('/_test/email/absences/<int:user_id>', methods=['POST'])
def send_test_absence_email(user):
    test_email = request.form.get('test_email', None)
    if test_email:
        send_notify_mail(user, user.absence_mail_message_logs, to=test_email)
        success('%s에게 테스트 메일을 발송 하였습니다.' % test_email)
    else:
        error('테스트할 이메일을 입력 하여 주십시오.')
    return redirect(url_for('.list_absence_emails', test_email=test_email))

class MenuDirector(object):
    def __init__(self, source):
        self._source = [
            [desc, [e.__name__ for e in endpoints]] \
                for desc, endpoints in source
        ]
        
    def __iter__(self):
        current_endpoint = request.endpoint.split('.')[1]
        for description, endpoints in self._source:
            yield(
                description,
                url_for('.' + endpoints[0]),
                current_endpoint in endpoints
            )
    
menu_director = MenuDirector(
    (
     ('개요', (index,)), ('이용자', (list_users,))
    )
)

@admin.context_processor
def context():
    return dict(
        menu_director=menu_director
    )

@admin.before_request
def _before_request():
    if request.endpoint not in ['admin.login']:
        if not session.get('admin.user_id', None):
            return redirect(url_for('.login', redirect=request.url))
