# -*- coding: utf-8 -*-
from Products.Five.browser import BrowserView
import logging
from plone import api
import urllib2
from zope.component import getUtility, queryUtility
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.utils import safe_unicode
from os import popen, system
from bs4 import BeautifulSoup
from datetime import datetime
from naiveBayesClassifier import tokenizer
from naiveBayesClassifier.trainer import Trainer
from naiveBayesClassifier.classifier import Classifier
from ..config import TRAINING_SET as trainingSet
from plone.namedfile import NamedBlobImage
#以下4個import，做關聯用
from zope.app.intid.interfaces import IIntIds
from z3c.relationfield import RelationValue
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
#以上4個import，做關聯用

from ..tfidf import run as tfIdf

logger = logging.getLogger("cj.product.productimport")


class PorductImport(BrowserView):
    prefixString = "cj.product.cjconfiglet.ICjConfiglet"
    splitString = ":::"
    tmpDir = "/tmp"

    trainer = Trainer(tokenizer)
    for record in trainingSet:
        trainer.train(record['text'], record['category'])
    classifier = Classifier(trainer.data, tokenizer)

    def __call__(self):
        request = self.request
        portal = api.portal.get()
        catalog = api.portal.get_tool(name='portal_catalog')
        intIds = getUtility(IIntIds)
        registry = getUtility(IRegistry)
        connectId = registry.get("%s.%s" % (self.prefixString, "cjDataFeedConnectId"))
        connectPassword = registry.get("%s.%s" % (self.prefixString, "cjDataFeedConnectPassword"))
        dataFeedSetting = registry.get("%s.%s" % (self.prefixString, "cjDataFeedSetting"))

        # get one record for each operator
        record = dataFeedSetting.split("\r\n")[int(request["record"])]
        advertiser, urlString = record.split(self.splitString)

        advertiserObject = catalog({"portal_type":"mingtak.advertiser.advertiser", "id":advertiser.lower()})[0].getObject()
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
            return

        soup = BeautifulSoup(doc, "xml")

        # in this loop, every product have same advertiser
        count = 0
        for product in soup.find_all("product"):
            title = getattr(product.find("name"), "string", None)
            sku = getattr(product.find("sku"), "string", None)
            if title is None or sku is None:
                continue
            recordCount = len(catalog({"portal_type":"cj.product.cjproduct",
                                       "programName":safe_unicode(str(getattr(product.find("programname"), "string", advertiser))),
                                       "title":title,
                                       "sku":sku}))
            if recordCount > 0:
                continue
            #Import 1000 record at one time， to avoid out of memory
            count += 1
            if count > 200:
                return
            try:
                year, month, day = str(getattr(product.find("lastupdated"), "string", "")).split()[0].split("-")[0:3]
                hour, minute = str(getattr(product.find("lastupdated"), "string", "")).split()[1].split(":")[0:2]
#                descriptionString = safe_unicode(str(getattr(product.find("description"), "string", "")))
                descriptionString = safe_unicode(getattr(product.find("description"), "string", ""))
                productClassification = self.classifier.classify(descriptionString)
                subjectList, bayesPair = [], []
                for subject in productClassification:
                    # bayes value
                    if subject[1] > 0:
                        if bayesPair == []:
                            bayesPair = subject
                        elif subject[1] > bayesPair[1]:
                            bayesPair = subject
                if bayesPair == []:
                    subjectList = ["Other"]
                else:
                    subjectList.append(bayesPair[0])
                logger.info(productClassification)

                #get product image
                imageUrl = safe_unicode(str(getattr(product.find("imageurl"), "string", "")))
                imageFileName = safe_unicode(imageUrl.split('/')[-1])
                system("wget %s -O %s/%s" % (imageUrl, self.tmpDir, imageFileName))
                with open('%s/%s' % (self.tmpDir, imageFileName)) as tmpImage:
                    productImage = tmpImage.read()
                # delete temp file
                system("rm %s/%s" % (self.tmpDir, imageFileName))

                # try more the
                tf_idf_result = tfIdf(descriptionString.encode('utf-8'))

                for result in tf_idf_result[0:7]:
                    if len(result[0]) > 5:
                        subjectList.append(result[0])

                object = api.content.create(
                             container=portal['product'],
                             type='cj.product.cjproduct',
                             title=safe_unicode(str(title)),
                             subject=subjectList,
                             advertiser=[RelationValue(intIds.getId(advertiserObject))],
                             programName=safe_unicode(str(getattr(product.find("programname"), "string", advertiser))),
                             programUrl=safe_unicode(str(getattr(product.find("programurl"), "string", ""))),
                             catalogName=safe_unicode(str(getattr(product.find("catalogName"), "string", ""))),
                             lastUpdated=datetime(int(year), int(month), int(day), int(hour), int(minute)),
                             productName=safe_unicode(str(getattr(product.find("name"), "string", ""))),
                             keywords=safe_unicode(str(getattr(product.find("keywords"), "string", ""))),
#                             description=safe_unicode(str(getattr(product.find("description"), "string", ""))),
                             description=descriptionString.encode('utf-8'),
                             sku=safe_unicode(str(getattr(product.find("sku"), "string", ""))),
                             manufacturer=safe_unicode(str(getattr(product.find("manufacturer"), "string", ""))),
                             manufacturerId=safe_unicode(str(getattr(product.find("manufacturerid"), "string", ""))),
                             upc=safe_unicode(str(getattr(product.find("upc"), "string", ""))),
                             isbn=safe_unicode(str(getattr(product.find("isbn"), "string", ""))),
                             currency=safe_unicode(str(getattr(product.find("currency"), "string", "USD"))),
                             salePrice=float(str(getattr(product.find("saleprice"), "string", "0.0"))),
                             price=float(str(getattr(product.find("price"), "string", "0.0"))),
                             retailPrice=float(str(getattr(product.find("retailprice"), "string", "0.0"))),
                             fromPrice=safe_unicode(str(getattr(product.find("fromprice"), "string", ""))),
                             buyUrl=safe_unicode(str(getattr(product.find("buyurl"), "string", ""))),
                             impressionUrl=safe_unicode(str(getattr(product.find("impressionurl"), "string", ""))),
                             imageUrl=imageUrl,
                             advertiserCategory=safe_unicode(str(getattr(product.find("advertisercategory"), "string", ""))),
                             thirdPartyId=safe_unicode(str(getattr(product.find("thirdpartyid"), "string", ""))),
                             thirdPartyCategory=safe_unicode(str(getattr(product.find("thirdpartycategory"), "string", ""))),
                             publicationAuthor=safe_unicode(str(getattr(product.find("publicationauthor"), "string", ""))),
                             artist=safe_unicode(str(getattr(product.find("artist"), "string", ""))),
                             publicationTitle=safe_unicode(str(getattr(product.find("publicationtitle"), "string", ""))),
                             publisher=safe_unicode(str(getattr(product.find("publisher"), "string", ""))),
                             label=safe_unicode(str(getattr(product.find("label"), "string", ""))),
                             format=safe_unicode(str(getattr(product.find("format"), "string", ""))),
                             special=safe_unicode(str(getattr(product.find("special"), "string", ""))),
                             gift=safe_unicode(str(getattr(product.find("gift"), "string", ""))),
                             promotionalText=safe_unicode(str(getattr(product.find("promotionaltext"), "string", ""))),
                             offLine=safe_unicode(str(getattr(product.find("offline"), "string", ""))),
                             onLine=safe_unicode(str(getattr(product.find("online"), "string", ""))),
                             inStock=safe_unicode(str(getattr(product.find("instock"), "string", ""))),
                             condition=safe_unicode(str(getattr(product.find("condition"), "string", ""))),
                             warranty=safe_unicode(str(getattr(product.find("warranty"), "string", ""))),
                             standardShippingCost=float(str(getattr(product.find("standardshippingcost"), "string", "0.0"))),
                             productImage = NamedBlobImage(data=productImage, filename=imageFileName),
                         )
                api.content.transition(obj=object, transition='publish')
                object.exclude_from_nav = True
                object.reindexObject()
            except:
                logger.error('error position 1')
                continue
            #目前尚未處理startDate, endDate (對應catalog index的 start, end),原因：找不到sample
            #以及，advertiser的反向關連尚未確認正確性，如不正確，要使用notify處理(見getnewrelation...)！
            #還有，新增處理了，但更新沒處理到！
            logger.info("||| %s ||| %s ||| %s" %
                (count,
                 product.find("name").string,
                 product.find("buyurl").string,))
