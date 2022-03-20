
import requests
import re
import csv
import os
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import traceback
import psycopg2
from config import config
import logging
from datetime import datetime

options = webdriver.ChromeOptions()
options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
options.add_argument("--headless")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
browser = webdriver.Chrome(executable_path = os.environ.get("CHROMEDRIVER_PATH"), options=options)

def deactivate_record(mls):
    updater = """UPDATE public."Apartment" SET "Status" = %s WHERE "mls" = %s"""
    params = config()
    conn = psycopg2.connect(**params)
    cursor = conn.cursor()
    cursor.execute(updater,("Deactive", mls))
    conn.commit()
    cursor.close()

def new_price(mls,price):
        updater = """UPDATE public."Apartment" SET "Updated Price" = %s WHERE "mls" = %s"""
        params = config()
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()
        cursor.execute(updater,(price, mls))
        updater_two = """UPDATE public."Apartment" SET "Date reviewed" = %s WHERE "mls" = %s"""
        date = datetime.today().strftime('%Y-%m-%d')
        cursor.execute(updater_two,(date, mls))
        conn.commit()
        cursor.close()

def import_rows():
    try:
        # read database configuration
        params = config()
        # connect to the PostgreSQL database
        conn = psycopg2.connect(**params)
        # create a new cursor
        cursor = conn.cursor()
        postgreSQL_select_Query = """SELECT * FROM public."Apartment";"""
        cursor.execute(postgreSQL_select_Query)
        print("Selecting rows from apartment table using cursor.fetchall")
        apartment_records = cursor.fetchall()
        for row in apartment_records:
            if row[11] == "Active":
                double_check(row)
        # close communication with the database
        cursor.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

def double_check(row):
    url = row[8]
    price = row[3]
    browser.get(url)
    time.sleep(1)
    try:
        current_price = browser.find_element_by_class_name('data-price').text[1:].replace(",","")
    except:
        print("failed on row", row[0])
        deactivate_record(row[0])
        current_price = price
    if int(price) != int(current_price):
        print(row[0],"False")
        new_price(row[0],current_price)
date = datetime.today().weekday()
print(date)
if date == 6:
    import_rows()
browser.quit()
