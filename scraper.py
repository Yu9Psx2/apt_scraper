
import requests
import re
import csv
import os
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from datetime import date
import traceback
import psycopg2
from config import config
import logging
from datetime import datetime

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

def insert_ad(ad):
    """ insert a new ad into the ad table """
    sql = """INSERT INTO public."Apartment"("url", "mls", "address", "city","Date First","sqft", "price", "year_built","bedrooms","postal_code","construction")
             VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"""
    conn = None
    today = date.today()
    try:
        # read database configuration
        params = config()
        # connect to the PostgreSQL database
        conn = psycopg2.connect(**params)
        # create a new cursor
        cur = conn.cursor()
        # execute the INSERT statement
        cur.execute(sql, (ad.url,ad.mls,ad.address,ad.city,today,ad.sqft,ad.price,ad.year_built,ad.bedrooms,ad.postal_code,ad.construction))
        # get the generated id back
        # commit the changes to the database
        conn.commit()
        # close communication with the database
        cur.close()

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        logging.warning(f'Failed on MLS {mls}, error is {error}')
        logging.warning(f'MLS: {ad.mls} \n sqft: {ad.sqft} \n price: {ad.price} \n year: {ad.year} \n bedrooms: {ad.bedrooms} \n postal_code: {ad.postal_code} \n construction: {ad.construction} \n')
    finally:
        if conn is not None:
            conn.close()


class Record:
    def __init__(self,url,mls,address,city,sqft,price,year_built,bedrooms,postal_code,construction):
        self.url = url
        self.mls = mls
        self.address = address
        self.city = city
        self.sqft = sqft
        self.price = price
        self.year_built = year_built
        self.bedrooms = bedrooms
        self.postal_code = postal_code
        self.construction = construction

options = webdriver.ChromeOptions()
options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
#options.add_argument("--headless")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
browser = webdriver.Chrome(executable_path = os.environ.get("CHROMEDRIVER_PATH"), options=options)

def pick_up_links():
    array = []
    status = True
    count = 1
# change number below for initial load
    while status == True:
        url = "https://www.edmontonrealestate.pro/idx/search.html?refine=true&sortorder=ASC-HiddenDOM&map%5Blongitude%5D=0&map%5Blatitude%5D=0&map%5Bzoom%5D=&map%5Bradius%5D=&map%5Bpolygon%5D=&map%5Bne%5D=&map%5Bsw%5D=&map%5Bbounds%5D=0&search_universal=&search_type%5B0%5D=Condo+%2F+Townhouse&idx=ereb&minimum_price=&maximum_price=150000&search_reduced=&minimum_year=&maximum_year=&maximum_dom=7&minimum_bedrooms_above_grade=&maximum_bedrooms_above_grade=&minimum_bedrooms=&maximum_bedrooms=&minimum_full_bathrooms=&maximum_full_bathrooms=&minimum_half_bathrooms=&maximum_half_bathrooms=&minimum_sqft=&maximum_sqft=&minimum_acres=&maximum_acres=&minimum_stories=&maximum_stories=&search_location%5B0%5D=edmonton&p={}".format(count)
        browser.get(url)
        time.sleep(3)
        elems = browser.find_elements_by_class_name('info-links.brewImage')
        #elems = WebDriverWait(browser,10).until(EC.presence_of_element_located((By.ID, "mediaIMG")))
        for elem in elems:
            href = elem.get_attribute('href')
            if href is not None:
                array.append(href)
        if len(elems) == 0:
            status = False
        count += 1
    return array

def gather_details(url):
    details = apartment_dictionary(url)
    time.sleep(3)
    try:
        mls = browser.find_element_by_css_selector("div.details-extended:nth-child(4) > div:nth-child(1) > div:nth-child(1) > ul:nth-child(2) > li:nth-child(1) > span:nth-child(2)").text
        address = details.get("Address","Not Found ! ")
        city = details.get("Area","Not Found ! ")
        sqft = details.get("Square Footage","Not Found ! ")
        price = details.get("Price","Not Found ! ")[1:].replace(",","")
        year_built = details.get("Year Built","Not Found ! ")
        bedrooms = details.get("Bedrooms","Not Found ! ")
        postal_code = details.get("Postal Code","Not Found ! ")
        construction = details.get("Construction","Not Found ! ")
        ad_object = Record(url,mls,address,city,sqft,price,year_built,bedrooms,postal_code,construction)
        insert_ad(ad_object)
    except:
        logging.warning(f'Failed on MLS {mls}')
        logging.warning(f'MLS {mls} \n sqft {sqft} \n price {price} \n year {year_built} \n bedrooms {bedrooms} \n postal_code {postal_code} \n construction {construction} \n')
        print("mls", mls)
        print("address", address)
        print("city", city)
        print("sqft", sqft)
        print("price", price)
        print("year", year_built)
        print("bedrooms", bedrooms)
        print("postal_code", postal_code)
        print("construction", construction)

def apartment_dictionary(url):
    switcher = {}
    browser.get(url)
    time.sleep(3)
    container = browser.find_elements_by_class_name("keyvalset")
    for c in container:
        array = c.find_elements_by_class_name("keyval")
        for i in array:
            switcher[i.find_element_by_tag_name("strong").text] = i.find_element_by_tag_name("span").text
        # for x, y in switcher.items():
        #     print(x, y)
    return switcher


#database has been loaded; now can populate database on go forward basis

date = datetime.today().weekday()
print(date)
if date == 6:
    links_to_be_searched = pick_up_links()
    for i in links_to_be_searched:
        gather_details(i)

#Single test url
#gather_details("https://www.edmontonrealestate.pro/listing/Edmonton/Queen-Mary-Park/e4200495-137-10636-120-street-nw-edmonton-ab-t5h-4l5/")
browser.quit()



