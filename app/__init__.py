# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Arquivo de Inicialização da Aplicação
################################################################################


from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from flask_babelex import Babel

from config import modos_configuracao


########## Instanciação de Extensões ##########


db = SQLAlchemy()
bootstrap = Bootstrap()
login_manager = LoginManager()
mail = Mail()
babel = Babel(default_locale='pt_BR')


########## Configuração de Extensões ##########


# Sistema de Login

login_manager.session_protection = 'strong'
login_manager.login_view = 'autenticacao.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'warning'


########## Application Factory ##########


# Cria uma instância da aplicação em determinado modo de configuração

def criar_app(configuracao):
    app = Flask(__name__)
    app.config.from_object(modos_configuracao[configuracao])

    # Passando a instância da aplicação para as extensões

    db.init_app(app)
    bootstrap.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    babel.init_app(app)

    # Habilitar SSL, caso esteja na configuração de produção

    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask_sslify import SSLify
        sslify = SSLify(app)


    ##### Blueprints #####

    # Principal

    from principal import principal as principal_blueprint
    app.register_blueprint(principal_blueprint)

    # Autenticação

    from autenticacao import autenticacao as autenticacao_blueprint
    app.register_blueprint(autenticacao_blueprint, url_prefix='/autenticacao')

    # Administração

    from administracao import admin
    admin.init_app(app)
    
    from administracao import views
    
    return app

    