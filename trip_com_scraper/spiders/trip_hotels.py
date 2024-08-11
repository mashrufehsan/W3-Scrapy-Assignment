import scrapy
import re
import random
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, TEXT, inspect
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.types import TypeDecorator
import requests
import os
import pickle

# Define a custom type for storing lists of strings
class PickleType(TypeDecorator):
    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is not None:
            return pickle.dumps(value)
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            return pickle.loads(value)
        return None

# Define the PostgreSQL database URL
DATABASE_URL = 'postgresql://postgres:admin@localhost/scrapy_hotels'

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a base class for our class definitions
Base = declarative_base()

class TripHotelsSpider(scrapy.Spider):
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
            self.process_data(data)
        else:
            print('"hotelList" or "firstPageRequest" not found in the content')

    def process_data(self, data):
        city_name = data['hotelList'][0]['positionInfo']['cityName']
        city_name = city_name.replace(" ", "_").replace("-", "_").lower()  # Sanitize and convert to lowercase

        # Define the Hotel class dynamically
        class Hotel(Base):
            __tablename__ = city_name  # Set the table name dynamically and in lowercase
            
            id = Column(Integer, primary_key=True, autoincrement=True)
            title = Column(String(100), nullable=False)
            rating = Column(Float, nullable=False)
            location = Column(String(100), nullable=False)
            latitude = Column(Float, nullable=False)
            longitude = Column(Float, nullable=False)
            room_type = Column(String(100), nullable=False)
            discount_price = Column(Float, nullable=True)  # Discount price can be null
            base_price = Column(Float, nullable=True)  # Base price can be null
            images = Column(String, nullable=True)  # Path to the image file
            
            def __repr__(self):
                return (f"<Hotel(title={self.title}, rating={self.rating}, "
                        f"location={self.location}, latitude={self.latitude}, "
                        f"longitude={self.longitude}, room_type={self.room_type}, "
                        f"base_price={self.base_price}, discount_price={self.discount_price}, "
                        f"images={self.images})>")

        # Check if the table exists
        inspector = inspect(engine)
        if city_name in inspector.get_table_names():
            print(f"Table '{city_name}' already exists.")
        else:
            # Create the table in the database
            Base.metadata.create_all(engine)
            print(f"Table '{city_name}' created.")

        Session = sessionmaker(bind=engine)
        session = Session()

        # Ensure the images directory exists
        if not os.path.exists('images'):
            os.makedirs('images')

        # Iterate through each hotel and insert data into the table
        for hotel in data['hotelList']:
            hotel_info = hotel['hotelBasicInfo']
            position_info = hotel['positionInfo']
            room_info = hotel['roomInfo']

            hotel_title = hotel_info['hotelName']
            hotel_rating = float(hotel['commentInfo']['commentScore']) if hotel['commentInfo']['commentScore'] else None
            hotel_address = hotel_info['hotelAddress']
            latitude = float(position_info['mapCoordinate'][0]['latitude'])
            longitude = float(position_info['mapCoordinate'][0]['longitude'])
            physical_room_name = room_info['physicalRoomName']
            price = hotel_info['price']
            origin_price = hotel_info['originPrice']
            hotel_img = hotel_info['hotelImg']

            # Convert empty strings to None
            base_price = float(origin_price) if origin_price not in [None, ''] else None
            discount_price = float(price) if price not in [None, ''] else None

            # Download the image and save it to the images folder
            image_path = None
            if hotel_img:
                try:
                    image_response = requests.get(hotel_img)
                    if image_response.status_code == 200:
                        # Define the image file path
                        image_filename = f"{hotel_title.replace(' ', '_').replace('-', '_').lower()}.jpg"
                        image_path = os.path.join('images', image_filename)
                        # Save the image
                        with open(image_path, 'wb') as img_file:
                            img_file.write(image_response.content)
                except Exception as e:
                    print(f"Failed to fetch or save image from {hotel_img}. Error: {e}")

            # Create new hotel instance
            new_hotel = Hotel(
                title=hotel_title,
                rating=hotel_rating,
                location=hotel_address,
                latitude=latitude,
                longitude=longitude,
                room_type=physical_room_name,
                discount_price=discount_price,
                base_price=base_price,
                images=image_path  # Save the image path in the database
            )
            
            # Add the new hotel to the session
            session.add(new_hotel)

        # Commit the session to save changes to the database
        session.commit()
        print("Data inserted successfully.")

        # Close the session
        session.close()
