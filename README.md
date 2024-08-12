# Trip Hotels Scraper
This project is a web scraper for extracting hotel information from the Trip.com website. It uses Scrapy to crawl hotel data, SQLAlchemy to interact with a PostgreSQL database, and requests to download hotel images.

## Setup Instructions

1. **Clone the repository:**
    ```bash
    git clone https://github.com/mashrufehsan/W3-Scrapy-Assignment.git
    cd W3-Scrapy-Assignment
    ```

2. **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Set up the database:**
    Create a PostgreSQL database for storing the scraped data. You can do this using the psql command-line tool or a PostgreSQL client.
    ```bash
    CREATE DATABASE scrapy_hotels;
    ```

5. **Configure environment variables:**

    Copy the .env.sample file to .env and fill in the required configuration:
    ```bash
    cp .env.sample .env
    ```
    Update the `.env` file with your PostgreSQL database credentials:

6. **Run the application:**
    ```bash
    cd trip_com_scraper
    scrapy crawl trip_hotels
    ```

## Notes

- Ensure PostgreSQL is running and accessible with the credentials provided in the .env file.
- Images will be saved in the images/ directory with filenames based on hotel names.
- The Scrapy spider will create tables dynamically based on the city names.
