#!/usr/bin/env python
# -*- coding: utf-8 -*-
import scrapy
from pip.utils import logging


class NjuskaloSpider(scrapy.Spider):
    name = 'njuskalo'
    start_urls = [
        'http://www.njuskalo.hr/auti'
        # 'http://www.njuskalo.hr/auti/dacia',
        # 'http://www.njuskalo.hr/auti/land-rover-range-rover',
        # 'http://www.njuskalo.hr/auti/toyota',

        # 'http://www.njuskalo.hr/auti/santana'
    ]

    def __init(self):
        self.pagenum = 1
        self.LOG_LEVEL = logging.INFO
    
    def parse(self, response):
        # print("Existing settings: %s" % self.settings.attributes.keys())
        # print("Existing settings: %s" % self.settings.attributes.values())
        yield scrapy.Request(response.url, self.parse_category)

    def parse_category(self,response):

        categoriesList=response.css('#form_browse_detailed_search-categories-block .topcat-item .link::attr(href)')

        if categoriesList:
            for href in categoriesList:
                category_url = response.urljoin(href.extract())
                print("category found: " + category_url)

                yield scrapy.Request(category_url, self.parse_category)
        else:
            self.pagenum = 1
            url=response.url+"?page=" + (str)(self.pagenum)
            print('paging start: ' +url)

            yield scrapy.Request(url, self.parse_page)

    def parse_page(self, response):
        for href in response.css(".js-EntityList-item--Regular .entity-title .link::attr(href)"):
            oglas_url = response.urljoin(href.extract())             
            yield scrapy.Request(oglas_url, self.parse_oglas)
            
        #print '******************************************************************'
        
        
        next_page_button = response.css(".Pagination-item--next .Pagination-link::text")

        if next_page_button:


            print("next page exists after " + response.url)

            url = response.url

            baseUrl = url[:url.index("?page=")]
            pageNo= url[url.index("?page=")+6:]
            pageNo=int(pageNo)+1
            nextUrl=baseUrl + "?page=" + pageNo

            print("next page: " + nextUrl)

            yield scrapy.Request(nextUrl, self.parse_page)

        else:
            print("last page " + response.url)


            
        
        
         

    def parse_oglas(self, response):        

        result = {
            'cijena': int(response.css('.price--hrk::text').extract()[0].strip().replace('.','')),
            'id': response.css('.base-entity-id::text').extract()[0].strip(),

        }

        dataHeaders = response.css('tr th::text').extract()

        dataHeaders = [ x.replace(':','') for x in dataHeaders ]

        #datavalues=response.css('tr td::text').extract()

        for header in dataHeaders:
            try:
                row = dataHeaders.index(header)                
                data = response.css('tr:nth-child(' + (str)(row + 1) + ') td::text').extract()

                if not data: #years are (int) in an attribute
                    # data = response.css('tr:nth-child(' + `row + 1` + ') time::text').extract()[0]
                    data = response.css('tr:nth-child(' + (str)(row + 1) + ') time::attr(datetime)').extract()[0]
                else:
                    data = data[0]
                data=data.strip()

                if data.isdigit():
                    data=int(data)

                result[header] = data
                
            except:
                result[header] = ""
        
        #print result
        yield result        