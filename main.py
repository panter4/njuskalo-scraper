
#import scrapy
from scrapy.crawler import CrawlerProcess
from spiders.njuskalo import NjuskaloSpider


from scrapy.utils.project import get_project_settings

import settings

if __name__ == "__main__":
#    spider = NjuskaloSpider()    
#    spider.parse('http://www.njuskalo.hr/auti/toyota')
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        # 'ITEM_PIPELINES': ['pipelines.JsonWriterPipeline']
        # 'ITEM_PIPELINES': ['pipelines.MongoPipeline']
        'ITEM_PIPELINES': {'scrapyelasticsearch.scrapyelasticsearch.ElasticSearchPipeline':500},

        # 'ITEM_PIPELINES' : {'scrapyelasticsearch.scrapyelasticsearch.ElasticSearchPipeline',},
        # 'ELASTICSEARCH_SERVERS' : ['https://elastic:7S3PKgfesSvGC9t6uT3Z8WmR@3e6cd9ae150c3d1f6f5a8a246a8a0a91.eu-west-1.aws.found.io:9243'],
        'ELASTICSEARCH_SERVERS' : ['search-panter4-p7ocqhgdiixspehfm6hmdseypy.eu-central-1.es.amazonaws.com:80'],
        'ELASTICSEARCH_INDEX' : 'njuskalo',
        # 'ELASTICSEARCH_INDEX_DATE_FORMAT' : '%Y-%m',
        'ELASTICSEARCH_TYPE' : 'items',
        'ELASTICSEARCH_UNIQ_KEY' : 'id'  # Custom uniqe key,

    })




    process.crawl(NjuskaloSpider)
    process.start()
    
    print "done"
    
    
