# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Fomulários do Blueprint Principal
################################################################################


from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import InputRequired, Email, Length, Regexp


########## Formulários ##########


# Formulário Base (Com traduções)
class FormBase(FlaskForm):
    class Meta:
        locales = ['pt_BR']


# Envio de Email
class FormEmailContato(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                               Length(1, 64),
                               Regexp(u'[A-Za-z ÁÉÍÓÚÂÊÎÔÛÃÕÇáéíóúâêîôûãõç]*$')])

    email = StringField('Email', validators=[InputRequired(),
                                             Length(1, 64),
                                             Email()])

    enviar_para = SelectField('Enviar para', choices=[('adm', 'Administradores'),
                                                      ('dev', 'Desenvolvedores')])

    assunto = StringField('Assunto', validators=[InputRequired(),
                                                 Length(1, 100)])

    mensagem = TextAreaField('Mensagem', validators=[InputRequired()])

    enviar = SubmitField('Enviar')

