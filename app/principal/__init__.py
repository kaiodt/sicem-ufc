# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Arquivo de Inicialização do Blueprint Principal
################################################################################


from flask import Blueprint


########## Criação do Blueprint ##########


principal = Blueprint('principal', __name__)

# Importação das views

from . import views, errors


########## Disponibilização de Permissões nos Templates ##########

# Torna a classe "Permissao" (em "models.py") global para todos os templates

from ..models import Permissao

@principal.app_context_processor
def injetar_permissoes():
    return dict(Permissao=Permissao)

