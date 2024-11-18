import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import json
import time


path = '/mnt/c/Users/Nathan/Desktop/checked-schemas'
save_location = Path(path)
save_location.mkdir(exist_ok=True)
save_location = path + '/schemas.csv'

append_schema_to_csv = False
csv_mode = 'w'
if append_schema_to_csv:
    csv_mode = 'a'

websites = open("sites-to-check.txt").readlines()
time_delay = 5
if len(websites) <= 1:
    time_delay = 0



def checkSchema(schema, website):
    schema_json = json.loads(schema.contents[0])
    
    missing_items = []
    invalid_items = []
    empty_items = []
    missing_items_message = ''
    invalid_items_message = ''
    empty_items_message = ''

    def checkItem(json, item, group = False):
        checked_item = json.get(item)
        if checked_item is None:
            if group:
                missing_items.append(item + ' group')
            else:
                missing_items.append(item)
            return False
        if checked_item == "":
            if group:
                empty_items.append(item + ' group')
            else:
                empty_items.append(item)
            return False
        return True
     
    items_to_check = ['@type','logo','image','name','description',['address','streetAddress','addressLocality','addressRegion','postalCode','addressCountry'],['geo','latitude','longitude'],'url','telephone']

    for item in items_to_check:
        if isinstance(item, str):
            checkItem(schema_json,item)
        else:
            main_item = item[0]
            if checkItem(schema_json,main_item, True):
                i = 0
                for subitem in item:
                    if i == 0:
                        i += 1
                    else:
                        checkItem(schema_json.get(main_item),subitem)

    if checkItem(schema_json,'openingHoursSpecification'):
        all_days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        for days in schema_json.get('openingHoursSpecification'):
            if days.get('dayOfWeek'):
                if days.get('opens') is None:
                    missing_items.append('missing opening hours for: ' + ", ".join(days.get('dayOfWeek')))
                if days.get('opens') == "":
                    empty_items.append('empty opening hours for: ' + ", ".join(days.get('dayOfWeek')))
                if days.get('closes') is None:
                    missing_items.append('missing closing hours for: ' + ", ".join(days.get('dayOfWeek')))
                if days.get('closes') == "":
                    empty_items.append('empty opening hours for: ' + ", ".join(days.get('dayOfWeek')))
                for day in days.get('dayOfWeek'):
                    day_is_present = False
                    for val in all_days:
                        if day == val:
                            day_is_present = True
                            all_days.remove(val)
                    if day_is_present == False:
                        invalid_items.append('hours has invalid day: ' + day)
        if len(all_days) > 0:
            missing_items.append('missing hours for: ' + ", ".join(all_days))

    if len(missing_items) > 0:
        missing_items_message = 'missing items are as follows: ' + ", ".join(missing_items)
        print(missing_items_message)
    else:
        missing_items_message = 'N/A'
    if len(empty_items) > 0:
        empty_items_message = 'empty items are as follows: ' + ", ".join(empty_items)
        print(empty_items_message)
    else:
        empty_items_message = 'N/A'
    if len(invalid_items) > 0:
        invalid_items_message = 'invalid items are as follows: ' + ", ".join(invalid_items)
        print(invalid_items_message)
    else:
        invalid_items_message = 'N/A'
    
    df = pd.DataFrame({'website':[website],'schemas': [schema_json],'missing_items':[missing_items_message],'empy_items':[empty_items_message],'invalid_items':[invalid_items_message]})
    df.to_csv(save_location, mode=csv_mode, index=False, encoding="utf-8")


def getSchema(website_url):
    site = 'https://' + website_url + '/'
    print(site)
    response = requests.get(site, timeout=5)
    h = response.history
    if(len(h) > 0):
        site = 'https://www.' + website_url + '/'
        print(site)
        response = requests.get(site, timeout=5)
    soup = BeautifulSoup(response.text, 'html.parser')
    schema = soup.find('script', attrs={'type':'application/ld+json'})
    if schema != None:
        checkSchema(schema, website_url)
    else:
        print(website_url + ' has no schema')    
        df = pd.DataFrame({'website':[website_url],'schemas': ['No Schema Found'],'missing_items':['N/A'],'invalid_items':['N/A']})
        df.to_csv(save_location, mode=csv_mode, index=False, encoding="utf-8")

for website in websites:
    time.sleep(time_delay)
    getSchema(website[:-1])


