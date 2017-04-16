# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Views do Blueprint de Autenticação
################################################################################


from flask import render_template, url_for, redirect, request, flash
from flask_login import current_user, login_user, logout_user, login_required

from . import autenticacao
from .. import db
from .forms import *
from ..models import Usuario
from ..util.email import enviar_email
from ..util.decorators import *


########## Rotas ##########


# Redirecionar usuários não confirmados que fizeram login para uma página
# que informará que o email precisa ser confirmado
@autenticacao.before_app_request
def before_request():
    # Testar se o usuário fez login, não confirmou o email e está tentando
    # acessar uma página que não seja relativa à autenticação ou conteúdo
    # estático (imagens, css, js -> requests automáticos)
    if current_user.is_authenticated \
            and not current_user.confirmado \
            and request.endpoint[:13] != 'autenticacao.' \
            and request.endpoint != 'static':
        # Redirecionar para página informando necessidade de confirmação ou
        # pedido de novo email de confirmação
        return redirect(url_for('autenticacao.nao_confirmado'))


# Página de Login
@autenticacao.route('/login', methods=['GET', 'POST'])
def login():
    # Formulário de login
    form = FormLogin()

    # Após validação do formulário
    if form.validate_on_submit():
        # Obter usuário
        usuario = Usuario.query.filter_by(email=form.email.data).first()

        # Testar se o usuário existe e a senha está correta
        if usuario and usuario.verificar_senha(form.senha.data):
            # Caso o usuário ainda não tenha sido verificado por um administrador
            if not usuario.verificado:
                # Redirecionar para página informando que não foi verificado
                return render_template('autenticacao/nao_verificado.html')

            # Caso o usuário tenha sido verificado, fazer login
            login_user(usuario, form.lembrar.data)

            # Redirecionar para página inicial
            return redirect(request.args.get('next') or url_for('principal.home'))

        flash('Email ou senha incorretos.', 'danger')

    return render_template('autenticacao/login.html', form=form)


# Procedimento de Logout
@autenticacao.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('principal.home'))


# Página de Cadastro de Usuário
@autenticacao.route('/cadastro-usuario', methods=['GET', 'POST'])
def cadastro_usuario():
    # Formulário de cadastro de usuário
    form = FormCadastroUsuario()

    # Após validação do formulário
    if form.validate_on_submit():
        # Adicionar novo usuário no banco de dados
        # (não verificado e não confirmado por padrão)
        novo_usuario = Usuario(email=form.email.data,
                               nome=form.nome.data,
                               senha=form.senha.data)

        db.session.add(novo_usuario)
        db.session.commit()

        # Enviar email para administradores solicitando verificação de
        # novo usuário
        
        # Obter lista de administradores cadastrados
        lista_adms = Usuario.listar_administradores()

        # Gerar lista de emails dos administradores
        destinatarios = [usuario.email for usuario in lista_adms]

        enviar_email(destinatarios,
                     'Verificação de Novo Usuário',
                     'autenticacao/email/verificacao_novo_usuario',
                     novo_usuario=novo_usuario)
        
        flash('Seu cadastro foi recebido e será analisado pelos administradores.', 'info')

        # Redirecionar para página inicial
        return redirect(url_for('principal.home'))

    return render_template('autenticacao/cadastro_usuario.html', form=form)


# Verificação de novo usuário (Somente administradores)
# Esta página é acessada a partir do link de verificação de novo usuário enviado 
# para os emails dos administradores
@autenticacao.route('/verificacao', methods=['GET', 'POST'])
@login_required
@restrito_administrador
def verificacao():
    # Obtendo usuário a ser verificado
    id_usuario = request.args.get('id')
    usuario = Usuario.query.get(id_usuario)

    # Identificação inválida
    if usuario is None:
        flash('Usuário não existe ou foi negado!', 'danger')
        return redirect(url_for('principal.home'))

    # Usuário já verificado
    if usuario.verificado:
        flash('Usuário já verificado.', 'warning')
        return redirect(url_for('principal.home'))

    # Formulário para verificação do usuário, onde pode-se também
    # ser definido seu cargo (nome e email já são preenchidos)
    form = FormVerificarUsuario()
    form.nome.data = usuario.nome
    form.email.data = usuario.email

    # Após validação do formulário
    if form.validate_on_submit():
        # Atribuir cargo escolhido pelo administrador ao novo usuário
        cargo = Cargo.query.filter_by(nome=form.cargo.data).first()
        usuario.cargo = cargo

        # Verificar usuário
        usuario.verificado = True

        # Salvar no banco de dados
        db.session.add(usuario)
        db.session.commit()

        # Enviar email para o usuário, para que confirme o email cadastrado

        # Gerar token de confirmação de email
        token = usuario.gerar_token_confirmacao()

        enviar_email(usuario.email, 
                     'Confirme Seu Cadastro',
                     'autenticacao/email/confirmacao',
                     usuario=usuario,
                     token=token)

        flash('O usuário foi verificado e receberá um email de confirmação.', 'success')

        # Redirecionar para página inicial
        return redirect(url_for('principal.home'))

    return render_template('autenticacao/verificacao_usuario.html', form=form)


# Procedimento de negação de verificação de novo usuário (Somente administradores)
# Esta página é acessada a partir do link de negação verificação de novo usuário enviado 
# para os emails dos administradores
@autenticacao.route('/verificacao-negada')
@login_required
@restrito_administrador
def verificacao_negada():
    # Obtendo usuário a ser negado
    id_usuario = request.args.get('id')
    usuario = Usuario.query.get(id_usuario)

    # Identificação inválida
    if usuario is None:
        flash('Usuário não existe ou já foi negado!', 'danger')
        return redirect(url_for('principal.home'))

    # Caso o usuário já tenha sido verificado por outro administrador, 
    # a negação não ocorrerá.
    if usuario.verificado:
        flash('Este usuário foi verificado por outro administrador!', 'warning')
        return redirect(url_for('principal.home'))

    # Enviar email para o usuário, informando negação da verificação
    enviar_email(usuario.email, 
                 'Cadastro não Autorizado',
                 'autenticacao/email/verificacao_negada',
                 usuario=usuario)

    # Excluir usuário do banco de dados
    db.session.delete(usuario)
    db.session.commit()

    flash('A verificação do usuário foi cancelada.', 'info')

    # Redirecionar para página inicial
    return redirect(url_for('principal.home'))


# Página de Usuário Não Confirmado
# Esta página é acessada quando um usuário já verificado ainda não confirmou
# seu email tenta fazer login no sistema
@autenticacao.route('/nao-confirmado')
def nao_confirmado():
    # Caso o usuário não seja cadastrado ou já esteja confirmado
    if current_user.is_anonymous or current_user.confirmado:
        # Redirecionar para página inicial
        return redirect(url_for('principal.home'))

    return render_template('autenticacao/nao_confirmado.html')


# Página de Confirmação de Conta
@autenticacao.route('/confirmacao/<token>')
@login_required
def confirmacao(token):
    # Caso o usuário já esteja confirmado
    if current_user.confirmado:
        # Redirecionar para a página inicial
        return redirect(url_for('principal.home'))

    # Testar se o token de confirmação é válido
    if current_user.confirmar_conta(token):
        # Usuário foi confirmado
        flash('Seu cadastro foi confirmado. Obrigado!', 'success')
    else:
        # Token inválido (o usuário será redirecionado para página de não confirmado)
        flash('Este link de confirmação é inválido ou expirou.', 'danger')

    # Redirecionar para página inicial
    return redirect(url_for('principal.home'))


# Página de Reenvio de Confirmação de Conta
@autenticacao.route('/confirmacao')
@login_required
def reenviar_confirmacao():
    # Caso o usuário já esteja confirmado
    if current_user.confirmado:
        # Redirecionar para página inicial
        return redirect(url_for('principal.home'))

    # Gerar novo token de confirmação
    token = current_user.gerar_token_confirmacao()

    # Enviar novo email de confirmação
    enviar_email(current_user.email,
                 'Confirme Seu Cadastro',
                 'autenticacao/email/confirmacao',
                 usuario=current_user,
                 token=token)

    flash('Um novo email de confirmação foi enviado. Confira a sua caixa de entrada.', 'info')

    # Redirecionar para página inicial
    return redirect(url_for('principal.home'))


# Página de Alteração de Senha
@autenticacao.route('/alterar-senha', methods=['GET', 'POST'])
@login_required
def alterar_senha():
    # Formulário de alteração de senha
    form = FormAlterarSenha()

    # Após validação do formulário
    if form.validate_on_submit():
        # Testar se a senha está correta
        if current_user.verificar_senha(form.senha_atual.data):
            # Alterar senha antiga para a nova
            current_user.senha = form.senha_nova.data

            # Salvar no banco de dados
            db.session.add(current_user)

            flash('Sua senha foi alterada.', 'success')

            # Redirecionar para página inicial
            return redirect(url_for('principal.home'))
        else:
            flash('Senha incorreta.', 'danger')

    return render_template('autenticacao/alterar_senha.html', form=form)


# Página de Pedido de Recuperação de Senha
# Esta página é acessada pelo link "Esqueci minha senha" na página de login
@autenticacao.route('/recuperar-senha', methods=['GET', 'POST'])
def pedido_recuperacao_senha():
    # Caso o usuário já esteja logado (não precisa de recuperação)
    if not current_user.is_anonymous:
        # Redirecionar para página inicial
        return redirect(url_for('principal.home'))

    # Formulário de pedido recuperação de senha
    form = FormPedidoRecuperarSenha()

    # Após validação do formulário
    if form.validate_on_submit():
        # Obter usuário a partir do email informado
        usuario = Usuario.query.filter_by(email=form.email.data).first()

        # Caso o usuário seja válido
        if usuario:
            # Gerar token de recuperação de senha
            token = usuario.gerar_token_recuperacao_senha()

            # Enviar email com link de redirecionamento para página de recuperação
            # de senha (cadastro de nova senha)
            enviar_email(usuario.email,
                         'Recuperação de Senha',
                         'autenticacao/email/recuperacao_senha',
                         usuario=usuario,
                         token=token)

            flash('Um email com instruções para recuperar sua senha foi enviado.', 'info')

            # Redirecionar para página de login
            return redirect(url_for('autenticacao.login'))

    return render_template('autenticacao/recuperar_senha.html', form=form)


# Confirmação de Recuperação de Senha
# Esta página é acessada a partir do link de recuperação de senha enviado
# para o email de um usuário que solicitou recuperação de senha
@autenticacao.route('/recuperar-senha/<token>', methods=['GET', 'POST'])
def recuperar_senha(token):
    # Caso o usuário já esteja logado (não precisa de recuperação)
    if not current_user.is_anonymous:
        return redirect(url_for('principal.home'))

    # Formulário de pedido recuperação de senha
    form = FormRecuperarSenha()

    # Após validação do formulário
    if form.validate_on_submit():
        # Obter usuário a partir do email informado
        usuario = Usuario.query.filter_by(email=form.email.data).first()

        # Caso o usuário não exista
        if usuario is None:
            # Redirecionar para página inicial
            return redirect(url_for('principal.home'))

        # Caso o usuário exista, e o token de recuperação de senha seja válido,
        # a senha é alterada
        if usuario.recuperar_senha(token, form.senha_nova.data):
            flash('Sua senha foi atualizada.', 'success')

            # Redirecionar para página de login
            return redirect(url_for('autenticacao.login'))
        else:
            # Redirecionar para página inicial
            return redirect(url_for('principal.home'))

    return render_template('autenticacao/recuperar_senha.html', form=form)


# Página de Pedido de Alteração de Email
@autenticacao.route('/alterar-email', methods=['GET', 'POST'])
@login_required
def pedido_alteracao_email():
    # Formulário de alteração de email
    form = FormAlterarEmail()

    # Após validação do formulário
    if form.validate_on_submit():
        # Testar se a senha está correta
        if current_user.verificar_senha(form.senha.data):
            # Obter novo email desejado
            email_novo = form.email_novo.data

            # Gerar token de alteração de email
            token = current_user.gerar_token_alteracao_email(email_novo)

            # Enviar email de confirmação para novo email informado
            enviar_email(email_novo,
                         'Confirme Alteração de Email',
                         'autenticacao/email/alteracao_email',
                         usuario=current_user,
                         token=token)

            flash('Um email com instruções para confirmar seu novo email foi enviado.', 'info')

            # Redirecionar para página inicial
            return redirect(url_for('principal.home'))
        else:
            flash('Senha incorreta.', 'danger')

    return render_template('autenticacao/alterar_email.html', form=form)


# Página de Confirmação de Alteração de Email
# Esta página é acessada a partir do link de confirmação de alteração de email enviado
# para o novo email desejado pelo usuário
@autenticacao.route('/alterar-email/<token>')
@login_required
def alterar_email(token):
    # Caso o token de alteração seja válido, o email é alterado
    if current_user.alterar_email(token):
        flash('Seu email foi atualizado.', 'success')
    else:
        flash('Solicitação inválida.', 'danger')

    # Redirecionar para página inicial
    return redirect(url_for('principal.home'))

