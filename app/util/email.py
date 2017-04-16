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


# Envio assíncrono de email (O processo ocorre paralelamente, em uma thread separada
# do funcionamento principal da aplicação)
def enviar_email_assinc(app, msg):
    with app.app_context():
        mail.send(msg)


# Preparação para envio do email
def enviar_email(para, assunto, template, **kwargs):
    # Obter aplicação sendo utilizada
    app = current_app._get_current_object()

    # Caso haja apenas um destinatário, colocá-lo em uma lista
    if not isinstance(para, list):
        para = [para]

    # Criação da mensagem

    msg = Message(assunto, sender=app.config['MAIL_SENDER'],
                  recipients=para)
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)

    # Criando uma thread para que o email possa ser enviado de modo assíncrono,
    # ou seja, a aplicação não precisa esperar até que o email seja enviado

    thr = Thread(target=enviar_email_assinc, args=[app, msg])
    thr.start()

    return thr

