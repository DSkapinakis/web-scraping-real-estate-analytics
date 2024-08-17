#import libraries
import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
import numpy as np
import requests
import re
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
import matplotlib.pyplot as plt
from datetime import datetime

# Google  place ids - to be further enhanced
geo_ids = {}
geo_ids['exarcheia'] = 'ChIJk8jKmja9oRQRck07-S29ACY'
geo_ids['kolonaki'] = 'ChIJwdDKbEe9oRQREk47-S29ACY'
geo_ids['pangrati'] = 'ChIJy1stSUK9oRQRi9ObJcOmO20'
geo_ids['kifisia'] = 'ChIJi_32gR6foRQRlpfLA-6I2OA'
geo_ids['marousi'] = 'ChIJN6QK8dmYoRQRbzNbL4ODpQY'
geo_ids['gyzi'] =  'ChIJXcJaXLOioRQRM1r_V3pg178'
geo_ids['kypseli'] = 'ChIJc0WaHrmioRQRUk07-S29ACY'
geo_ids['galatsi'] = 'ChIJLbYjnoSioRQRGDYRmwa6d6M'
geo_ids['zografou'] = 'ChIJuQ2QkfqXoRQRivx3qy72mZk'
geo_ids['glyfada'] = 'ChIJr3Ztlyi-oRQR6El5e7CyRpM'


"""
Main functions of the scraper program following
"""

def base_url(transaction_type, item_type, location_id = False):

    valid_transaction_type = {'rent','buy'}
    valid_item_type = {'re_residence','re_prof','re_land','re_parking'}


    if transaction_type not in valid_transaction_type:
        raise ValueError('base_url: transactiont_type should be one of %r.' % valid_transaction_type)
    if item_type not in valid_item_type:
        raise ValueError('base_url: item_type should be one of %r.' % valid_item_type)

    if location_id == False:
        return f'https://www.xe.gr/en/property/results?transaction_name={transaction_type}&item_type={item_type}&sorting=create_desc'
    else:
        return f'https://www.xe.gr/en/property/results?transaction_name={transaction_type}&item_type={item_type}&sorting=create_desc&geo_place_ids%5B%5D={location_id}'
    
def batch_pages(a):

    k=[]
    l=[]
    count=0
    if len(a)%2 == 0:
        b = a
        c=[]
    else:
        c=a[-1]
        b = a[:-1]
    while count < len(b):
        while len(k) < 2:
            k.append(b[count])
            count += 1
        l.append(k)
        k=[]
    if c!=[]: l.append([c])       
    
    return l 

def pages2scrape(num):
    pages = [i for i in range(1,num+1)]
    return pages

def extract_url_prop(base_url, start_page, end_page):
    
    urls = []
    for i in range(start_page, end_page+1):
        reqs = requests.get(base_url + f'&page={i}')
        soup = BeautifulSoup(reqs.text, 'html.parser')
        for link in soup.find_all('a'):
            urls.append(link.get('href'))

    prop_urls = []  # urls related to property entries
    for link in urls:
        if link[:32] == 'https://www.xe.gr/en/property/d/':
            prop_urls.append(link)
        
    prop_urls = list(set(prop_urls)) # remove duplicate property entries with set
    print('Number of properties collected: ', len(prop_urls))
    return prop_urls


def extract_data(url):
    
    driver = webdriver.Chrome()
    driver.get(url)
    content = driver.page_source
    soup = BeautifulSoup(content, features='html.parser')

    sm = soup.find('div',class_='title').h1.get_text()
    location = soup.find('div',class_='title').h3.get_text()
    price = soup.find('div', class_='price').h2.get_text()
    publication_Date = soup.find('section', class_ = 'grid-x statistics align-left').p.get_text()
    publication_Date = datetime.strptime(publication_Date[publication_Date.find(':')+1:], '%B %d, %Y').strftime('%d/%m/%Y')
    visits = soup.find('p', {'data-testid': 'views'}).get_text()
    visits = int(visits[visits.find(':')+1:])
    saves = soup.find('p', {'data-testid': 'saves'}).get_text()
    saves = int(saves[saves.find(':')+1:])

    # Find the <section> element with class="characteristics-wrapper"
    characteristics_section = soup.find('section', class_='characteristics-wrapper')

    # Find all <li> elements with class="cell large-6" under the characteristics_section
    characteristics_items = characteristics_section.find_all('li', class_='cell large-6')

    # Initialize a dictionary to store the extracted characteristics
    characteristics = {}
    # Iterate over each characteristics item
    for item in characteristics_items:
        # Find the <span> elements containing the characteristic name and value
        spans = item.find_all('span')
        if len(spans) == 2:
            characteristic_name = spans[1].get_text(strip=True)
            characteristic_value = spans[0].get('class')[1]  # Extract class attribute for icon
            characteristics[characteristic_name] = characteristic_value

    dic = {}
    for i in characteristics.keys():
        split_string = i.split(':')
        # Extract the column name and value
        column_name = split_string[0].strip()
        value = split_string[-1].strip()
        dic[column_name] = value
    

    dic['Price'] = price
    dic['Location'] = location
    dic['Square Meters'] = sm
    dic['publication_Date'] = publication_Date
    dic['visits'] = visits
    dic['saves'] = saves
    dic['link'] = url
    
    return dic

def prop_to_df(property_urls):

    data = {}    # extract preperty data
    for i,l in enumerate(property_urls):  
        data[i] = extract_data(l) 
    
    all_cols = []
    for l in list(data.keys()):
        for i in list(data[l].keys()):
            all_cols.append(i)
    unique_cols = list(set(all_cols))

    df = pd.DataFrame(columns=unique_cols)
    for i in list(data.keys()):
        a = pd.DataFrame(data[i], index=[0])
        df = pd.concat([df,a], axis=0)
    df = df.reset_index(drop=True)
    
    return df

def batch_scraping(location, transaction_type, item_type, num_pages):
    
    print(f'Scraping data for {location}...  (details: {transaction_type}, {item_type})')
    pages = pages2scrape(num_pages)
    loc_url = base_url(transaction_type, item_type, geo_ids[location])
    data = {}
    for i,l in enumerate(batch_pages(pages)):
        if len(l)==2:
            print(f'Batch {i}:')
            n_properties = extract_url_prop(loc_url,l[0],l[1])
        else:
            n_properties = extract_url_prop(loc_url,l[0],l[0])
        df = prop_to_df(n_properties)
        data[f'batch_{i}'] = df

    return data

