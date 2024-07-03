from finder import Finder
import image_diff 
import traceback
import os
import json

with open('targets.json', 'r') as f:
    targets = json.load(f)

if __name__ == '__main__':
    for target in targets:
        for device in ["desktop", "mobile"]:
            try:
                finder = Finder("", device=device)
                currentFile, _ = finder.get_full_page_screenshot(target["current"], target["current"])
                newFile, _ = finder.get_full_page_screenshot(target["new"], target["new"])
                image_diff.make_diff_image(currentFile, newFile, os.path.join("/app/src/diff/",target['title'], device))
            except Exception as e:
                print(traceback.format_exc())
            finally:
                finder.browser.quit()


