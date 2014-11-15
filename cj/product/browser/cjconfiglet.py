from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper

#from oauth2login import IOauth2Setting
#from cj.product.cjconfiglet import ICjConfiglet
from ..cjconfiglet import ICjConfiglet
from plone.z3cform import layout
from z3c.form import form

class CjControlPanelForm(RegistryEditForm):
    form.extends(RegistryEditForm)
    schema = ICjConfiglet

CjControlPanelView = layout.wrap_form(CjControlPanelForm, ControlPanelFormWrapper)
CjControlPanelView.label = u"Cj product datafeed setting"
