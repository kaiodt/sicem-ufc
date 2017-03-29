# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Arquivo de Inicialização dos Blueprints de Administração
################################################################################


from flask_admin import Admin, AdminIndexView, expose
from flask_login import current_user


########## View da Página Inicial do Painel de Administração ##########


class HomeView(AdminIndexView):
    # Restringir acesso apenas para administradores e cadastradores
    def is_accessible(self):
        return current_user.cadastrador()

    @expose('/')
    def home(self):
        return self.render('administracao/home.html')


########## Criação da Instância do Flask Admin ##########


admin = Admin(index_view=HomeView(url='/administracao'))
admin.name = 'SICEM-UFC'
admin.template_mode = 'bootstrap3'

