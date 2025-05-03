from playwright.sync_api import sync_playwright




def take_screenshot(url, output_file):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.screenshot(path=output_file, full_page=True)
        browser.close()

def get_name(url)->str:
    if "://" in url:
        url = url.split("://")[1]
    return url.split('/')[0]

ss_output = lambda url, subfolder="screenshots" : subfolder+"/"+get_name(url)+".png"

# Example
url = "https://crescentdentalhealth.co.uk"

take_screenshot(url, ss_output(url))
