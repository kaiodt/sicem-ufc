# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Arquivo de Inicialização do Blueprint Principal
################################################################################


from flask import Blueprint


########## Criação do Blueprint ##########


principal = Blueprint('principal', __name__)

# Importação de views

from . import views, errors


########## Disponibilação de Permissões nos Templates ##########


from ..models import Permissao

@principal.app_context_processor
def injetar_permissoes():
    return dict(Permissao=Permissao)

    