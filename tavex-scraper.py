import time
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
from pymongo import MongoClient

def scrape_and_store_tavex_data():
    start_url = 'https://tavex.dk/guldpriser-og-solvpriser/?tab=Guld#:~:text=Hvad%20er%20investeringsguld%3F'
    mongo_uri = 'mongodb://user:password@localhost:27017/'
    database_name = 'db'
    collection_name = 'products'

    async def scrape_products(page_url):
        async with aiohttp.ClientSession() as session:
            async with session.get(page_url) as response:
                html_content = await response.text()

        soup = BeautifulSoup(html_content, 'html.parser')

        products = []
        product_elements = soup.select('.js-filter-search-row')
        for product_element in product_elements:
            name_element = product_element.select_one('.accordion__title-item--name > span')
            title = name_element.text.strip().split('\n')[0] if name_element else ''

            buy_price_element = product_element.select_one('.accordion__title-item--price:nth-child(3) .price-amount-whole')
            buy_price_fraction = product_element.select_one('.accordion__title-item--price:nth-child(3) .price-amount-fraction')
            buy_price = f'{buy_price_element.text.strip().replace(" ", "")},{buy_price_fraction.text.strip()}' if buy_price_element and buy_price_fraction else 'N/A'

            sell_price_element = product_element.select_one('.accordion__title-item--price:nth-child(4) .accordion__title-item-value.js-accordion-item-total-value-combined')
            sell_price = sell_price_element.text.strip() if sell_price_element else 'N/A'

            if title:
                products.append({
                    'title': title,
                    'buy_price': buy_price,
                    'sell_price': sell_price
                })

        return products

    async def main():
        start_time = time.time()

        product_data = await scrape_products(start_url)

        end_time = time.time()
        execution_time = end_time - start_time
        print(execution_time)

        output_data = {
            'execution_time': execution_time,
            'products': product_data
        }

        return output_data


    def write_to_mongodb(data):
        client = MongoClient(mongo_uri)
        db = client[database_name]
        collection = db[collection_name]
        collection.insert_one(data)  # Insert a single document
        client.close()


    async def run_scraper():
        data = await main()
        write_to_mongodb(data)

    # Run the scraper
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_scraper())

scrape_and_store_tavex_data()