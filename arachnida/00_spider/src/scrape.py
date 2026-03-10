#!/usr/bin/env python3
from bs4 import BeautifulSoup
import requests
import re

def scrape(url) :
    RED = "\033[31m"
    RESET = "\033[0m"
    try :
        response = requests.get(url)
        print(f"URL : {url} | Status code : {response.status_code}\n")
        content_type = response.headers.get('Content-type')
        print(f"content type : {content_type}")
        # if "text/html" in content_type :
            # print(f"cest une page html")
        soup = BeautifulSoup(response.text, 'html.parser')
        if "text/html" in content_type :
            supposedly_links = soup.find_all(href=True) # get tous les urls
            supposedly_img = soup.find_all(src=True) # get tous les src
            for link in supposedly_links :
                if link['href'] :
                    print(f"link url : {link['href']}")
            for src in supposedly_img :
                if src['src'] :
                    print(f"image html  : {src['src']}")
    
        elif "text/css" in content_type :
            comment_pattern = re.compile(r"/\*.*?\*/", re.DOTALL) # regex pour trouver les commentaires dans le css, le re.DOTALL permet de faire en sorte que le . puisse matcher les sauts de ligne sinon ne le match pas
            css_without_comments = comment_pattern.sub("", response.text) # on remplace les commentaires par une chaine vide
            pattern = re.compile(r"url\(([^)]+)\)", re.IGNORECASE) # cherche url(...) et ignore si c'est en majuscule ou minuscule
            # css_img_with_comments = pattern.findall(response.text)    
            # for img in css_img_with_comments :
            #     print(f"image with comments : {img}")
            css_img = pattern.findall(css_without_comments)
            for img in css_img :
                print(f"image css : {img.strip('\'\" ')}") # strip pour enlever les espaces et les guillemets simples ou doubles
        
        
    except requests.exceptions.RequestException as e:
        print(f"{RED}Error fetching URL: {e}{RESET}")
        return 1