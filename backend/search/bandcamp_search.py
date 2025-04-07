from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from time import sleep
class BandcampSearch:

    def __init__(self, track, artist):
        self.track = track
        self.artist = artist
        self.driver = self.setup_driver()

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

    def get_track_url(self):
        search_url = f'https://bandcamp.com/search?q={self.track}+{self.artist}&item_type=t'
        self.driver.get(search_url)
        sleep(3) 

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        # Find first track result
        first_track = None
        for item in soup.select("li.searchresult"):
            item_type = item.select_one(".itemtype")
            if item_type and item_type.text.strip().lower() == "track":
                first_track = item
                break

        if not first_track:
            self.driver.quit()
            return None  

        heading = first_track.select_one(".heading a")
        url = heading['href']
        return url
        
    
    def get_track_price(self, url):
        # Visit track page
        self.driver.get(url)
        sleep(2)
        track_soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        price_span = track_soup.select_one('span.base-text-color')
        price = price_span.get_text(strip=True) if price_span else "Price not found"

        self.driver.quit()
        return price


# Example Usage:

'''
bc = BandcampSearch("asthma", "dierot")

url = bc.get_track_url()
price = bc.get_track_price(url)

print("Track price: " + price)
print('\n')
print("Track URL: " + url)

'''


