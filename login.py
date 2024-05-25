from selenium import webdriver
from selenium.webdriver.common.by import By
import os


if __name__ == "__main__":
    email = os.environ['MT_EMAIL']
    password = os.environ['MT_PASSWORD']

    options = webdriver.ChromeOptions()
    driver = webdriver.Remote(
        command_executor='http://192.168.11.12:4444/wd/hub',
        options=options)
    try:
        driver.implicitly_wait(10)

        driver.get('http://app.getmoneytree.com')
        driver.find_element(By.CSS_SELECTOR,
                            'input[name="guest[email]"]').send_keys(email)

        driver.find_element(By.CSS_SELECTOR,
                            'input[name="guest[password]"]').send_keys(password)
        driver.find_element(By.CSS_SELECTOR,
                            '.login-form-button').click()
        driver.find_element(By.CSS_SELECTOR,
                            '.free-trial')

        token = driver.get_cookie("accessToken").get('value')
        with open("bearer_token", "w") as f:
            f.write(token)

    finally:
        driver.quit()
