from selenium import webdriver
from selenium.webdriver.common.devtools import v124 as devtools
from selenium.webdriver.common.by import By
import traceback
import csv
import urllib.parse
import time
import os
from os import path
import pathlib
import base64
from gpt import GPT
# import selenium.webdriver.common.devtools.v111 as devtools
import trio

class Finder:
    def __init__(self, base_url, screenshot_dir="/app/screenshots", device="desktop"):
        options = webdriver.ChromeOptions()
        if device == "mobile":
            options.add_argument("--window-size=375,812")
        else:
            options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        # options.set_capability("browserVersion", "latest")
        # options.set_capability("browserName", "chrome")
        options.set_capability(
            "selenoid:options", {"enableVNC": True, "enableVideo": False}
        )
        print("init start")
        self.base_url = base_url
        self.browser = webdriver.Remote(
            command_executor="http://selenium:4444/wd/hub",
            options=options
        )
        self.browser.maximize_window()
        self.urls = []
        self.screenshot_dir = path.join(screenshot_dir, device) 
        self.gpt = GPT("gpt-4-turbo", os.environ['OPENAI_API_KEY'])
        print("init done")
        pass

    def empty_urls(self):
        self.urls = []

    def execute_cdp(self, cmd):
        async def execute_cdp_async():
            async with self.browser.bidi_connection() as session:
                cdp_session = session.session
                return await cdp_session.execute(cmd)
        # It will have error if we use asyncio.run
        # https://github.com/SeleniumHQ/selenium/issues/11244
        return trio.run(execute_cdp_async)
    
    def find_all_urls_in_one_page(self, url):
        try:
            self.browser.get(url)
        except Exception as e:
            print("error: " + url)
            print(traceback.format_exc())
            return []
        elms = self.browser.find_elements(By.TAG_NAME, "a")
        result = []
        for v in elms:
            try:
                result.append(v.get_attribute('href'))
            except:
                continue
        return result   

    def get_full_page_screenshot(self, url, file_name):
        self.browser.get(url)
        time.sleep(1)
        return self.get_current_full_page_screenshot(file_name)

    def generate_screenshot_path_from_url(self, url):
        return urllib.parse.urlparse(url).path

    def read_image_as_base64(self, abs_path):
        with open(abs_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def get_current_full_page_screenshot(self, file_name):
        try:
            if file_name.startswith("/"):
                file_name = file_name[1:]
            file_dir = path.join("/app/screenshots/", file_name)
            html_dir = path.join("/app/astro/src/pages", file_name)
            
            imageName = "index.png"
            width = self.browser.execute_script("return Math.max( document.body.scrollWidth, document.body.offsetWidth, document.documentElement.clientWidth, document.documentElement.scrollWidth, document.documentElement.offsetWidth );")
            height = self.browser.execute_script("return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight );")
            self.browser.set_window_size(width, height)

            pathlib.Path(file_dir).mkdir(parents=True, exist_ok=True)
            pathlib.Path(html_dir).mkdir(parents=True, exist_ok=True)

            full_page = self.browser.find_element(By.TAG_NAME, "body")
            full_page.screenshot(imageName)
            os.system(f"mv {imageName} {file_dir}")
            
            return path.join(file_dir, imageName), html_dir
        except Exception as e:
            print("error: " + file_name)
            print(traceback.format_exc())
            return []

    def find_all_urls(self, url):
        print(url)
        if url.startswith("/") or url == (""):
                # print("start with /: " + url)
                url = urllib.parse.urljoin(self.base_url, url)

        for v in self.find_all_urls_in_one_page(url):
            if v is None or v == "" or v == "#":
                continue

            if v.startswith("/"):
                v = urllib.parse.urljoin(self.base_url, v)

            if not self.is_same_url(v, self.base_url):
                continue
            
            if not self.has_url(v):
                print("self.is_same_url(v, self.base_url): ", self.is_same_url(v, self.base_url))
                print("v:                                  ",v)
                print("self.base_url:                      ",self.base_url)
                print("try to get:                         " + v)
                title = ""
                execute_note = ""
                try:
                    self.browser.get(v)
                    # Execute Chrome dev tool command to obtain the mhtml file
                    mhtml = self.execute_cdp(devtools.page.capture_snapshot())


                    # Write the file locally
                    with open('/app/qq.mhtml', 'w', newline='') as f:   
                        f.write(mhtml)
                    print("write done")

                    time.sleep(1000)
                    imagePath, html_dir = self.get_current_full_page_screenshot(self.generate_screenshot_path_from_url(v))
                    base64Image = self.read_image_as_base64(imagePath)
                    # print("base64Image: ", base64Image)
                    resp = self.gpt.base64_image_to_astro_tailwind_code(base64Image)
                    with open(path.join(html_dir,"index.astro"), "w") as file:
                        file.write(resp)

                    # print("b64Image: ", b64Image)
                    title = self.browser.title
                    self.urls.append({"url": v, "title": title, "execute_note": execute_note})
                    self.find_all_urls(v)
                except Exception as e:
                    print("error: " + v)
                    print(traceback.format_exc())
                    execute_note = traceback.format_exc()
                    self.urls.append({"url": v, "title": title, "execute_note": execute_note})
        return self.urls

    def is_same_url(self, url1, url2):
        return urllib.parse.urlparse(url1).netloc == urllib.parse.urlparse(url2).netloc
    
    def has_url(self, url):
        for v in self.urls:
            if v["url"] == url:
                return True
        return False

    def write_to_csv(self, file_name):
        with open(file_name, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["url", "title"])
            for v in self.urls:
                writer.writerow([v["url"], v["title"]])
