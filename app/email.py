from threading import Thread
from flask import current_app, render_template
from flask_mail import Message


def send_async_email(app, msg):
    """异步发送邮件"""
    with app.app_context():
        from app import mail
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    """发送邮件"""
    app = current_app._get_current_object()
    msg = Message(
        app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
        sender=app.config['FLASKY_MAIL_SENDER'],
        recipients=[to]
    )
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    Thread(target=send_async_email, args=(app, msg)).start()
