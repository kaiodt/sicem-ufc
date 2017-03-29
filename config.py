# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Arquivo de Configuração
################################################################################


import os

# Diretório base
basedir = os.path.abspath(os.path.dirname(__file__))


########## Classes de Configuração ##########


# Configuração Geral
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')

    SSL_DISABLE = True

    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    ADMIN_SENHA = os.environ.get('ADMIN_SENHA')

    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_SENDER = os.environ.get('MAIL_SENDER')

    MAPBOX_MAP_ID = 'mapbox.streets'
    MAPBOX_ACCESS_TOKEN = os.environ.get('MAPBOX_ACCESS_TOKEN')

    
# Configuração de Desenvolvimento
class ConfigDesenvolvimento(Config):
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
      'postgresql://sie_ufc_admin:sie_ufc@localhost/dev_sie_ufc'

# Configuração de Teste
class ConfigTeste(Config):
    TESTING = True


# Configuração de Produção
class ConfigProducao(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # Enviar email de erros para administradores

        import logging
        from logging.handlers import SMTPHandler
        from app.models import Usuario
        
        credentials = None
        secure = None

        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()

        lista_adms = Usuario.listar_administradores()
        emails_administradores = [usuario.email for usuario in lista_adms]

        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.MAIL_SENDER,
            toaddrs=emails_administradores,
            subject='Erro de Sistema - SICEM-UFC',
            credentials=credentials,
            secure=secure)

        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)



# Configuração do Heroku (perceba que ela herda da configuração de produção)
class HerokuConfig(ConfigProducao):
    SSL_DISABLE = bool(os.environ.get('SSL_DISABLE'))

    @classmethod
    def init_app(cls, app):
        ConfigProducao.init_app(app)

        # Resolve headers do proxy do servidor
        from werkzeug.contrib.fixers import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app)

        # Log em stderr
        import logging
        from logging import StreamHandler

        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)


########## Dicionário para Seleção de Configuração ##########


modos_configuracao = {
    'desenvolvimento': ConfigDesenvolvimento,
    'teste': ConfigTeste,
    'producao': ConfigProducao,
    'heroku': HerokuConfig,

    'padrao': ConfigDesenvolvimento
}

