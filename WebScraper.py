#!/bin/Python3
#! Created by : Barath
#! Tool name : WebScraper
#! verison :  1.0

# usage : python3 WebScraper.py

# Packages import
import requests
from bs4 import BeautifulSoup
import re

# Get url input has http://www.example.com or https://www.example.com
url = input("[+] Enter the url (eg: http://www.example.com or https://www.example.com):")
input_check = re.search("http*.://.*", url)
if (input_check):
    req = requests.get(url)
    cont = req.content
    soup = BeautifulSoup(cont, 'html.parser')
    atag = soup.find_all('a')
    
    # List all href attributes
    for links in atag:
        if (links.get('href') != '#'):
            path = str(links.get('href'))
            av_links = re.search("http", path)
            if (av_links):
                print(path)
            else:
                print(url+path)
else:
    print("[-] Check your input of url !!!")