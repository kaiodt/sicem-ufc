# coding: utf-8

################################################################################
## SICEM - UFC
################################################################################
## Campos para Fomulários do Painel de Administração
################################################################################


import datetime
from wtforms import DateField


########## Campos ##########


# Campo de data modificado para aceitar valores vazios
class DateFieldMod(DateField):
    def __init__(self, *args, **kwargs):
        super(DateFieldMod, self).__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        if valuelist:
            date_str = ' '.join(valuelist)
            try:
                self.data = datetime.datetime.strptime(date_str, self.format).date()
            except ValueError:
                self.data = None

                if date_str != u'':
                    raise ValueError(self.gettext('Not a valid date value'))

