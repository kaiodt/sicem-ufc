# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Funções Auxiliares
################################################################################


########## Tratamento de Acentos ##########


acentos_minusculos = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
                     'â': 'a', 'ê': 'e', 'î': 'i', 'ô': 'o', 'û': 'u',
                     'ã': 'a', 'õ': 'o', 'ç': 'c'}
acentos_maiusculos = {'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
                      'Â': 'A', 'Ê': 'E', 'Î': 'I', 'Ô': 'O', 'Û': 'U',
                      'Ã': 'A', 'Õ': 'O', 'Ç': 'C'}
acentos_todos = dict(acentos_minusculos.items() + acentos_maiusculos.items())


def retirar_acentos(str, modo='todos'):
    if modo == 'minusculo':
        for acento in acentos_minusculos:
            if acento in str:
                str = str.replace(acento, acentos_minusculos[acento])
    elif modo == 'maiusculo':
        for acento in acentos_maiusculos:
            if acento in str:
                str = str.replace(acento, acentos_maiusculos[acento])
    elif modo == 'todos':
        for acento in acentos_todos:
            if acento in str:
                str = str.replace(acento, acentos_todos[acento])

    return str

    