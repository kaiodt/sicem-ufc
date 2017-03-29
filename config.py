# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Arquivo de Configuração
################################################################################


import os

from app.models import Usuario

# Diretório base
basedir = os.path.abspath(os.path.dirname(__file__))


########## Classes de Configuração ##########


# Configuração Geral
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or \
        'w\xc4\x1d\xfc\xaf\xab.\x03a\x02!\x87#p\nH\xcb\xd4\x86yV\x90Z\x89'  # !!!!!!!

    SSL_DISABLE = True

    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'kaiodtr@gmail.com'      # !!!!!!!
    ADMIN_SENHA = os.environ.get('ADMIN_SENHA') or '123456'                 # !!!!!!!

    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'sicem.ufc@gmail.com'  # !!!!!!!
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'SisInfoEquipMan'      # !!!!!!!
    MAIL_SENDER = os.environ.get('MAIL_SENDER') or 'SICEM-UFC <sicem.ufc@gmail.com>'

    MAPBOX_MAP_ID = 'mapbox.streets'
    MAPBOX_ACCESS_TOKEN = os.environ.get('MAPBOX_ACCESS_TOKEN') or \
        'pk.eyJ1IjoibHVjYXNzbSIsImEiOiJjaW05cDlmMXYwMDFidzhtM3JzN291dzZqIn0.WC0WGjp2FzN0VNOZ3JHjnQ'

        
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

