# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import FormRequest

class AmpligraphSpider(scrapy.Spider):
    name = 'ampligraph'
    download_delay = 1.0
    allowed_domains = ['github.com']
    start_urls = [
        #'https://github.com/Accenture/AmpliGraph/stargazers'
        'https://github.com/login'
    ]
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, headers={'Referer':url})
            
    def parse(self, response):
        page_name = response.url.split("/")[-1]
        self.log(f'Loaded {page_name}')

        # https://python.gotrained.com/scrapy-formrequest-logging-in/
        #token = response.xpath('//*[@name="authenticity_token"]/@value').extract_first()
        yield FormRequest.from_response(
            response,
            url='https://github.com/session',
            method="POST",
            formdata={'password' :'XXXXXXXXXXXXX', 'login':'XXXXXXXXXXXXX'},
            callback=self.scrape_pages
        )

    def scrape_pages(self, response):
        page_name = response.url.split("/")[-1]
        self.log(f'Loaded {page_name}')

        if page_name == '':
            yield scrapy.Request(url='https://github.com/Accenture/AmpliGraph/stargazers', callback=self.scrape_pages)

        if page_name.startswith('stargazers'):
            # Follow users
            users = list(map(lambda x: x.attrib['href'] , response.xpath('//a[contains(@data-hovercard-type, "user")]')))
            for user in users:
                yield response.follow(f'https://github.com{user}', self.scrape_pages)

            # Follow next page
            next_page = response.css('.paginate-container').xpath("//a[contains(., 'Next')]")
            if len(next_page) > 0:
                yield response.follow(next_page[0].attrib['href'], self.scrape_pages)            
                
        else:
            # Extract data for the current user page 
            attrs = {'name': response.css('title::text').get()}
            for attr in ['homeLocation', 'email', 'worksFor', 'url']:
                attrs[attr] = ''.join(set(response.xpath(f'//li[contains(@itemprop, "{attr}")]//text()').extract())).strip()
            yield attrs