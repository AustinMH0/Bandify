#from selenium import webdriver
#from selenium.webdriver.chrome.options import Options
import requests
from bs4 import BeautifulSoup
from time import sleep

class BandcampSearch:

    def __init__(self, track, artist):
        self.track = track
        self.artist = artist
        #self.driver = self.setup_driver()

        self.driver = None


    def setup_driver(self):
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-client-side-phishing-detection")
        options.add_argument("--disable-crash-reporter")
        options.add_argument("--disable-oopr-debug-crash-dump")
        options.add_argument("--no-crash-upload")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-low-res-tiling")
        options.add_argument("--log-level=3")
        options.add_argument("--silent")
        return webdriver.Chrome(options=options)

    def get_track_price(self):
        search_url = f'https://bandcamp.com/search?q={self.track}+{self.artist}&item_type=t'
        returned = requests.get(search_url)
        
        
        

        soup = BeautifulSoup(returned.content, 'html.parser')
        
        # Find first track result
        first_track = None
        for item in soup.select("li.searchresult"):
            item_type = item.select_one(".itemtype")
            if item_type and item_type.text.strip().lower() == "track":
                first_track = item
                break

        if not first_track:
            #self.driver.quit()
            return None  

        heading = first_track.select_one(".heading a")
        url = heading['href']
        price_span = soup.select_one('span.base-text-color')
        price = price_span.get_text(strip = True) if price_span else "Price not found"

        return {"price": price or -1, "url": url or ""}


        
    
    # def get_track_price(self, url):
    #     # Visit track page
    #     # self.driver.get(url)
    #     #sleep(2)
    #     returned = requests.get(url)
    #     track_soup = BeautifulSoup(returned.content, 'html.parser')

    #     price_span = track_soup.select_one('span.base-text-color')
    #     price = price_span.get_text(strip=True) if price_span else "Price not found"

    #     #self.driver.quit()
    #     return price


# Example Usage:

# import time
# import queue
# import threading


# songsQueue = queue.Queue()
    
# songsQueue.put(("king von", "armed and dangerous")),
# songsQueue.put(("king von", "took her to the o")),


# songsQueue.put(("king von", "gleesh place")),
# songsQueue.put(("king von", "crazy story")),


# songsQueue.put(("king von", "twin nem")),
# songsQueue.put(("lil durk", "green light")),


# songsQueue.put(("lil baby", "we paid")),
# songsQueue.put(("juice wrld", "syphilis")),
    



# Function to search for songs in a queue
# def search_songs(songsQueue, results):
#     while not songsQueue.empty():
#         try:
#             artist, song = songsQueue.get(timeout= 2)
#         except queue.Empty:
#             print("queue empty")
#             return
#         bc = BandcampSearch(song, artist)
#         price = None
#         url = bc.get_track_url()
#         if url:
#             price = bc.get_track_price(url)
#         results.put((f"{artist} {song}", price))
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
#     print(f"{song} cost {price}")

# print(end - start)

