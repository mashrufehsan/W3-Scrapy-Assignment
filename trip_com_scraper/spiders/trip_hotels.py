from datetime import datetime, timedelta
import random
import json
import scrapy
import re
from scrapy import Spider
from ..pipelines import HotelPipeline 

class TripHotelsSpider(Spider):
    name = "trip_hotels"
    start_urls = ["https://uk.trip.com/hotels/?locale=en-GB&curr=GBP"]

    def parse(self, response):
        data = response.body.decode("utf-8")
        city_ids = list(set(re.findall(r'"cityId":\s*(\d+)', data)))
        if city_ids:
            random_city_id = random.choice(city_ids)
            checkin_date = (datetime.now() + timedelta(days=1)).strftime('%Y/%m/%d')
            checkout_date = (datetime.now() + timedelta(days=2)).strftime('%Y/%m/%d')
            new_url = f"https://uk.trip.com/hotels/list?city={random_city_id}&checkin={checkin_date}&checkout={checkout_date}"
            print(f"New URL: {new_url}")
            yield scrapy.Request(url=new_url, callback=self.parse_hotel_list)
        else:
            print("No cityIds found in the response")

    def parse_hotel_list(self, response):
        html_content = response.body.decode('utf-8')
        start_index = html_content.find('"hotelList":')
        end_index = html_content.find('"firstPageRequest":')
        if start_index != -1 and end_index != -1:
            content_to_keep = html_content[start_index:end_index].rstrip(',')
            content_to_keep = '{' + content_to_keep
            data = json.loads(content_to_keep)
            pipeline = HotelPipeline()  # Create an instance of your pipeline
            pipeline.process_data(data)  # Proces
