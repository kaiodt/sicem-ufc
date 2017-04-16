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


########## Formulário Base (Tradução habilitada) ##########


class FormBase(FlaskForm):
    class Meta:
        locales = ['pt_BR']


########## Formulários do Sistema de Autenticação ##########


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
                                               EqualTo('senha2', 'Senhas diferentes.')])

    senha2 = PasswordField('Confirme Senha', validators=[InputRequired()])

    submit = SubmitField('Cadastrar')


    # Cerificar que o email já não foi cadastrado
    def validate_email(self, field):
        if Usuario.query.filter_by(email=field.data).first():
            raise ValidationError('Email já cadastrado.')


# Verificação de Usuário (Para administradores aceitarem novos usuários)
class FormVerificarUsuario(FormBase):
    nome = StringField('Nome', render_kw={'disabled': 'disabled'})

    email = StringField('Email', render_kw={'disabled': 'disabled'})

    # Escolha do cargo do novo usuário
    cargo = SelectField('Cargo')

    submit = SubmitField('Verificar')


    # Inicialização
    def __init__(self, *args, **kwargs):
        super(FormVerificarUsuario, self).__init__(*args, **kwargs)

        # Gerar as opções de cargo via busca no banco de dados
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


    # Certificar que o email existe no banco de dados
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


    # Certificar que o email existe no banco de dados
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


    # Certificar que o novo email desejado já não existe no banco de dados
    def validate_email(self, field):
        if Usuario.query.filter_by(email=field.data).first():
            raise ValidationError('Email já cadastrado.')

