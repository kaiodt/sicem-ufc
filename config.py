# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Arquivo de Configuração
################################################################################


import os


########## Classes de Configuração ##########


# Cada classe traz configurações para um tipo específico de uso da aplicação

# Configuração Geral (Comum a todas as configurações)
class Config:
    # Configurações sensíveis devem ser definidas como variáveis de ambiente!

    # Usada nos processos de autenticação do Flask
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Desabilitar encriptação por padrão
    SSL_DISABLE = True

    # Dados do primeiro administrador
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    ADMIN_SENHA = os.environ.get('ADMIN_SENHA')

    # Gerar commits do banco de dados ao final de cada request
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    # Configuração do envio de emails do sistema
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_SENDER = os.environ.get('MAIL_SENDER')

    # Configuração do Mapbox
    MAPBOX_MAP_ID = 'mapbox.streets'
    MAPBOX_ACCESS_TOKEN = os.environ.get('MAPBOX_ACCESS_TOKEN')

    # Método executado quando a aplicação é criada (cls é a própria classe)
    @classmethod
    def init_app(cls, app):
        pass


# Configuração de Desenvolvimento
class ConfigDesenvolvimento(Config):
    DEBUG = True

    # Banco de dados (local)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
      'postgresql://sicem_ufc_admin:sicem_ufc@localhost/dev_sicem_ufc'


# Configuração de Teste
class ConfigTeste(Config):
    TESTING = True


# Configuração de Produção
class ConfigProducao(Config):
    # Banco de dados
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    # Método executado quando a aplicação é criada (cls é a própria classe)
    @classmethod
    def init_app(cls, app):
       # Executar método inicial da configuração padrão
        Config.init_app(app)

        # Configuração do envio de emails com logs de erros críticos para os
        # desenvolvedores

        import logging
        from logging.handlers import SMTPHandler
        from app.models import Usuario

        credentials = None
        secure = None

        # Obter dados da conta de envio de emails do sistema

        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()

        # Gerar lista de emails dos desenvolvedores

        lista_devs = Usuario.listar_desenvolvedores()
        emails_desenvolvedores = [usuario.email for usuario in lista_devs]

        # Criação do objeto que enviará os emails

        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.MAIL_SENDER,
            toaddrs=emails_desenvolvedores,
            subject='Erro de Sistema - SICEM-UFC',
            credentials=credentials,
            secure=secure)

        # Definindo nível de log (apenas erros graves)
        mail_handler.setLevel(logging.ERROR)

        # Registrando o objeto na aplicação
        app.logger.addHandler(mail_handler)


# Configuração do Heroku (herda da Configuração de Produção)
class ConfigHeroku(ConfigProducao):
    # Habilitar encriptação
    SSL_DISABLE = bool(os.environ.get('SSL_DISABLE'))

    # Método executado quando a aplicação é criada (cls é a própria classe)
    @classmethod
    def init_app(cls, app):
        # Executar método inicial da configuração de produção
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

# A configuração é selecionada na criação da aplicação

modos_configuracao = {
    'desenvolvimento': ConfigDesenvolvimento,
    'teste': ConfigTeste,
    'producao': ConfigProducao,
    'heroku': ConfigHeroku,

    'padrao': ConfigDesenvolvimento
}

