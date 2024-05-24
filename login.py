from playwright.sync_api import sync_playwright
import os


if __name__ == "__main__":
    email = os.environ['MT_EMAIL']
    password = os.environ['MT_PASSWORD']

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('http://app.getmoneytree.com')
        page.wait_for_selector('input[name="guest[email]"]')

        page.type('input[name="guest[email]"]', email)
        page.type('input[name="guest[password]"]', password)
        page.click('.login-form-button')
        page.wait_for_selector('.free-trial')

        accessToken = None
        for cookie in page.context.cookies():
            if cookie.get('name') == 'accessToken':
                accessToken = cookie.get('value')
                break

        if accessToken is None:
            print("No accessToken found")
            browser.close()
            exit(-1)

        with open("bearer_token", "w") as f:
            f.write(accessToken)

        browser.close()
