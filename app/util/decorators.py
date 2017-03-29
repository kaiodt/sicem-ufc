# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Decorators de Permissões
################################################################################

from functools import wraps
from flask import abort
from flask_login import current_user

from ..models import Permissao

# Decorator base para restringir páginas somente a usuários
# que possuam certas permissões
def permissao_necessaria(permissao):
    def decorator(f):
        @wraps(f)
        def funcao_decorada(*args, **kwargs):
            if not current_user.autorizado(permissao):
                abort(403)
            
            return f(*args, **kwargs)

        return funcao_decorada

    return decorator

# Decorators específicos por tipo de usuário / permissão

# Administradores / Desenvolvedores
def restrito_administrador(f):
    return permissao_necessaria(Permissao.ADMINISTRAR)(f)

# Cadastradores
def restrito_cadastrador(f):
    return permissao_necessaria(Permissao.CADASTRAR)(f)

# Usuários
def somente_usuarios(f):
    return permissao_necessaria(Permissao.VISUALIZAR)(f)

