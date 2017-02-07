# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import json
import time    
import pymongo

from datetime import datetime
from elasticsearch import Elasticsearch, helpers
from six import string_types

import logging
import hashlib
import types


class NjuskaloPipeline(object):
    def process_item(self, item, spider):
        return item




class JsonWriterPipeline(object):

    def __init__(self):
        filename=time.strftime('results/%Y-%m-%d %H%M%S')+".js"
        self.file = open(filename, 'wb')

    def process_item(self, item, spider):
        line = json.dumps(dict(item)) + "\n"
        self.file.write(line)
        return item



class MongoPipeline(object):

    collection_name = 'njuskalo_full'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            # mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_uri='localhost',
            # mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
            mongo_db='njuskalo'
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db[self.collection_name].insert(dict(item))
        return item



class ElasticSearchPipeline(object):
    settings = None
    es = None
    items_buffer = []

    @classmethod
    def validate_settings(cls, settings):
        def validate_setting(setting_key):
            if settings[setting_key] is None:
                raise InvalidSettingsException('%s is not defined in settings.py' % setting_key)

        required_settings = {'ELASTICSEARCH_INDEX', 'ELASTICSEARCH_TYPE'}

        for required_setting in required_settings:
            validate_setting(required_setting)

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls()
        ext.settings = crawler.settings

        cls.validate_settings(ext.settings)

        es_servers = ext.settings.get('ELASTICSEARCH_SERVERS', 'localhost:9200')
        es_servers = es_servers if isinstance(es_servers, list) else [es_servers]

        authType = ext.settings['ELASTICSEARCH_AUTH']

        if authType == 'NTLM':
            from .transportNTLM import TransportNTLM
            ext.es = Elasticsearch(hosts=es_servers,
                                   transport_class=TransportNTLM,
                                   ntlm_user= ext.settings['ELASTICSEARCH_USERNAME'],
                                   ntlm_pass= ext.settings['ELASTICSEARCH_PASSWORD'],
                                   timeout=ext.settings.get('ELASTICSEARCH_TIMEOUT',60))
        else :
            ext.es = Elasticsearch(hosts=es_servers, timeout=ext.settings.get('ELASTICSEARCH_TIMEOUT', 60))
        return ext

    def get_unique_key(self, unique_key):
        if isinstance(unique_key, list):
            unique_key = unique_key[0].encode('utf-8')
        elif isinstance(unique_key, string_types):
            unique_key = unique_key.encode('utf-8')
        else:
            raise Exception('unique key must be str or unicode')

        return unique_key

    def index_item(self, item):

        index_name = self.settings['ELASTICSEARCH_INDEX']
        index_suffix_format = self.settings.get('ELASTICSEARCH_INDEX_DATE_FORMAT', None)
        index_suffix_key = self.settings.get('ELASTICSEARCH_INDEX_DATE_KEY', None)
        index_suffix_key_format = self.settings.get('ELASTICSEARCH_INDEX_DATE_KEY_FORMAT', None)

        if index_suffix_format:
            if index_suffix_key and index_suffix_key_format:
                dt = datetime.strptime(item[index_suffix_key], index_suffix_key_format)
            else:
                dt = datetime.now()
            index_name += "-" + datetime.strftime(dt,index_suffix_format)
        elif index_suffix_key:
            index_name += "-" + index_suffix_key

        index_action = {
            '_index': index_name,
            '_type': self.settings['ELASTICSEARCH_TYPE'],
            '_source': dict(item)
        }

        if self.settings['ELASTICSEARCH_UNIQ_KEY'] is not None:
            item_unique_key = item[self.settings['ELASTICSEARCH_UNIQ_KEY']]
            unique_key = self.get_unique_key(item_unique_key)
            item_id = hashlib.sha1(unique_key).hexdigest()
            index_action['_id'] = item_id
            logging.debug('Generated unique key %s' % item_id)

        self.items_buffer.append(index_action)

        if len(self.items_buffer) >= self.settings.get('ELASTICSEARCH_BUFFER_LENGTH', 500):
            self.send_items()
            self.items_buffer = []

    def send_items(self):
        helpers.bulk(self.es, self.items_buffer)

    def process_item(self, item, spider):
        if isinstance(item, types.GeneratorType) or isinstance(item, list):
            for each in item:
                self.process_item(each, spider)
        else:
            self.index_item(item)
            logging.debug('Item sent to Elastic Search %s' % self.settings['ELASTICSEARCH_INDEX'])
            return item

    def close_spider(self, spider):
        if len(self.items_buffer):
            self.send_items()