from Products.Five.browser import BrowserView
import logging
from plone import api
import urllib2
from zope.component import getUtility, queryUtility
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.utils import safe_unicode
from os import popen, system

logger = logging.getLogger("cj.product.productimport")

class PorductImport(BrowserView):
    prefixString = "cj.product.cjconfiglet.ICjConfiglet"
    splitString = ":::"

    def __call__(self):
        registry = getUtility(IRegistry)
        connectId = registry.get("%s.%s" % (self.prefixString, "cjDataFeedConnectId"))
        connectPassword = registry.get("%s.%s" % (self.prefixString, "cjDataFeedConnectPassword"))
        dataFeedSetting = registry.get("%s.%s" % (self.prefixString, "cjDataFeedSetting"))
        for record in dataFeedSetting.split('\n'):
            urlString = record.split(self.splitString)[1]
            gzFileName = urlString.split("/")[-1]
            dataFileName = gzFileName.split(".gz")[0]
            wgetString = "http://%s:%s@%s" % (connectId, connectPassword, urlString)





            logger.info("\n%s\n%s\n%s\n%s\n\n" % (urlString, gzFileName, dataFileName, wgetString))











