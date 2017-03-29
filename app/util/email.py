# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Envio de Emails
################################################################################


from threading import Thread
from flask import current_app, render_template
from flask_mail import Message

from .. import mail


########## Funções ##########


# Envio assíncrono de email
def enviar_email_assinc(app, msg):
    with app.app_context():
        mail.send(msg)


# Envio de email
def enviar_email(para, assunto, template, **kwargs):
    app = current_app._get_current_object()

    if not isinstance(para, list):
        para = [para]

    msg = Message(assunto, sender=app.config['MAIL_SENDER'],
                  recipients=para)
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)

    thr = Thread(target=enviar_email_assinc, args=[app, msg])
    thr.start()

    return thr

