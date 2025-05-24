import scrapy

class Product(scrapy.Item):
    customer_name = scrapy.Field()
    nationality = scrapy.Field()
    emirates_id = scrapy.Field()
    date_of_birth = scrapy.Field() 
    pdf_data = scrapy.Field()


# data = {
#                     'customer_name': name,
#                     'nationality': nationality,
#                     'emirates_id': emirates_id,
#                     'date_of_birth': date_of_birth,
#                     'pdf_data': base64.b64decode(base64_string)
                    
#                 }