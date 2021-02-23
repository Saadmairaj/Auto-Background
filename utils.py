import os
import time
import queue
import random
import threading
import urllib.parse

from selenium import webdriver
from appscript import app, mactypes
from urllib.request import urlretrieve
from chromedriver_autoinstaller import install

BASE_DIR = os.path.realpath(os.path.curdir)


def change_background_image(file):
    return app('Finder').desktop_picture.set(
        mactypes.File(file))


def threaded(arg):
    """Thread decorator.

    To use as decorator to make a function call threaded, 
    takes function as argument. To join=True pass @threaded(True)."""
    kw = {}

    def wrapper(*args, **kwargs):
        kw['return'] = kw['function'](*args, **kwargs)

    def _threaded(fn):
        kw['function'] = fn

        def thread_func(*args, **kwargs):
            thread = threading.Thread(
                target=wrapper, args=args, kwargs=kwargs, daemon=True)
            thread.start()
            if kw.get('wait'):
                thread.join()
            return kw.get('return', thread)
        return thread_func

    if callable(arg):
        return _threaded(arg)
    kw['wait'] = arg
    return _threaded


class download_image:
    previous_filename = []

    def __init__(self, link, save=False, save_path='./images'):
        """Image downloader. 
        
        Downloads and save the image if the parameter `save=True`."""
        self.save = save
        self.filename = os.path.join('./.tmpimage.jpg')
        if save:
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            count = len(
                [name for name in os.listdir(
                    save_path) if os.path.isfile(name)])
            self.filename = os.path.join(save_path, f'image_{count}.jpg')
            while os.path.exists(self.filename):
                count += 1
                self.filename = os.path.join(save_path, f'image_{count}.jpg')
        self.link = link

    def delete_previous(self):
        """Deletes the previous downloaded saved image."""
        if self.previous_filename and os.path.exists(
                self.previous_filename[0]):
            os.remove(self.previous_filename.pop(0))

    def __enter__(self):
        """Downloads the image from the url on enter."""
        self.filename = os.path.realpath(
            urlretrieve(self.link, self.filename)[0])
        return self

    def __exit__(self, *args, **kwargs):
        """Removes the image if save=False."""
        if not self.save:
            os.remove(self.filename)
        self.previous_filename.append(self.filename)


class Queue(queue.Queue):
    def __contains__(self, item):
        with self.mutex:
            return item in self.queue

    def shuffle(self):
        random.shuffle(self.queue)


class ImageLink:

    LINK = 'https://unsplash.com/wallpapers/desktop/'

    def __init__(self, timeout=5, scroll_time=0.5, pages=-1,
                 refresh_timer=5000, fetch_start_callback=None,
                 fetch_end_callback=None):
        """Image links class.
        
        Fetches all images links and save them in queue which 
        makes them thread safe and can be used together with 
        tkinter-threading."""

        self._queue = Queue()
        self._categories = {}
        self.fetch_start_callback = fetch_start_callback
        self.fetch_end_callback = fetch_end_callback
        self._fetching = False
        self._stop_fetching = False

        # Configurable
        self.timeout = timeout
        self.scroll_time = scroll_time
        self.pages = pages
        self.refresh_timer = refresh_timer

        self._driver = self._create_driver(1, keep_alive=True)
        self._fetch_links(self.LINK)

    @staticmethod
    def _create_driver(headless=True, keep_alive=False):
        """Create Chrome driver."""
        install()   # checks for chromedriver
        op = webdriver.ChromeOptions()  # Chrome Options
        # Disable images
        prefs = {"profile.managed_default_content_settings.images": 2}
        op.add_experimental_option("prefs", prefs)      # slight difference
        if headless:
            op.add_argument('--headless')               # faster by 1/3
        op.add_argument('--disable-gpu')                # slight difference
        # op.add_argument('--window-size=500,500')        # faster by 1/4
        op.add_experimental_option(
            "excludeSwitches", ["enable-automation"])
        op.add_experimental_option('useAutomationExtension', False)
        driver = webdriver.Chrome(
            options=op, keep_alive=keep_alive)
        return driver

    def _fetch(self, link):
        self._driver.get(link)
        time.sleep(1)

        # Scrolling page.
        self._driver.set_page_load_timeout(self.timeout)
        page_height = self._driver.execute_script(
            "return document.body.scrollHeight")
        one_page_height = page_height/2

        while self.pages and not self._stop_fetching:
            height = self._driver.execute_script(
                "return document.body.scrollHeight") - one_page_height
            self._driver.execute_script(
                f"window.scrollTo(0, {height});")
            time.sleep(self.scroll_time)
            new_height = self._driver.execute_script(
                "return document.body.scrollHeight")

            if new_height == page_height:
                break

            page_height = new_height
            if self.pages != -1:
                self.pages -= 1

            for img_id in self._driver.find_elements_by_class_name('_2Mc8_'):
                downlaod_link = img_id.get_attribute(
                    "href")+'/download?force=true'
                if downlaod_link not in self._queue:
                    self._queue.put(downlaod_link)

    @threaded
    def _fetch_links(self, *links):
        if self._fetching and not links:
            return

        self._fetching = True

        if self.fetch_start_callback is not None:
            self.fetch_start_callback()

        for link in links:
            self._fetch(link)

        if self.fetch_end_callback is not None:
            self.fetch_end_callback()

        self._fetching = False

    @property
    def categories(self):
        self._categories.clear()
        self._driver.get(self.LINK)
        cates = self._driver.find_elements_by_xpath(
            "//*[@class='_2a4HK HqGX1']")
        for cate in cates:
            self._categories[cate.text] = urllib.parse.urljoin(
                self.LINK, '-'.join(
                    cate.text[3: -11].lower().split(' ')))
        return self._categories

    @categories.setter
    def categories(self, value):
        self._categories = value
        self._stop_fetching = True
        with self._queue.mutex:
            self._queue.queue.clear()

        self._stop_fetching = False
        self._driver.delete_all_cookies()
        self._fetch_links(
            *list(self.categories.values()))

    def download_link(self, shuffle=False):
        if self._queue.empty():
            self._fetch_links(
                *list(self.categories.values()))
        if shuffle:
            self._queue.shuffle()
        return self._queue.get()

    def close(self):
        self._driver.quit()


if '__main__' == __name__:
    image = ImageLink(pages=2, scroll_time=0.4)
    print(image._queue.qsize())
    print(image.categories)
    with download_image(image.download_link(True)) as di:
        change_background_image(di.filename)
    image.close()
