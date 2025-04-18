from bs4 import BeautifulSoup
from urllib.parse import quote
from playwright.sync_api import sync_playwright
import re
from .currency_converter import CurrencyConverter

class BandcampSearch:
    def __init__(self):
        pass
        
    def get_page_html(self, url: str) -> str:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=0)
            page.wait_for_timeout(500)
            html = page.content()
            browser.close()
        return html


    def search_song(self, track_name: str, artist_name: str) -> dict:
        query = f'{track_name} {artist_name}'
        search_url = f'https://bandcamp.com/search?q={quote(query)}&item_type=t'

        html = self.get_page_html(search_url)
        soup = BeautifulSoup(html, 'html.parser')

        result_row = soup.find('li', class_=lambda c: c and 'searchresult' in c)

        track_url = ''
        price = -1

        if result_row:
            anchor = result_row.select_one('.heading a')
            if anchor and anchor.has_attr('href'):
                track_url = anchor['href']
                # print(f'Track URL for {track_name}: {track_url}')

                track_html = self.get_page_html(track_url)
                track_soup = BeautifulSoup(track_html, 'html.parser')

                nyp_span = track_soup.find('span', string=lambda text: text and 'name your price' in text.lower())
                if nyp_span:
                    price = 'Free'

                else:
                    buy_item = track_soup.select_one('li.buyItem:has(h4:contains("Buy Digital Track"))')
                    if buy_item:
                        price_span = buy_item.select_one('span.base-text-color')

                        price_text = price_span.get_text(strip=True)
                        print(f'Raw price text: {price_text}')

                        # Extract currency symbol and amount
                        match = re.match(r'([^\d]+)?([\d.]+)', price_text)
                        if match:
                            symbol = match.group(1).strip() if match.group(1) else '$'
                            amount = float(match.group(2))

                            # Currency symbol to code mapping
                            currency_map = {
                                    '€': 'EUR',
                                    '£': 'GBP',
                                    '$': 'USD',
                                    '¥': 'JPY',
                            }

                            currency_code = currency_map.get(symbol)
                            print(f"Detected symbol: '{symbol}' | Code: {currency_code} | Amount: {amount}")

                            try:
                                if currency_code and currency_code != 'USD':
                                    usd_price = CurrencyConverter.convert_to_usd(currency_code, amount)
                                    print(f'Converted {amount} {currency_code} to {usd_price} USD')
                                    price = usd_price
                                else:
                                    price = round(amount, 2)
                            except Exception as e:
                                print(f'Currency conversion error: {e}')
                                price = -1

        return {'price': price, 'url': track_url}

        # # Find first track result
        # first_track = None
        # for item in soup.select('li.searchresult'):
        #     print(f'item: {item}')
        #     item_type = item.select_one('.itemtype')
        #     if item_type and item_type.text.strip().lower() == 'track':
        #         first_track = item
        #         break

        # if not first_track:
        #     print('No track result found')
        #     return {'price': -1, 'url': search_url}

        # heading = first_track.select_one('.heading a')
        # url = heading['href']
        # price_span = soup.select_one('span.base-text-color')
        # price = price_span.get_text(strip = True) if price_span else 'N/A'

        # return {
        #     'price': price,
        #     'url': url
        # }


        
    
    # def get_track_price(self, url):
    #     # Visit track page
    #     # self.driver.get(url)
    #     #sleep(2)
    #     returned = requests.get(url)
    #     track_soup = BeautifulSoup(returned.content, 'html.parser')

    #     price_span = track_soup.select_one('span.base-text-color')
    #     price = price_span.get_text(strip=True) if price_span else 'Price not found'

    #     #self.driver.quit()
    #     return price


# Example Usage:

# import time
# import queue
# import threading


# songsQueue = queue.Queue()
    
# songsQueue.put(('king von', 'armed and dangerous')),
# songsQueue.put(('king von', 'took her to the o')),


# songsQueue.put(('king von', 'gleesh place')),
# songsQueue.put(('king von', 'crazy story')),


# songsQueue.put(('king von', 'twin nem')),
# songsQueue.put(('lil durk', 'green light')),


# songsQueue.put(('lil baby', 'we paid')),
# songsQueue.put(('juice wrld', 'syphilis')),
    



# Function to search for songs in a queue
# def search_songs(songsQueue, results):
#     while not songsQueue.empty():
#         try:
#             artist, song = songsQueue.get(timeout= 2)
#         except queue.Empty:
#             print('queue empty')
#             return
#         bc = BandcampSearch(song, artist)
#         price = None
#         url = bc.get_track_url()
#         if url:
#             price = bc.get_track_price(url)
#         results.put((f'{artist} {song}', price))
#         songsQueue.task_done()




# Search for songs using multithreading
# start = time.perf_counter()

# results = queue.Queue()
# for i in range(4):
#     t = threading.Thread(target=search_songs, args=(songsQueue, results))
#     t.start()

# songsQueue.join()

# end = time.perf_counter()

# while not results.empty():
#     song, price = results.get()
#     print(f'{song} cost {price}')

# print(end - start)

