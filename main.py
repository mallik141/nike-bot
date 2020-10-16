#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Buy stuff from nike.com/launch

Useful endpoints at  https://api.nike.com

/launch/launch_views/v2/?filter=productId(...)
Find whether can buy an item

/merch/skus/v2/?filter=productId%28...&filter=country%28US%29
Find SKUs of different sizes of items

-----------------------------
They set so many cookies that it is easier to lauch selenium,
let it do all of the horrible JS and then simply clone the session 
to use with requests
"""

import requests
from requests import session
import re
from fake_useragent import UserAgent
from selenium import webdriver
import json
import time
from datetime import datetime

class Worker():
    def __init__(self):
        self.product_url = ''
        ua = UserAgent()
        self.userAgent = ua.random
        
        self.driver = self.start_selenium()
        email,password = self.get_logins()
        self.login(email,password)
        
        self.s = self.create_session()
                
    def get_logins(self):
        with open('login','r') as f:
            l = f.read()
        t = l.split("\n")
        return t[0],t[1]
    
    def start_selenium(self):
        #chrome_options = webdriver.ChromeOptions()
        #chrome_options.add_argument(f'user-agent={self.userAgent}')
        
        url0 = 'https://www.nike.com/launch?s=upcoming'
        
        #chrome = webdriver.Chrome(options=chrome_options)
        chrome = webdriver.Chrome()
        chrome.get(url0)
        
        return chrome
    
    def login(self,email,password):
        button = self.driver.find_element_by_class_name('join-log-in')
        button.click()
        inputs = self.driver.find_elements_by_tag_name('input')
        for i in inputs:
            tmp = i.get_attribute('type')
            if tmp == 'email':
                i.send_keys(email)
            elif tmp == 'password':
                i.send_keys(password)
            elif tmp == 'button':
                i.click()
        time.sleep(5)
    
    def create_session(self):
        cookies= self.driver.get_cookies()
        s = session()
        for cookie in cookies:
            s.cookies.set(cookie['name'], cookie['value'])
        return s
    
    def get_product_id_from_url(self):
        r=self.s.get(self.product_url)
        if r.status_code != 200:
            self.prod_ids = None
            return -1
        else:
            o = []
            matches = re.findall('(productId":"(.*?)")',r.text)
            for m in matches:
                if not m[1] in o and m[1] != '':
                    o.append(m[1])
            self.prod_ids = o
            return o
    
    def get_state(self,ids):
        '''
        Find whether the item is launched using the API

        Parameters
        ----------
        ids : List
            List of product ids.

        Returns
        -------
        launched : Boolean
            True when launched, False otherwise.

        '''
        base_url = 'https://api.nike.com/launch/launch_views/v2/?filter=productId({})'
        
        good_ids = []
        for i in ids:
            if i != '':
                good_ids.append(i)
            
        url = base_url.format(','.join(good_ids))
        output = json.loads(requests.get(url).text)
        
        launched = 'LIVE'        
        if 'objects' in output:
            for l in output['objects']:
                tmp = l['launchState']
                # ACCEPTING_ENTRIES
                # LAUNCH_CLOSED
                # NOT_ACCEPTING_ENTRIES
                return tmp
                # if not tmp in ('ACCEPTING_ENTRIES',
                #                'LAUNCH_CLOSED'):
                #     print(tmp)
                #     launched = Tr
                # else:
                #     print(tmp)
        return launched
    
    def get_user_details(self):
        # IDK how the upmId is obtained,
        # but I know that if I place something in the basket then it is saved
        # into the global variable.
        # So, I am going to place something into the basket, remove it.
        # Then check the sessionStorage variable.
        
        stage = 0
        while 1:
            try:
                if stage == 0:
                    # print('stage:',stage)
                    # Go to the in stock page
                    self.driver.get('https://www.nike.com/launch?s=in-stock')
                    stage += 1
                elif stage == 1:
                    # print('stage:',stage)
                    # Open the 6th item
                    tmp = w.driver.find_elements_by_tag_name('figure')
                    tmp[7].click()
                    stage += 1
                elif stage == 2:
                    # print('stage:',stage)
                    # Find all sizes
                    sizes = self.driver.find_elements_by_class_name('size')
                    stage += 1
                elif stage == 3:
                    # print('stage:',stage)
                    # Click on the first available size
                    c = 0
                    for size in sizes:
                        tmp = size.get_attribute('data-qa')
                        if not 'size-unavailable' in tmp:
                            size.click()
                            time.sleep(2)
                            c += 1
                            break
                    if c == 0:
                        stage -= 1
                    else:
                        stage += 1
                elif stage == 4:
                    # print('stage:',stage)
                    # Click on the "Add to Cart" button
                    buttons = self.driver.find_elements_by_tag_name('button')
                    for button in buttons:
                        if button.get_attribute('data-qa') == 'add-to-cart':
                            button.click()
                            time.sleep(2)
                            break
                    stage += 1
                elif stage == 5:
                     break
            except:
                time.sleep(1)
                pass
        stage = 0

        run = True
        while run:
            try:
                if stage == 0:
                    # Go to cart
                    self.driver.get('https://www.nike.com/cart')
                    stage += 1
                elif stage == 1:
                    c = 0
                    # Remove all items from the basket
                    buttons = self.driver.find_elements_by_tag_name('button')
                    for button in buttons:
                        if button.get_attribute('name') == 'remove-item-button':
                            if button.text != '':
                                c += 1
                                button.click()
                                time.sleep(1)
                                run = False
            except:
                time.sleep(1)
                pass
                        
        jj = json.loads(self.driver.execute_script('return sessionStorage["persist:user"]'))
        
        self.visitorId = eval(jj['visitorId'])
        self.upmId = eval(jj['upmId'])
        
        self.driver.get('https://www.nike.com/launch?s=upcoming')
        
    def find_tokens(self):
        iframes = self.driver.find_elements_by_tag_name('iframe')
        for frame in iframes:
            tmp = frame.get_attribute('src')
            if tmp == 'https://unite.nike.com/session.html':
                self.driver.switch_to.frame(frame)
                val = self.driver.execute_script('return localStorage')
                tmp = json.loads(val['com.nike.commerce.snkrs.web.credential'])
                self.token = tmp['access_token']
                self.driver.switch_to.default_content()
                
        # Find traceid
        r = self.s.get(self.product_url)
        self.traceid = r.headers['x-b3-traceid'] #x-request-id:
            
    def country_from_url(self,url):
        l = len('https://www.nike.com/')
        tmp = url[l:l+6]
        if 'launch' in tmp:
            self.country = 'US'
        else:
            self.country = tmp[:2].upper()
    def find_sizes(self,product_id):
        base_url = 'https://api.nike.com/merch/skus/v2/?filter=productId%28{}%29&filter=country%28{}%29'
        url = base_url.format(product_id,self.country)
        
        r = requests.get(url)
        resp = r.json()
        
        # Print available sizes
        print("Available sizes in {}".format(self.country))
        if 'objects' in resp.keys():
            items = resp['objects']
            for c,item in enumerate(items):
                print('{}: NikeSize {}, LocalSize {}'.format(c,
                            item['nikeSize'],
                            item['countrySpecifications'][0]['localizedSize']))
        choice = int(input('size val = '))
        self.sku_id = items[choice]['id']
    
    def place_order(self):
        # Need to place item into the basket first
        # There are lots of requests.. 
        # It seems only 3 are actually do the basket placement
        
        # visitorId nike['unite']['sessionData']["visitor"]
        url = "https://api.nike.com/buy/carts/v2/{}/NIKE/NIKECOM?modifiers=VALIDATELIMITS,VALIDATEAVAILABILITY"
        url = url.format(self.country)
        headers = {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "appid": "com.nike.commerce.nikedotcom.web",
            "authorization": "Bearer {}".format(self.token),
            "content-type": "application/json; charset=UTF-8",
            "origin": "https://www.nike.com",
            "referer": self.product_url,
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36",
            "x-b3-spanname": "CiCCart",
            "x-b3-traceid": self.traceid            
            }
        payload = [{"op":"add",
             "path":"/items",
             "value":{
                 "itemData":{
                     "url":self.product_url
                     },
                 "skuId":self.sku_id,
                 "quantity":1
                 }
             }
            ]
        self.s.headers = headers
        r=self.s.patch(url,data=json.dumps(payload))
        if r.status_code == 200:
            print("Success!")
        else:
            print(r.status_code)
            print(url)
            print(headers)
            print(payload)
            print(r.content)
            print('Something went wrong :(')
        pass
    
    def spam_and_buy(self):
        while 1:
            if (not '/launch?s=upcoming' in w.driver.current_url and
                    not '/launch?s=in-stock' in w.driver.current_url):
                self.product_url = self.driver.current_url
                self.country_from_url(self.driver.current_url)
                break
        
        w.s = self.create_session()
        ids = self.get_product_id_from_url()
        skuId = self.find_sizes(ids[0])
        self.find_tokens()
        
        for i in range(10):
            state = self.get_state(ids)
            print(state,datetime.now())
            if state == 'ACCEPTING_ENTRIES':
                # Launch, go for the pre-determined size
                w.place_order()
                w.driver.get('https://www.nike.com/checkout')
                break
            elif state in ('LAUNCH_CLOSED','LIVE'):
                # 1 hour after the launch, some sizes might not be available
                # Might want to check first
                w.place_order()
                w.driver.get('https://www.nike.com/checkout')
                break
            elif state == 'NOT_ACCEPTING_ENTRIES':
                # Item is not available yet
                pass
            time.sleep(1)

w = Worker()
# while 1:
#     if (not '/launch?s=upcoming' in w.driver.current_url and
#             not '/launch?s=in-stock' in w.driver.current_url):
#         w.product_url = w.driver.current_url
#         w.country_from_url(w.driver.current_url)
#         break
# w.get_user_details()
def do_stuff():
    w.s = w.create_session()
    ids = w.get_product_id_from_url()
    skuId = w.find_sizes(ids[0])
    w.find_tokens()
    w.place_order()
    w.driver.get('https://www.nike.com/checkout')

#do_stuff()
#w.driver.quit()
# print(w.get_state(ids))
        