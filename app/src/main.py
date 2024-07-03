from finder import Finder
import os

if __name__ == '__main__':
    print("start")
    # print("OPENAI_API_KEY: ", os.environ['OPENAI_API_KEY'])
    try:

        # 検索パラメーター付きの URL
        finder = Finder("https://webscraper.io/")
        urls = finder.find_all_urls("/")
        sorted(urls, key=lambda d: d['url'])
        print(urls)
        finder.write_to_csv("urls.csv")
        print("end")
        
    except Exception as e:
        print(traceback.format_exc())
    finally:
        finder.browser.quit()


