import scrapy
# from ICP_UAE.items import Product
from lxml import html

class Icp_uaeSpider(scrapy.Spider):
    name = "ICP_UAE"
    start_urls = ["https://example.com"]

    def parse(self, response):
        parser = html.fromstring(response.text)
        print("Visited:", response.url)
