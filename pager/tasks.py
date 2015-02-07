from datetime import timedelta
from collections import defaultdict
from smtplib import SMTP
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from celery import Celery
from flask import render_template

from config import config
from pager.models import db, User, MessageLog, Message
from pager.app import app

celery = Celery()
celery.config_from_object(config)

def rfc2047_header(str):
    return Header(str.encode('utf-8'), 'UTF-8').encode('utf-8')

def create_message(from_addr, to_addr, from_, to, subject, html):
    message = MIMEMultipart('alternative')
    message['Subject'] = subject
    # if email address encoded then attach local address
    message['From'] = "%s<%s>" % (rfc2047_header(from_), from_addr)
    message['To'] = "%s<%s>" % (rfc2047_header(to), to_addr)
    message.attach(MIMEText(html, 'html', 'utf-8'))
    return message

def send_mail(from_addr, to_addr, from_, to, subject, html, smtp=None, smtp_server='localhost'):
    if smtp is None:
        smtp = SMTP(smtp_server)
        try:
            return send_mail(from_addr, to_addr, from_, to, subject, html, smtp)
        finally:
            smtp.quit()
    message = create_message(from_addr, to_addr, from_, to, subject, html)
    smtp.sendmail(from_addr, to_addr, message.as_string())

def absence_email(user, message_logs):
    chat_rooms = defaultdict(list)
    messages = []
    for message_log in message_logs:
        messages.append(message_log.message)
        chat_rooms[message_log.message.chat_room_id].append(message_log.message)

    # generate title
    messages.sort(key=lambda x: x.created)
    message = messages[0]
    users = []
    for m in messages:
        if m.user not in users:
            users.append(m.user)
    senders = "%s" % users[0].nickname
    if len(users) == 1:
        senders += " has"
    elif len(users) == 2:
        senders = " and %s have" % (users[1].nickname)
    else:
        senders = " and %d others have" % (len(users) - 1)
    if len(messages) == 1:
        title = senders + " sent you a message!"
    else:
        title = senders + " sent you messages!"

    html = render_template(
        'email/absence.jade', user=user, chat_rooms=chat_rooms, title=title
    )
    return title, html

def send_notify_mail(user, message_logs, smtp=None, to=None):
    to = to or user.email
    title, html = absence_email(user, message_logs)
    send_mail(
        'norepy@pager.funnyplan.com', to,
        'Pager', user.nickname,
        title, html, smtp
    )

@celery.task
def send_notify_mails(limit=0):
    smtp = SMTP(config.SMTP_SERVER)
    try:
        with app.test_request_context(base_url=config.BASE_URL):
            query = User.query_has_absence_mail_message_logs()
            if limit > 0:
                query = query.limit(limit)
            for user in query:
                    message_logs = tuple(
                        user.absence_mail_message_logs.options(
                            db.joinedload(MessageLog.message),
                            db.joinedload(MessageLog.message, Message.user),
                        )
                    )
                    send_notify_mail(user, message_logs, smtp)
                    for ml in message_logs:
                        ml.mark_notified()
                    db.session.commit()
    finally:
        smtp.quit()
        send_notify_mails.apply_async(countdown=60)

