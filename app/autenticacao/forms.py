# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Fomulários do Blueprint de Autenticação
################################################################################


from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, \
                    SubmitField
from wtforms import ValidationError
from wtforms.validators import InputRequired, Email, Length, Regexp, EqualTo

from ..models import Usuario, Cargo


########## Formulários ##########


# Formulário Base (Com traduções)
class FormBase(FlaskForm):
    class Meta:
        locales = ['pt_BR']


# Login
class FormLogin(FormBase):
    email = StringField('Email', validators=[InputRequired(),
                                             Length(1, 64),
                                             Email()])

    senha = PasswordField('Senha', validators=[InputRequired(),
                                               Length(6, 16)])

    lembrar = BooleanField('Manter-se logado')
    
    submit = SubmitField('Login')


# Cadastro de Usuário
class FormCadastroUsuario(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                               Length(1, 64),
                               Regexp(u'[A-Za-z ÁÉÍÓÚÂÊÎÔÛÃÕÇáéíóúâêîôûãõç]*$', 0)])

    email = StringField('Email', validators=[InputRequired(),
                                             Length(1, 64),
                                             Email()])

    senha = PasswordField('Senha', validators=[InputRequired(),
                                               Length(6, 16),
                                               EqualTo('senha2')])

    senha2 = PasswordField('Confirme Senha', validators=[InputRequired()])

    submit = SubmitField('Cadastrar')


    def validate_email(self, field):
        if Usuario.query.filter_by(email=field.data).first():
            raise ValidationError('Email já cadastrado.')


# Verificação de Usuário
class FormVerificarUsuario(FormBase):
    nome = StringField('Nome', render_kw={'disabled': 'disabled'})

    email = StringField('Email', render_kw={'disabled': 'disabled'})

    cargo = SelectField('Cargo')

    submit = SubmitField('Verificar')

    def __init__(self, *args, **kwargs):
        super(FormVerificarUsuario, self).__init__(*args, **kwargs)

        self.cargo.choices = \
            [(cargo.nome, cargo.nome) for  cargo in Cargo.query.all()]


# Alteração de Senha
class FormAlterarSenha(FormBase):
    senha_atual = PasswordField('Senha Atual', validators=[InputRequired()])
    
    senha_nova = PasswordField('Nova Senha', validators=[InputRequired(),
                                                         Length(6, 16),
                                                         EqualTo('senha_nova2')])

    senha_nova2 = PasswordField('Confirme Nova Senha', validators=[InputRequired()])

    submit = SubmitField('Atualizar Senha')


# Pedido de Recuperação de Senha
class FormPedidoRecuperarSenha(FormBase):
    email = StringField('Email', validators=[InputRequired(),
                                             Length(1, 64),
                                             Email()])

    submit = SubmitField('Recuperar Senha')


    def validate_email(self, field):
        if Usuario.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Email não cadastrado.')


# Recuperação de Senha
class FormRecuperarSenha(FormBase):
    email = StringField('Email', validators=[InputRequired(),
                                             Length(1, 64),
                                             Email()])

    senha_nova = PasswordField('Nova Senha', validators=[InputRequired(),
                                                         Length(6, 16),
                                                         EqualTo('senha_nova2')])

    senha_nova2 = PasswordField('Confirme Nova Senha', validators=[InputRequired()])

    submit = SubmitField('Atualizar Senha')


    def validate_email(self, field):
        if Usuario.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Email não cadastrado.')


# Alteração de Email
class FormAlterarEmail(FormBase):
    email_novo = StringField('Novo Email', validators=[InputRequired(),
                                                       Length(1, 64),
                                                       Email()])

    senha = PasswordField('Senha', validators=[InputRequired()])

    submit = SubmitField('Atualizar Email')


    def validate_email(self, field):
        if Usuario.query.filter_by(email=field.data).first():
            raise ValidationError('Email já cadastrado.')

