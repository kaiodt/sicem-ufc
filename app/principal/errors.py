# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Views de Erros
################################################################################


from flask import render_template

from . import principal


########## Rotas ##########


# Erro 403 - Acesso Proibido
@principal.app_errorhandler(403)
def proibido(e):
    return render_template('erros/403.html'), 403


# Erro 404 - Página Não Encontrada
@principal.app_errorhandler(404)
def pagina_nao_encontrada(e):
    return render_template('erros/404.html'), 404


# Erro 500 - Erro Interno no Servidor
@principal.app_errorhandler(500)
def erro_interno_servidor(e):
    return render_template('erros/500.html'), 500

