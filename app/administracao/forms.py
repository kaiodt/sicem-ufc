# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Fomulários do Painel de Administração
################################################################################


from datetime import date, timedelta
from flask import request, flash
from flask_wtf import FlaskForm
from flask_admin.form.fields import Select2Field, Select2TagsField
from flask_admin.form.widgets import DatePickerWidget
from flask_admin.contrib.sqla.fields import QuerySelectField, QuerySelectMultipleField
from flask_admin.contrib.geoa.fields import GeoJSONField
from wtforms import StringField, PasswordField, BooleanField, IntegerField, DecimalField, \
                    SubmitField, TextAreaField, DateField
from wtforms import ValidationError
from wtforms.validators import InputRequired, Optional, Regexp, Email, Length, NumberRange, \
                               EqualTo

from .. import db
from ..models import *
from .fields import DateFieldMod


########## Formulário Base (Tradução habilitada) ##########


class FormBase(FlaskForm):
    class Meta:
        locales = ['pt_BR']


########## Formulários para os Modelos do Sistema ##########


# Edição de Cargo
class FormEditarCargo(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 36)])

    permissoes = IntegerField('Permissões', validators=[InputRequired(),
                                                        NumberRange(0, 255)])

    padrao = BooleanField('Padrão')

    usuarios = QuerySelectMultipleField('Usuários',
                                        allow_blank=True,
                                        query_factory= lambda: 
                                        Usuario.query.order_by('nome').all())


# Criação de Usuário
class FormCriarUsuario(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                               Length(1, 64),
                               Regexp(u'[A-Za-z ÁÉÍÓÚÂÊÎÔÛÃÕÇáéíóúâêîôûãõç]*$')])

    email = StringField('Email', validators=[InputRequired(),
                                             Length(1, 64),
                                             Email()])

    senha = PasswordField('Senha', validators=[InputRequired(),
                                               Length(6, 16)])

    cargo = QuerySelectField('Cargo',
                             query_factory=lambda: Cargo.query.order_by('nome').all())

    confirmado = BooleanField('Confirmado')


    # Certificar que o email é diferente dos já cadastrados
    def validate_email(self, field):
        if Usuario.query.filter_by(email=field.data).first():
            raise ValidationError('Email já cadastrado.')


# Edição de Usuário
class FormEditarUsuario(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                               Length(1, 64),
                               Regexp(u'[A-Za-z ÁÉÍÓÚÂÊÎÔÛÃÕÇáéíóúâêîôûãõç]*$')])

    email = StringField('Email', validators=[InputRequired(),
                                             Length(1, 64),
                                             Email()])

    cargo = QuerySelectField('Cargo',
                             query_factory=lambda: Cargo.query.order_by('nome').all())

    verificado = BooleanField('Verificado')
    

    # Certificar que, se houve alteração no email, o novo é diferente dos já cadastrados
    def validate_email(self, field):
        if Usuario.query.filter_by(email=field.data).first() and \
                field.data != Usuario.query.get(request.args.get('id')).email:
            raise ValidationError('Email já cadastrado.')


    # Avisar ao administrador quando a verificação de um usuário é alterada de 
    # verdadeira para falsa
    def validate_verificado(self, field):
        if Usuario.query.get(request.args.get('id')).verificado and \
                field.data == False:
            flash('Você retirou a verificação deste usuário, e ele não poderá mais acessar o sistema.',
                  'warning')


# Criação de Instituição
class FormCriarInstituicao(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])


# Edição de Instituição
class FormEditarInstituicao(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])

    campi = QuerySelectMultipleField('Campi',
                                     allow_blank=True,
                                     query_factory=lambda: 
                                        Campus.query.order_by('nome').all())


# Criação de Campus
class FormCriarCampus(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])

    instituicao = QuerySelectField('Instituição',
                                   query_factory=lambda: 
                                       Instituicao.query.order_by('nome').all())

    mapeamento = GeoJSONField('Mapeamento', srid=-1, session=db.session,
                              geometry_type='MULTIPOLYGON',
                              # Aumentar o mapa e centralizar em Fortaleza
                              render_kw={'data-width':400, 'data-height':400,
                                         'data-zoom':10,
                                         'data-lat':-3.7911773, 'data-lng':-38.5893123})


# Edição de Campus
class FormEditarCampus(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])

    instituicao = QuerySelectField('Instituição',
                                   query_factory=lambda: 
                                       Instituicao.query.order_by('nome').all())

    mapeamento = GeoJSONField('Mapeamento', srid=-1, session=db.session,
                              geometry_type='MULTIPOLYGON',
                              # Aumentar o mapa
                              render_kw={'data-width':400, 'data-height':400})

    centros = QuerySelectMultipleField('Centros',
                                       allow_blank=True,
                                       query_factory=lambda: 
                                           Centro.query.order_by('nome').all())


    # Inicialização
    def __init__(self, *args, **kwargs):
        super(FormEditarCampus, self).__init__(*args, **kwargs)
        
        # Existe um problema com a extensão Leaflet que não permite
        # a edição de mapas com polígonos.        
        flash('No momento, a edição de mapeamento não é possível.', 'info')


# Criação de Centro
class FormCriarCentro(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])

    campus = QuerySelectField('Campus',
                        query_factory=lambda: Campus.query.order_by('nome').all())

    mapeamento = GeoJSONField('Mapeamento', srid=-1, session=db.session,
                              geometry_type='MULTIPOLYGON',
                              # Aumentar o mapa e centralizar em Fortaleza
                              render_kw={'data-width':400, 'data-height':400,
                                         'data-zoom':10,
                                         'data-lat':-3.7911773, 'data-lng':-38.5893123})


# Edição de Centro
class FormEditarCentro(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])

    campus = QuerySelectField('Campus',
                        query_factory=lambda: Campus.query.order_by('nome').all())

    mapeamento = GeoJSONField('Mapeamento', srid=-1, session=db.session,
                              geometry_type='MULTIPOLYGON',
                              # Aumentar o mapa
                              render_kw={'data-width':400, 'data-height':400})

    departamentos = QuerySelectMultipleField('Departamentos',
            allow_blank=True,
            query_factory=lambda: Departamento.query.order_by('nome').all())


    # Inicialização
    def __init__(self, *args, **kwargs):
        super(FormEditarCentro, self).__init__(*args, **kwargs)

        # Existe um problema com a extensão Leaflet que não permite
        # a edição de mapas com polígonos.
        flash('No momento, a edição de mapeamento não é possível.', 'info')


# Criação de Departamento
class FormCriarDepartamento(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])

    centro = QuerySelectField('Centro',
                        query_factory=lambda: Centro.query.order_by('nome').all())


# Edição de Departamento
class FormEditarDepartamento(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])

    centro = QuerySelectField('Centro',
                        query_factory=lambda: Centro.query.order_by('nome').all())

    blocos = QuerySelectMultipleField('Blocos',
                            allow_blank=True,
                            query_factory=lambda: Bloco.query.order_by('nome').all())


# Criação de Bloco
class FormCriarBloco(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])

    departamento = QuerySelectField('Departamento',
                                query_factory=lambda: 
                                Departamento.query.order_by('nome').all())

    localizacao = GeoJSONField('Localização', srid=-1, session=db.session,
                                geometry_type='POINT',
                                # Aumentar o mapa e centralizar em Fortaleza
                                render_kw={'data-width':400, 'data-height':400,
                                           'data-zoom':10,
                                           'data-lat':-3.7911773, 'data-lng':-38.5893123})


# Edição de Bloco
class FormEditarBloco(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])

    departamento = QuerySelectField('Departamento',
            query_factory=lambda: Departamento.query.order_by('nome').all())

    localizacao = GeoJSONField('Localização', srid=-1, session=db.session,
                               geometry_type='POINT',
                               # Aumentar o mapa
                               render_kw={'data-width':400, 'data-height':400})

    ambientes = QuerySelectMultipleField('Ambientes',
                allow_blank=True,
                query_factory=lambda: Ambiente.query.order_by('nome').all())


# Criação de Ambiente (Escolha do tipo de ambiente a ser criado)
class FormCriarAmbiente(FormBase):
    tipo_ambiente = Select2Field('', validators=[InputRequired()],
                    # Obter os tipos de ambientes automaticamente
                    choices=[(tipo.endpoint, tipo.nome_formatado_singular) 
                        for tipo in Ambiente.__subclasses__()])

    proximo = SubmitField('Próximo')


# Criação de Ambiente Interno
class FormCriarAmbienteInterno(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])

    andar = Select2Field('Andar',
      choices=[('Térreo', 'Térreo')] + [(str(n)+'º Andar', str(n)+'º Andar') 
               for n in range(1, 11)])

    bloco = QuerySelectField('Bloco',
                        query_factory=lambda: Bloco.query.order_by('nome').all())

    detalhe_localizacao = TextAreaField('Detalhe de Localização')

    area = DecimalField('Área (m²)', use_locale=True,
                        validators=[Optional(), NumberRange(0)])

    populacao = IntegerField('População', validators=[Optional(), NumberRange(0)])


# Edição de Ambiente Interno
class FormEditarAmbienteInterno(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])

    andar = Select2Field('Andar',
      choices=[('Térreo', 'Térreo')] + [(str(n)+'º Andar', str(n)+'º Andar')
               for n in range(1, 11)])    

    bloco = QuerySelectField('Bloco',
                        query_factory=lambda: Bloco.query.order_by('nome').all())

    detalhe_localizacao = TextAreaField('Detalhe de Localização')

    area = DecimalField('Área (m²)', use_locale=True,
                        validators=[Optional(), NumberRange(0)])

    populacao = IntegerField('População', validators=[Optional(), NumberRange(0)])

    equipamentos = QuerySelectMultipleField('Equipamentos',
            allow_blank=True,
            query_factory=lambda: 
                Equipamento.query.order_by('tipo_equipamento').all())


# Criação de Ambiente Externo
class FormCriarAmbienteExterno(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])

    bloco = QuerySelectField('Bloco',
                        query_factory=lambda: Bloco.query.order_by('nome').all())

    detalhe_localizacao = TextAreaField('Detalhe de Localização')


# Edição de Ambiente Externo
class FormEditarAmbienteExterno(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])

    bloco = QuerySelectField('Bloco',
                        query_factory=lambda: Bloco.query.order_by('nome').all())

    detalhe_localizacao = TextAreaField('Detalhe de Localização')

    equipamentos = QuerySelectMultipleField('Equipamentos',
            allow_blank=True,
            query_factory=lambda: 
                Equipamento.query.order_by('tipo_equipamento').all())


# Criação de Subestação Abrigada
class FormCriarSubestacaoAbrigada(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])

    bloco = QuerySelectField('Bloco', 
        query_factory=lambda: 
            # Mostrar apenas blocos especiais de subestação
            Bloco.query.filter(Bloco.nome.like('Subestações%')).order_by('nome').all())

    localizacao = GeoJSONField('Localização', srid=-1, session=db.session,
                               geometry_type='POINT',
                               # Aumentar o mapa e centralizar em Fortaleza
                               render_kw={'data-width':400, 'data-height':400,
                                          'data-zoom':10,
                                          'data-lat':-3.7911773, 'data-lng':-38.5893123})

    detalhe_localizacao = TextAreaField('Detalhe de Localização')


# Edição de Subestação Abrigada
class FormEditarSubestacaoAbrigada(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])

    bloco = QuerySelectField('Bloco', 
        query_factory=lambda: 
            # Mostrar apenas blocos especiais de subestação
            Bloco.query.filter(Bloco.nome.like('Subestações%')).order_by('nome').all())

    localizacao = GeoJSONField('Localização', srid=-1, session=db.session,
                               geometry_type='POINT',
                               # Aumentar o mapa
                               render_kw={'data-width':400, 'data-height':400})

    detalhe_localizacao = TextAreaField('Detalhe de Localização')

    equipamentos = QuerySelectMultipleField('Equipamentos',
            allow_blank=True,
            query_factory=lambda: 
                Equipamento.query.order_by('tipo_equipamento').all())


# Criação de Subestação Aérea
class FormCriarSubestacaoAerea(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])

    bloco = QuerySelectField('Bloco', 
        query_factory=lambda: 
            # Mostrar apenas blocos especiais de subestação
            Bloco.query.filter(Bloco.nome.like('Subestações%')).order_by('nome').all())

    localizacao = GeoJSONField('Localização', srid=-1, session=db.session,
                               geometry_type='POINT',
                               # Aumentar o mapa e centralizar em Fortaleza
                               render_kw={'data-width':400, 'data-height':400,
                                          'data-zoom':10,
                                          'data-lat':-3.7911773, 'data-lng':-38.5893123})

    detalhe_localizacao = TextAreaField('Detalhe de Localização')


# Edição de Subestação Aérea
class FormEditarSubestacaoAerea(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])

    bloco = QuerySelectField('Bloco', 
        query_factory=lambda: 
            # Mostrar apenas blocos especiais de subestação
            Bloco.query.filter(Bloco.nome.like('Subestações%')).order_by('nome').all())

    localizacao = GeoJSONField('Localização', srid=-1, session=db.session,
                               geometry_type='POINT',
                               # Aumentar o mapa
                               render_kw={'data-width':400, 'data-height':400})

    detalhe_localizacao = TextAreaField('Detalhe de Localização')

    equipamentos = QuerySelectMultipleField('Equipamentos',
            allow_blank=True,
            query_factory=lambda: 
                Equipamento.query.order_by('tipo_equipamento').all())


# Criação de Equipamento (Escolha do tipo de equipamento a ser criado)
class FormCriarEquipamento(FormBase):
    tipo_equipamento = Select2Field('', validators=[InputRequired()],
                    # Obter os tipos de equipamentos automaticamente
                    choices=[(tipo.endpoint, tipo.nome_formatado_singular) 
                        for tipo in Equipamento.__subclasses__()])

    proximo = SubmitField('Próximo')


# Criação de Extintor
class FormCriarExtintor(FormBase):
    # Caso não haja número de tombamento, usar 0
    tombamento = IntegerField('Tombamento', validators=[NumberRange(0)])

    classificacao = Select2Field('Classificação', 
                                 choices=[('Água [A]', 'Água [A]'),
                                          ('Espuma [AB]', 'Espuma [AB]'),
                                          ('CO2 [BC]', 'CO2 [BC]'),
                                          ('Pó Químico [BC]', 'Pó Químico [BC]'),
                                          ('Pó Químico [ABC]', 'Pó Químico [ABC]')],
                                 validators=[InputRequired()])

    carga_nominal = DecimalField('Carga Nominal (kg)', use_locale=True,
                                 validators=[NumberRange(0)])

    fabricante = StringField('Fabricante', validators=[Length(1, 64)])

    ambiente = QuerySelectField('Ambiente',
                                query_factory=lambda: 
                                    Ambiente.query.order_by('nome').all())

    intervalo_manutencao = IntegerField('Intervalo de Manutenção (Meses)',
                                        validators=[InputRequired(), NumberRange(0)])
                                                                               
    em_uso = BooleanField('Em Uso')

    info_adicional = TextAreaField('Informações Adicionais')                         


    # Certificar que o número de tombamento ainda não existe
    def validate_tombamento(self, field):
        # Desconsiderar o caso 0 (quando não há número de tombamento)
        if field.data != 0:
            if Equipamento.query.filter_by(tombamento=field.data).first():
                raise ValidationError('Equipamento já cadastrado.')


# Edição de Extintor
class FormEditarExtintor(FormBase):
    # Caso não haja número de tombamento, usar 0
    tombamento = IntegerField('Tombamento', validators=[NumberRange(0)])

    classificacao = Select2Field('Classificação', 
                                 choices=[('Água [A]', 'Água [A]'),
                                          ('Espuma [AB]', 'Espuma [AB]'),
                                          ('CO2 [BC]', 'CO2 [BC]'),
                                          ('Pó Químico [BC]', 'Pó Químico [BC]'),
                                          ('Pó Químico [ABC]', 'Pó Químico [ABC]')],
                                 validators=[InputRequired()])

    carga_nominal = DecimalField('Carga Nominal (kg)', use_locale=True,
                                 validators=[NumberRange(0)])

    fabricante = StringField('Fabricante', validators=[Length(1, 64)])

    ambiente = QuerySelectField('Ambiente',
                                query_factory=lambda: 
                                    Ambiente.query.order_by('nome').all())

    intervalo_manutencao = IntegerField('Intervalo de Manutenção (Meses)',
                                        validators=[InputRequired(),
                                                    NumberRange(0)])
    
    em_uso = BooleanField('Em Uso')

    info_adicional = TextAreaField('Informações Adicionais')

    manutencoes = QuerySelectMultipleField('Manutenções',
                                           query_factory=lambda: Manutencao.query.all(),
                                           allow_blank=True)


    # Certificar que, se houve alteração no número de tombamento, o novo número
    # não é de um equipamento já existente
    def validate_tombamento(self, field):
        # Desconsiderar o caso 0 (quando não há número de tombamento)
        if field.data != 0:
            if Equipamento.query.filter_by(tombamento=field.data).first() and \
               field.data != Equipamento.query.get(request.args.get('id')).tombamento:
                raise ValidationError('Equipamento já cadastrado.')


# Criação de Condicionador de Ar
class FormCriarCondicionadorAr(FormBase):
    # Caso não haja número de tombamento, usar 0
    tombamento = IntegerField('Tombamento', validators=[NumberRange(0)])

    classificacao = Select2Field('Classificação', 
                                 choices=[('Split', 'Split'),
                                          ('Janela', 'Janela'),
                                          ('Teto Aparente', 'Teto Aparente'),
                                          ('Piso Aparente', 'Piso Aparente')])

    cap_refrigeracao = IntegerField('Capacidade de Refrigeração (Btu/h)',
                                    validators=[NumberRange(0)])

    pot_nominal = IntegerField('Potência Nominal de Entrada (W)',
                               validators=[Optional(), NumberRange(0)])

    tensao_alimentacao = Select2Field('Tensão de Alimentação (V)',
                                      choices=[(220, '220'), (380, '380')],
                                      coerce=int,
                                      validators=[InputRequired()])

    eficiencia = Select2Field('Eficiência (Selo Procel)', 
                                 choices=[('A', 'A'), ('B', 'B'), ('C', 'C'),
                                          ('D', 'D'), ('E', 'E'), ('F', 'F'),
                                          ('G', 'G')])

    fabricante = StringField('Fabricante', validators=[Length(1, 64)])

    ambiente = QuerySelectField('Ambiente',
                                query_factory=lambda: 
                                    Ambiente.query.order_by('nome').all())

    intervalo_manutencao = IntegerField('Intervalo de Manutenção (Meses)',
                                        validators=[InputRequired(), NumberRange(0)])
                                                                               
    em_uso = BooleanField('Em Uso')

    info_adicional = TextAreaField('Informações Adicionais')                         


    # Certificar que o número de tombamento ainda não existe
    def validate_tombamento(self, field):
        # Desconsiderar o caso 0 (quando não há número de tombamento)
        if field.data != 0:
            if Equipamento.query.filter_by(tombamento=field.data).first():
                raise ValidationError('Equipamento já cadastrado.')


# Edição de Condicionador de Ar
class FormEditarCondicionadorAr(FormBase):
    # Caso não haja número de tombamento, usar 0
    tombamento = IntegerField('Tombamento', validators=[NumberRange(0)])

    classificacao = Select2Field('Classificação', 
                                 choices=[('Split', 'Split'),
                                          ('Janela', 'Janela'),
                                          ('Teto Aparente', 'Teto Aparente'),
                                          ('Piso Aparente', 'Piso Aparente')])

    cap_refrigeracao = IntegerField('Capacidade de Refrigeração (Btu/h)',
                                    validators=[NumberRange(0)])

    pot_nominal = IntegerField('Potência Nominal de Entrada (W)',
                               validators=[Optional(), NumberRange(0)])

    tensao_alimentacao = Select2Field('Tensão de Alimentação (V)',
                                      choices=[(220, '220'), (380, '380')],
                                      coerce=int,
                                      validators=[InputRequired()])

    eficiencia = Select2Field('Eficiência (Selo Procel)', 
                                 choices=[('A', 'A'), ('B', 'B'), ('C', 'C'),
                                          ('D', 'D'), ('E', 'E'), ('F', 'F'),
                                          ('G', 'G')])

    fabricante = StringField('Fabricante', validators=[Length(1, 64)])

    ambiente = QuerySelectField('Ambiente',
                                query_factory=lambda: 
                                    Ambiente.query.order_by('nome').all())

    intervalo_manutencao = IntegerField('Intervalo de Manutenção (Meses)',
                                        validators=[InputRequired(), NumberRange(0)])
                                                                               
    em_uso = BooleanField('Em Uso')

    info_adicional = TextAreaField('Informações Adicionais')                         

    manutencoes = QuerySelectMultipleField('Manutenções',
                                           query_factory=lambda: Manutencao.query.all(),
                                           allow_blank=True)


    # Certificar que, se houve alteração no número de tombamento, o novo número
    # não é de um equipamento já existente
    def validate_tombamento(self, field):
        # Desconsiderar o caso 0 (quando não há número de tombamento)
        if field.data != 0:
            if Equipamento.query.filter_by(tombamento=field.data).first() and \
               field.data != Equipamento.query.get(request.args.get('id')).tombamento:
                raise ValidationError('Equipamento já cadastrado.')


# Criação de Manutenção
class FormCriarManutencao(FormBase):
    # Caso não haja número de ordem de serviço, usar 0
    num_ordem_servico = IntegerField('Número da Ordem de Serviço',
                                     validators=[InputRequired(),
                                                 NumberRange(0)])

    data_abertura = DateField('Data de Abertura', widget=DatePickerWidget(),
                              render_kw={'data-date-format': 'DD.MM.YYYY'},
                              format='%d.%m.%Y',
                              default=date.today(),
                              validators=[InputRequired()])

    data_conclusao = DateFieldMod('Data de Conclusão', widget=DatePickerWidget(),
                               render_kw={'data-date-format': 'DD.MM.YYYY'},
                               format='%d.%m.%Y',
                               validators=[])

    tipo_manutencao = Select2Field('Tipo de Manutenção',
                                   choices=[('Preventiva', 'Preventiva'),
                                            ('Corretiva', 'Corretiva'),
                                            ('Troca', 'Troca'),
                                            ('Inicial', 'Inicial')])

    equipamento = QuerySelectField('Equipamento',
        query_factory=lambda: 
            Equipamento.query.filter_by(em_uso=True).filter_by(em_manutencao=False)\
                             .order_by('tipo_equipamento').all())

    descricao_servico = TextAreaField('Descrição do Serviço')

    status = Select2Field('Status', choices=[('Aberta', 'Aberta'),
                                             ('Concluída', 'Concluída')])


    # Inicialização
    def __init__(self, *args, **kwargs):
        super(FormCriarManutencao, self).__init__(*args, **kwargs)

        # Caso o id de um equipamento esteja presente na query string, o campo
        # de equipamento é automaticamente preenchido
        if request.args.get('id'):
            # Buscar equipamento no banco de dados e preencher campo no formulário
            self.equipamento.data = Equipamento.query.get(request.args.get('id'))

            # Desativar edição do campo de equipamento
            self.equipamento.render_kw = dict(disabled='disabled')

            # Caso um parâmetro de tipo de manutenção seja passado pela query string,
            # alguns campos relevantes são preenchidos automaticamente, de acordo com
            # o tipo de manutenção

            # Manutenção tipo inicial
            if request.args.get('tipo') == 'inicial':
                # Preencher o campo de tipo de manutenção e desabilitar sua edição
                self.tipo_manutencao.data = 'Inicial'
                self.tipo_manutencao.render_kw = dict(disabled='disabled')

                # Preencher o campo de status e desabilitar sua edição
                self.status.data = 'Concluída'
                self.status.render_kw = dict(disabled='disabled')


    # Certificar que o número da ordem de serviço seja diferente dos já existentes
    def validate_num_ordem_servico(self, field):
        # Desconsiderar o caso 0 (quando não há número de ordem de serviço)
        if field.data != 0:
            if Manutencao.query.filter_by(num_ordem_servico=field.data).first():
                raise ValidationError('Manutenção já cadastrada.')


    # Certificar que a data de abertura não seja no futuro
    def validate_data_abertura(self, field):
      if field.data > date.today():
        raise ValidationError('Não é possível cadastrar datas no futuro.')


    # Certificar que, se a manutenção foi concluída, uma data de conclusão foi 
    # inserida e que esta data não seja no futuro, nem anterior à data de abertura
    def validate_data_conclusao(self, field):
        if self.status.data == 'Concluída':
            # Testar se foi inserida data de conclusão
            if field.data is None:
                raise ValidationError('Cadastre a data de conclusão.')
            
            # Testar se a data está no futuro
            if field.data > date.today():
                raise ValidationError('Não é possível cadastrar datas no futuro.')

            # Testar se a data de conclusão não é anterior à data de abertura
            if field.data < self.data_abertura.data:
                raise ValidationError('Data de conclusão anterior à data de abertura.')


    # Certificar que não seja possível abrir uma nova manutenção para
    # um equipamento que já possua uma manutenção aberta
    def validate_equipamento(self, field):
        if self.status.data == 'Aberta' and field.data.em_manutencao:
            raise ValidationError('Equipamento já em manutenção. Conclua a última manutenção.')


    # Certificar que se uma data de conclusão foi inserida, o status da 
    # manutenção deve ser "Concluída"
    def validate_status(self, field):
        if self.data_conclusao.data:
            if field.data == 'Aberta':
                raise ValidationError(
                    'Data de Conclusão cadastrada. Mude Status para "Concluída" ou deixe \
                     Data de Conclusão em branco.')


    # Certificar que não seja possível criar uma manutenção inicial para
    # um equipamento que já possua uma.
    # A manutenção inicial só será cadastrada por meio deste formulário quando
    # um equipamento é criado e o usuário opta por cadastrar uma manutenção
    # inicial personalizada.
    def validate_tipo_manutencao(self, field):
        # Caso haja o argumento 'tipo' com valor 'inicial' na query string, esta
        # é de fato a manutenção inicial do equipamento, e será validada, do contrário,
        # não será possível criar outra manutenção inicial.
        if field.data == 'Inicial' and request.args.get('tipo') != 'inicial':
            raise ValidationError(
                'Este equipamento já possui manutenção inicial. Edite a exstente.')


# Edição de Manutenção
class FormEditarManutencao(FormBase):
    # Caso não haja número de ordem de serviço, usar 0
    num_ordem_servico = IntegerField('Número da Ordem de Serviço',
                                     validators=[InputRequired(),
                                                 NumberRange(0)])

    data_abertura = DateField('Data de Abertura', widget=DatePickerWidget(),
                              render_kw={'data-date-format': 'DD.MM.YYYY'},
                              format='%d.%m.%Y',
                              validators=[InputRequired()])

    data_conclusao = DateFieldMod('Data de Conclusão', widget=DatePickerWidget(),
                                  render_kw={'data-date-format': 'DD.MM.YYYY'},
                                  format='%d.%m.%Y')
    
    tipo_manutencao = Select2Field('Tipo de Manutenção',
                                   choices=[('Preventiva', 'Preventiva'),
                                            ('Corretiva', 'Corretiva'),
                                            ('Troca', 'Troca'),
                                            ('Inicial', 'Inicial')])

    equipamento = QuerySelectField('Equipamento',
        query_factory=lambda: 
            Equipamento.query.filter_by(em_uso=True)\
                             .order_by('tipo_equipamento').all())

    descricao_servico = TextAreaField('Descrição do Serviço')

    status = Select2Field('Status', choices=[('Aberta', 'Aberta'),
                                             ('Concluída', 'Concluída')])


    # Inicialização
    def __init__(self, *args, **kwargs):
        super(FormEditarManutencao, self).__init__(*args, **kwargs)

        # A edição do campo de equipamento sempre será desabilitada, para evitar
        # comprometimento do banco de dados.
        self.equipamento.render_kw = dict(disabled='disabled')

        # Obter o id da manutenção
        id_manutencao = request.args.get('id')

        # Caso a manutenção seja do tipo inicial, desabilitar edição dos campos
        # de tipo de manutenção e de status
        if Manutencao.query.get(id_manutencao).tipo_manutencao == 'Inicial':
            self.tipo_manutencao.render_kw = dict(disabled='disabled')
            self.status.render_kw = dict(disabled='disabled')


    # Certificar que, se houve alteração no número da ordem de serviço,
    # o novo número seja diferente dos já existentes
    def validate_num_ordem_servico(self, field):
        # Desconsiderar o caso 0 (quando não há número de ordem de serviço)
        if field.data != 0:
            if Manutencao.query.filter_by(num_ordem_servico=field.data).first() and \
               field.data != Manutencao.query.get(request.args.get('id')).num_ordem_servico:
                raise ValidationError('Manutenção já cadastrada.')


    # Certificar que a data de abertura não seja no futuro
    def validate_data_abertura(self, field):
      if field.data > date.today():
        raise ValidationError('Não é possível cadastrar datas no futuro.')


    # Certificar que, se a manutenção foi concluída, uma data de conclusão foi 
    # inserida e que esta data não seja no futuro, nem anterior à data de abertura
    def validate_data_conclusao(self, field):
        if self.status.data == 'Concluída':
            # Testar se foi inserida data de conclusão
            if field.data is None:
                raise ValidationError('Cadastre a data de conclusão.')
            
            # Testar se a data está no futuro
            if field.data > date.today():
                raise ValidationError('Não é possível cadastrar datas no futuro.')

            # Testar se a data de conclusão não é anterior à data de abertura
            if field.data < self.data_abertura.data:
                raise ValidationError('Data de conclusão anterior à data de abertura.')


    # Certificar que se uma data de conclusão foi inserida, o status da 
    # manutenção deve ser "Concluída"
    def validate_status(self, field):
        if self.data_conclusao.data:
            if field.data == 'Aberta':
                raise ValidationError(
                    'Data de Conclusão cadastrada. Mude Status para "Concluída" ou deixe \
                     Data de Conclusão em branco.')


    # Certificar que não seja possível mudar o tipo de manutenção para 'Inicial',
    # pois o equipamento só pode ter uma manutenção inicial
    def validate_tipo_manutencao(self, field):
        # Caso a própria manutenção inicial não esteja sendo editada e o usuário
        # tentar mudar o tipo de manutenção para 'Inicial', não será validado.
        if field.data == 'Inicial' and \
                Manutencao.query.get(request.args.get('id')).tipo_manutencao != 'Inicial':
            raise ValidationError(
                'Este equipamento já possui manutenção inicial. Edite a exstente.')


# Criação de Unidade Responsável
class FormCriarUnidadeResponsavel(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])

    responsaveis = QuerySelectMultipleField('Responsáveis',
                                            query_factory=\
                                                lambda: Usuario.query.filter_by(responsavel_unidade=None).all(),
                                            validators=[InputRequired()])


    # Certificar que o nome é diferente dos já cadastrados
    def validate_nome(self, field):
        if UnidadeResponsavel.query.filter_by(nome=field.data).first():
            raise ValidationError('Unidade já cadastrada.')


# Edição de Unidade Responsável
class FormEditarUnidadeResponsavel(FormBase):
    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])

    responsaveis = QuerySelectMultipleField('Responsáveis',
                                            query_factory=\
                                                lambda: Usuario.query.all(),
                                            validators=[InputRequired()])

    unidades_consumidoras = QuerySelectMultipleField('Unidades Consumidoras',
                                            query_factory=\
                                                lambda: UnidadeConsumidora.query.all(),
                                            allow_blank=True)


    # Certificar que, se houve alteração no nome, o novo é diferente dos já cadastrados
    def validate_nome(self, field):
        if UnidadeResponsavel.query.filter_by(nome=field.data).first() and \
                field.data != UnidadeResponsavel.query.get(request.args.get('id')).nome:
            raise ValidationError('Unidade já cadastrada.')


# Criação de Unidade Consumidora
class FormCriarUnidadeConsumidora(FormBase):
    num_cliente = IntegerField('Número do Cliente',
                               validators=[InputRequired(),
                                           NumberRange(0)])

    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])

    unidade_responsavel = QuerySelectField('Unidade Responsável',
                                query_factory=lambda: 
                                    UnidadeResponsavel.query.order_by('nome').all(),
                                validators=[InputRequired()])

    endereco = StringField('Endereço', validators=[InputRequired(),
                                                   Length(1, 300)])

    localizacao = GeoJSONField('Localização', srid=-1, session=db.session,
                                geometry_type='POINT',
                                # Aumentar o mapa e centralizar em Fortaleza
                                render_kw={'data-width':400, 'data-height':400,
                                           'data-zoom':10,
                                           'data-lat':-3.7911773, 'data-lng':-38.5893123})

    mod_tarifaria = Select2Field('Modalidade Tarifária',
                            choices=[('Horária Verde', 'Horária Verde')],
                                     #('Convencional Monômia', 'Convencional Monômia')],
                            validators=[InputRequired()])

    num_medidores = IntegerField('Número dos Medidores',
                                 validators=[InputRequired(),
                                             NumberRange(0)])


    # Certificar que o número de cliente ainda não existe
    def validate_num_cliente(self, field):
        if UnidadeConsumidora.query.filter_by(num_cliente=field.data).first():
            raise ValidationError('Unidade já cadastrada.')


    # Certificar que o nome é diferente dos já cadastrados
    def validate_nome(self, field):
        if UnidadeConsumidora.query.filter_by(nome=field.data).first():
            raise ValidationError('Unidade já cadastrada.')


    # Certificar que o número de cliente ainda não existe
    def validate_num_medidores(self, field):
        if UnidadeConsumidora.query.filter_by(num_medidores=field.data).first():
            raise ValidationError('Número já cadastrado.')


# Edição de Unidade Consumidora
class FormEditarUnidadeConsumidora(FormBase):
    num_cliente = IntegerField('Número do Cliente',
                               validators=[InputRequired(),
                                           NumberRange(0)])

    nome = StringField('Nome', validators=[InputRequired(),
                                           Length(1, 64)])

    unidade_responsavel = QuerySelectField('Unidade Responsável',
                                query_factory=lambda: 
                                    UnidadeResponsavel.query.order_by('nome').all(),
                                validators=[InputRequired()])

    endereco = StringField('Endereço', validators=[InputRequired(),
                                                   Length(1, 300)])

    localizacao = GeoJSONField('Localização', srid=-1, session=db.session,
                                geometry_type='POINT',
                                # Aumentar o mapa e centralizar em Fortaleza
                                render_kw={'data-width':400, 'data-height':400,
                                           'data-zoom':10,
                                           'data-lat':-3.7911773, 'data-lng':-38.5893123})

    mod_tarifaria = Select2Field('Modalidade Tarifária',
                            choices=[('Horária Verde', 'Horária Verde')],
                                    #('Convencional Monômia', 'Convencional Monômia')],
                            validators=[InputRequired()])

    num_medidores = IntegerField('Número dos Medidores',
                                 validators=[InputRequired(),
                                             NumberRange(0)])


    hist_contas = QuerySelectMultipleField('Histórico de Contas',
                                            query_factory=\
                                                lambda: Conta.query.all(),
                                            allow_blank=True)


    # Certificar que, se houve alteração no número de cliente, o novo é diferente dos
    # já existentes
    def validate_num_cliente(self, field):
        if UnidadeConsumidora.query.filter_by(num_cliente=field.data).first() and \
                field.data != UnidadeConsumidora.query.get(request.args.get('id')).num_cliente:
            raise ValidationError('Unidade já cadastrada.')


    # Certificar que, se houve alteração no nome, o novo é diferente dos já cadastrados
    def validate_nome(self, field):
        if UnidadeConsumidora.query.filter_by(nome=field.data).first() and \
                field.data != UnidadeConsumidora.query.get(request.args.get('id')).nome:
            raise ValidationError('Unidade já cadastrada.')


    # Certificar que, se houve alteração no número dos medidores, o novo é diferente dos
    # já existentes
    def validate_num_medidores(self, field):
        if UnidadeConsumidora.query.filter_by(num_medidores=field.data).first() and \
                field.data != UnidadeConsumidora.query.get(request.args.get('id')).num_medidores:
            raise ValidationError('Número já cadastrado.')


# Criação de Conta de Energia
class FormCriarConta(FormBase):
    unidade_consumidora = QuerySelectField('Unidade Consumidora',
                                query_factory=lambda: 
                                    UnidadeConsumidora.query.order_by('nome').all(),
                                validators=[InputRequired()])

    data_leitura = DateField('Data da Leitura', widget=DatePickerWidget(),
                             render_kw={'data-date-format': 'DD.MM.YYYY'},
                             format='%d.%m.%Y',
                             validators=[InputRequired()])

    cons_fora_ponta = IntegerField('Consumo Fora de Ponta (kWh)',
                                   validators=[InputRequired(),
                                               NumberRange(0)])

    cons_hora_ponta = IntegerField('Consumo Hora Ponta (kWh)',
                                   validators=[InputRequired(),
                                               NumberRange(0)])

    valor_fora_ponta = DecimalField('Valor Fora de Ponta (R$)', use_locale=True,
                                    validators=[InputRequired(),
                                                NumberRange(0)])

    valor_hora_ponta = DecimalField('Valor Hora Ponta (R$)', use_locale=True,
                               validators=[InputRequired(),
                                           NumberRange(0)])

    valor_total = DecimalField('Valor Total (R$)', use_locale=True,
                               validators=[InputRequired(),
                                           NumberRange(0)])


    # Certificar que a data da leitura não seja no futuro
    def validate_data_leitura(self, field):
      if field.data > date.today():
        raise ValidationError('Não é possível cadastrar datas no futuro.')


# Edição de Conta de Energia
class FormEditarConta(FormBase):
    unidade_consumidora = QuerySelectField('Unidade Consumidora',
                                query_factory=lambda: 
                                    UnidadeConsumidora.query.order_by('nome').all(),
                                validators=[InputRequired()])

    data_leitura = DateField('Data da Leitura', widget=DatePickerWidget(),
                             render_kw={'data-date-format': 'DD.MM.YYYY'},
                             format='%d.%m.%Y',
                             validators=[InputRequired()])

    cons_fora_ponta = IntegerField('Consumo Fora de Ponta (kWh)',
                                   validators=[InputRequired(),
                                               NumberRange(0)])

    cons_hora_ponta = IntegerField('Consumo Hora Ponta (kWh)',
                                   validators=[InputRequired(),
                                               NumberRange(0)])

    valor_fora_ponta = DecimalField('Valor Fora de Ponta (R$)', use_locale=True,
                                    validators=[InputRequired(),
                                                NumberRange(0)])

    valor_hora_ponta = DecimalField('Valor Hora Ponta (R$)', use_locale=True,
                                    validators=[InputRequired(),
                                            NumberRange(0)])

    valor_total = DecimalField('Valor Total (R$)', use_locale=True,
                                validators=[InputRequired(),
                                            NumberRange(0)])



    # Certificar que a data da leitura não seja no futuro
    def validate_data_leitura(self, field):
      if field.data > date.today():
        raise ValidationError('Não é possível cadastrar datas no futuro.')