from Products.Five.browser import BrowserView
import logging
from plone import api
import urllib2
from zope.component import getUtility, queryUtility
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.utils import safe_unicode
from os import popen, system
from bs4 import BeautifulSoup

logger = logging.getLogger("cj.product.productimport")

class PorductImport(BrowserView):
    prefixString = "cj.product.cjconfiglet.ICjConfiglet"
    splitString = ":::"
    tmpDir = "/tmp"

    def __call__(self):
        portal = api.portal.get()
        registry = getUtility(IRegistry)
        connectId = registry.get("%s.%s" % (self.prefixString, "cjDataFeedConnectId"))
        connectPassword = registry.get("%s.%s" % (self.prefixString, "cjDataFeedConnectPassword"))
        dataFeedSetting = registry.get("%s.%s" % (self.prefixString, "cjDataFeedSetting"))
        for record in dataFeedSetting.split():
            advertiser, urlString = record.split(self.splitString)
            gzFileName = urlString.split("/")[-1]
            dataFileName = gzFileName.split(".gz")[0]
            wgetString = "http://%s:%s@%s" % (connectId, connectPassword, urlString)
            # wget, write to /tmp , read, del temp file, useing try-except.
            try:
                system("wget %s -O %s/%s" % (wgetString, self.tmpDir, gzFileName))
                system("gzip -d %s/%s" % (self.tmpDir, gzFileName))
                with open("%s/%s" % (self.tmpDir, dataFileName)) as fileName:
                    doc = fileName.read()
                # delete temp file
                system("rm %s/%s" % (self.tmpDir, dataFileName))
            except:
                logger.error('ERROR!!!, %s' % advertiser)
                continue

            soup = BeautifulSoup(doc, "xml")

            # in this loop, every product have same advertiser
            for product in soup.find_all("product"):
#                try:
                title = getattr(product.find("name"), "string", None)
                sku = getattr(product.find("sku"), "string", None)
                productName = getattr(product.find("name"), "string", None)
                if title is None or sku is None or productName is None:
                    continue
 #               id = "%s-%s" % (productName, sku)
 #               id = id.strip().replace(" ", "-")
                api.content.create(container=portal['product'],
                                   type='cj.product.cjproduct',
                                   title=safe_unicode(str(title)),
                                 #  id=id,
                                   programName=safe_unicode(str(getattr(product.find("programname"), "string", None))),
                                   programUrl=safe_unicode(str(getattr(product.find("programurl"), "string", None))),
                                   catalogName=safe_unicode(str(getattr(product.find("catalogName"), "string", None))),
#                                   lastUpdated=str(getattr(product.find("lastUpdated"), "string", None)),
                                   productName=safe_unicode(str(getattr(product.find("name"), "string", None))),
                                   keywords=safe_unicode(str(getattr(product.find("keywords"), "string", None))),
                                   description=safe_unicode(str(getattr(product.find("description"), "string", None))),
                                   sku=safe_unicode(str(getattr(product.find("sku"), "string", None))),
                                   manufacturer=safe_unicode(str(getattr(product.find("manufacturer"), "string", None))),
                                   manufacturerId=safe_unicode(str(getattr(product.find("manufacturerid"), "string", None))),
                                   upc=safe_unicode(str(getattr(product.find("upc"), "string", None))),
                                   isbn=safe_unicode(str(getattr(product.find("isbn"), "string", None))),
                                   currency=safe_unicode(str(getattr(product.find("currency"), "string", None))),
                                   salePrice=float(str(getattr(product.find("saleprice"), "string", None))),
                                   price=float(str(getattr(product.find("price"), "string", None))),
                                   retailPrice=float(str(getattr(product.find("retailprice"), "string", None))),
                                   fromPrice=safe_unicode(str(getattr(product.find("fromprice"), "string", None))),
                                   buyUrl=safe_unicode(str(getattr(product.find("buyurl"), "string", None))),
                                   impressionUrl=safe_unicode(str(getattr(product.find("impressionurl"), "string", None))),
                                   imageUrl=safe_unicode(str(getattr(product.find("imageurl"), "string", None))),
                                   advertiserCategory=safe_unicode(str(getattr(product.find("advertisercategory"), "string", None))),
                                   thirdPartyId=safe_unicode(str(getattr(product.find("thirdpartyid"), "string", None))),
                                   thirdPartyCategory=safe_unicode(str(getattr(product.find("thirdpartycategory"), "string", None))),
                                   publicationAuthor=safe_unicode(str(getattr(product.find("publicationauthor"), "string", None))),
                                   artist=safe_unicode(str(getattr(product.find("artist"), "string", None))),
                )
                break

                
                logger.info(":: %s: %s" %
                    (product.find("name").string,
                     product.find("buyurl").string,))
#                except:
#                    continue









