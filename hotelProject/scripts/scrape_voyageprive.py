import time
import re
from datetime import datetime, timedelta
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By

def initialize_webdriver():
    """Initialize the Selenium WebDriver."""
    driver = webdriver.Chrome()
    time.sleep(3)  # Allow the WebDriver to initialize
    return driver

def login_to_website(driver, email, password):
    """Log in to the Voyage Privé website."""
    driver.get("https://www.voyage-prive.co.uk/login/index#signin")
    time.sleep(5)

    # Accept cookies
    cookie_button = driver.find_element(By.CSS_SELECTOR, "#cookieBanner > div > div.BannerContainer__buttons > button.Button.Button--light.Button--accept")
    cookie_button.click()
    time.sleep(2)

    # Enter login credentials
    email_field = driver.find_element(By.CSS_SELECTOR, "#reactLogin > div > div > div.Login__content > form > div > div > div:nth-child(1) > input[type=email]")
    email_field.send_keys(email)
    time.sleep(1)

    password_field = driver.find_element(By.CSS_SELECTOR, "#reactLogin > div > div > div.Login__content > form > div > div > div.Login__line.passwordContainer > div > input")
    password_field.send_keys(password)
    time.sleep(1)

    # Click the login button
    login_button = driver.find_element(By.CSS_SELECTOR, "#reactLogin > div > div > div.Login__content > form > div > div > div.Login__line.Login__line--spaced > button")
    login_button.click()
    time.sleep(5)

def scroll_to_bottom(driver):
    """Scroll to the bottom of the page to load all content."""
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def add_dates_to_dataframe(df):
    """Add start_date and end_date columns to the DataFrame based on time_remaining."""
    current_datetime = datetime.now()
    start_dates, end_dates = [], []

    for time_remaining in df['time_remaining']:
        match_days = re.search(r"(\d+)\s*days?", time_remaining, re.IGNORECASE)
        if match_days:
            days = int(match_days.group(1))
            time_delta = timedelta(days=days)
        else:
            match_time = re.search(r"(\d+)h\s*(\d+)?m?", time_remaining, re.IGNORECASE)
            if match_time:
                hours = int(match_time.group(1))
                minutes = int(match_time.group(2)) if match_time.group(2) else 0
                time_delta = timedelta(hours=hours, minutes=minutes)
            else:
                time_delta = timedelta()

        end_datetime = current_datetime + time_delta
        start_dates.append(current_datetime)
        end_dates.append(end_datetime)

    df['start_date'] = start_dates
    df['end_date'] = end_dates
    return df

def extract_hotel_data(driver):
    """Extract hotel data from the webpage."""
    ads = driver.find_elements(By.XPATH, "//article[contains(@id, 'push-promo')]")
    for ad in ads:
        driver.execute_script("arguments[0].remove();", ad)

    hotel_list = driver.find_element(By.CSS_SELECTOR, '#section-now > div')
    hotel_elements = hotel_list.find_elements(By.TAG_NAME, "article")

    hotel_sale_destination, hotel_name, hotel_sale_price, hotel_sale_time_remaining, exclusif = [], [], [], [], []

    for hotel in hotel_elements:
        sale_price, sale_time_remaining, sale_destination, name, exclusif_status = None, None, None, None, 'no'
        sub_elements1 = hotel.find_elements(By.TAG_NAME, "a")
        if sub_elements1:
            sub_elements2 = sub_elements1[0].find_elements(By.TAG_NAME, "div")
            for element in sub_elements2:
                class_name = element.get_attribute("class")
                if class_name == 'sale_price':
                    sale_price = element.text
                    if sale_price == 'EXCLUSIF':
                        exclusif_status = 'yes'
                        link_url = hotel.find_element(By.TAG_NAME, "a").get_attribute("href")
                        driver.execute_script("window.open(arguments[0], '_blank');", link_url)
                        driver.switch_to.window(driver.window_handles[-1])
                        time.sleep(2)
                        try:
                            sale_price = driver.find_element(By.CSS_SELECTOR, ".offer-price.details-price.euro").text
                        except:
                            sale_price = "N/A"
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                elif class_name == 'sale-time-remaining  specific-not-near ':
                    sale_time_remaining = element.text
            if sub_elements1:
                sub_elements3 = sub_elements1[0].find_elements(By.TAG_NAME, "span")
                for element in sub_elements3:
                    class_name = element.get_attribute("class")
                    if class_name == 'sale-destination':
                        sale_destination = element.text
                    elif class_name == 'hotel-name':
                        name = element.text

        hotel_sale_price.append(sale_price or "N/A")
        hotel_sale_time_remaining.append(sale_time_remaining or "N/A")
        hotel_sale_destination.append(sale_destination or "N/A")
        hotel_name.append(name or "N/A")
        exclusif.append(exclusif_status)

    return pd.DataFrame({
        "Country": hotel_sale_destination,
        "hotel_name": hotel_name,
        "price": hotel_sale_price,
        "time_remaining": hotel_sale_time_remaining
    })

def save_data_to_csv(df):
    """Save the DataFrame to a CSV file."""
    today = datetime.today().strftime('%d_%m_%Y')
    output_file = f"../data/voyageprive_hotels_{today}.csv"
    df.to_csv(output_file, index=False)
    print(f"Data saved to {output_file}")

if __name__ == "__main__":
    my_email = "axelberglund98@gmail.com"
    my_password = "Password_1"

    driver = initialize_webdriver()
    try:
        login_to_website(driver, my_email, my_password)
        scroll_to_bottom(driver)
        df = extract_hotel_data(driver)
        df = add_dates_to_dataframe(df)
        save_data_to_csv(df)
    finally:
        driver.quit()
