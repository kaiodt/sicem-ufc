# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Arquivo de Execução da Aplicação
################################################################################


import os, sys

from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

from app import criar_app, db
import app.models as model


########## Configuração de Codificação UTF-8 ##########

# Necessário para que os caracteres especiais do português sejam reconhecidos

reload(sys)
sys.setdefaultencoding('utf-8')


########## Criação da Aplicação via Application Factory ##########


# A configuração é definida pela variável de ambiente FLASK_CONFIG
# Caso uma configuração específica não seja escolhida, a padrão é utilizada

app = criar_app(os.getenv('FLASK_CONFIG') or 'padrao')


########## Instanciação de Extensões ##########


manager = Manager(app)
migrate = Migrate(app, db)


########## Comandos de Shell ##########


# Shell de python com acesso à aplicação e ao banco de dados
# OBS: Os modelos do banco de dados são acessados da seguinte maneira:
# model.[Modelo], por exemplo, model.Usuario

def make_shell_context():
    return dict(app=app, db=db, model=model)

manager.add_command('shell', Shell(make_context=make_shell_context))


# Comandos de migração do banco de dados

manager.add_command('db', MigrateCommand)


# Comando de deploy da aplicação

@manager.command
def deploy():
    from flask_migrate import upgrade
    from app.models import Cargo, Usuario

    # Migrar banco de dados para última versão
    # A pasta "migrations" precisa existir e deve ter pelo menos uma
    # versão de migração de banco de dados
    upgrade()

    # Cria os cargos dos usuários, se ainda não foram criados
    Cargo.criar_cargos()
    
    # Criar administrador padrão, caso ainda não haja um
    Usuario.criar_administrador()


########## Execução da Aplicação ##########


if __name__ == '__main__':
    manager.run()

