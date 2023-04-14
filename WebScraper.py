#!/bin/Python3
#! Created by : Barath
#! Tool name : WebScraper
#! verison :  2.0

# usage : python3 WebScraper.py -u http://example.com

# Packages import
import requests
from bs4 import BeautifulSoup
import argparse
import re

                             
# Get url input has http://www.example.com or https://www.example.com
def Banner():
    print("""

                     #   ,                        %                    
                        ,                          @    (              
                  (.   .(                           @    @             
                 &*   .@                            &&    @            
                @@    @.                             @/   /@           
               &@    @@                              @@    @@          
              ,@@   #@&                              ,@@   *@#         
              @@.   @@&                              .@@#   @@         
             ,@@    .@@%#//(((/#@& @    @ ,@@.*#####&@@#    @@&        
             @@@       .&@@@@@@@,@@@@@@@@@@.@@@@@@@@*       &@@        
             @@@@@@@@.           @@@@@@@@@@            @@@@@@@@        
                .        @@@&*. (@@@@@@@@@@@  ,/@@@/        *          
                      @@@    *@@, @@@@@@@@  @@%    @@@                 
                   @@@    @@@@   @@@@@@@@@@   &@@@    @@@              
                @@@       @@@.   @@@@@@@@@@    @@@       @@@*          
          @(&@@@.         @@@*    @@@@@@@@#    @@@          @@@@*%     
          @@@&            @@@.    &@@@@@@@     @@@            *@@@     
          %@@             @@@      @@@@@@      @@@             @@@     
          ,@@             @@@       @@@@/      @@@             @@@     
           @@,            &@@        @@(       @@@             @@      
           %@&            ,@@                  @@@            ,@@      
            @@             @@                  @@(            @@       
            .@,            @@.                 @@             @%       
             *@            (@/                 @@            %@        
              (#            @@                *@,            @         
               *.           #@                @@            @          
                .            @/               @            %           
                              @              @,           /            
                              .&            .(                         
                                (           /                          
                                 &        .                            
                             
                                 WebScraper
                                 Version 2.0
                        
             usage : python3 WebScraper.py -u http://example.com \n""")
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", required=True ,help="Get a url")
    args = parser.parse_args()
    url = args.url
    if url != "None":
        
        input_check = re.search("http*.://.*", url)
        if (input_check):
            Banner()
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
                        status = requests.get(path)
                        status_code = status.status_code
                        print("[+]", path ,"\t[", status_code,"]")
                    else:
                        f_url = url+path
                        status = requests.get(f_url)
                        status_code = status.status_code
                        print("[+]", f_url , "\t[", status_code,"]")
        else:
            print("[-] Check your input of url !!!")
    else:
        print("[-] Try it again! \n usage : python3 WebScraper.py -u http://example.com")