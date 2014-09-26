from five import grok

from z3c.form import group, field
from zope import schema
from zope.interface import invariant, Invalid
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from plone.dexterity.content import Container
from plone.directives import dexterity, form
from plone.app.textfield import RichText
from plone.namedfile.field import NamedImage, NamedFile
from plone.namedfile.field import NamedBlobImage, NamedBlobFile
from plone.namedfile.interfaces import IImageScaleTraversable

from z3c.relationfield.schema import RelationList, RelationChoice
from plone.formwidget.contenttree import ObjPathSourceBinder


from cj.product import MessageFactory as _


# Interface class; used to define content-type schema.

class ICjConfiglet(form.Schema, IImageScaleTraversable):
    """
    Configlet for cj.com
    """
    cjDataFeedConnectId = schema.TextLine(
        title=_(u"Cj.com data feed connect id"),
        required=False,
    )

    cjDataFeedConnectPassword = schema.TextLine(
        title=_(u"Cj.com data feed connect password"),
        required=False,
    )

    cjDataFeedSetting = schema.Text(
        title=_(u"Cj.com data feed setting"),
        description=_(u"Cj.com product data feed setting, format: 'description of advertiser':::'cj-http full url, Does Not include http://', per line one record."),
        required=False,
    )


class CjConfiglet(Container):
    grok.implements(ICjConfiglet)


class SampleView(grok.View):
    """ sample view class """

    grok.context(ICjConfiglet)
    grok.require('zope2.View')
    grok.name('view')
