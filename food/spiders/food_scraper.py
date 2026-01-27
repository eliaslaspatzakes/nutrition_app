import scrapy
import re

class FoodScraperSpider(scrapy.Spider):
    name = "food_scraper"
    allowed_domains = ["www.nutritionvalue.org"]
    
    start_urls = [
        "https://www.nutritionvalue.org/foods_in_Fast_Foods_page_1.html",
        "https://www.nutritionvalue.org/foods_in_Vegetables_and_Vegetable_Products_page_1.html",
        "https://www.nutritionvalue.org/foods_in_Fruits_and_Fruit_Juices_page_1.html",
        "https://www.nutritionvalue.org/foods_in_Beef_Products_page_1.html",
        "https://www.nutritionvalue.org/foods_in_Legumes_and_Legume_Products_page_1.html"
    ]
    
    custom_settings = {
        'FEED_EXPORT_ENCODING': 'utf-8',
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 16,
    }

    def start_requests(self):
        
        for url in self.start_urls:
            yield scrapy.Request(
                url=url, 
                callback=self.parse, 
                headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' 
                    }
                
            )
    def parse(self, response):
        
        table = response.xpath("//table[contains(@class, 'results')]")
   
        rows = table.xpath(".//tr[position()>1]")
        
        for row in rows:
            
            name = row.xpath(".//td[1]/a/text()").get()
            link = row.xpath(".//td[1]/a/@href").get()
            
           
            if link:
                yield response.follow(
                    url=link,
                    callback=self.parse_food,
                    cb_kwargs={'food_name': name},
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' 
                    }
                
                )
        
        next_page = response.xpath("//a[text()='Next']/@href").get()
        if next_page:
            yield response.follow(url=next_page, callback=self.parse)
            



    def clean_value(self, value):
        
        if not value:
            return None
        value = str(value).strip()
        value = value.replace('\xa0', ' ')
        match = re.search(r'[\d\.]+', value)
        
        if match:
            return float(match.group())
        else:
            return None
        
        
    def parse_food(self, response, food_name):
        def get_nutrient(label):
            return response.xpath(f"//tr[td[1]//text()[contains(., '{label}')]]/td[@class='right']/text()").get()

        yield {
            'Name': food_name,
           
            'Calories': self.clean_value(response.xpath('//td[@id="calories"]/text()').get()),
            
            'Fat':           self.clean_value(get_nutrient('Fat')),
            'Carbohydrate':  self.clean_value(get_nutrient('Carbohydrate')),
            'Protein':       self.clean_value(get_nutrient('Protein')),
            'Sugars':        self.clean_value(get_nutrient('Sugars')),
            'Fiber':         self.clean_value(get_nutrient('Fiber')),
            'Sodium':        self.clean_value(get_nutrient('Sodium')),
            'Saturated_Fat': self.clean_value(get_nutrient('Saturated fatty acids')),
            'Cholesterol':   self.clean_value(get_nutrient('Cholesterol')),
            'Water':         self.clean_value(get_nutrient('Water')),
        }