#!/usr/bin/env python3
from ast import pattern
from pydoc import text
import sys
import re

from bs4 import BeautifulSoup
import requests
from src.arg_checker import arg_check
# from src.get_requests import get_requests

def main() -> int:
    RED = "\033[31m"
    RESET = "\033[0m"
    try:
        args = arg_check(sys.argv)
    except ValueError as e:
        print(f"Usage: spider.py -r [-l DEPTH] [-p PATH] URL\n\n{RED}Error : {e}{RESET}", file=sys.stderr)
        return 1
    
    try :
        response = requests.get(args.url)
        print(f"URL : {args.url} | Status code : {response.status_code}\n")
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
            for img in supposedly_img :
                if img['src'] :
                    print(f"image html  : {img['src']}")
    
        elif "text/css" in content_type :
            comment_pattern = re.compile(r"/\*.*?\*/", re.DOTALL) # regex pour trouver les commentaires dans le css, le re.DOTALL permet de faire en sorte que le . puisse matcher les sauts de ligne sinon ne le match pas
            css_without_comments = comment_pattern.sub("", response.text) # on remplace les commentaires par une chaine vide
            pattern = re.compile(r"url\(([^)]+)\)", re.IGNORECASE) # cherche url(...) et ignore si c'est en majuscule ou minuscule
            # css_img_with_comments = pattern.findall(response.text)    
            # for img in css_img_with_comments :
            #     print(f"image with comments : {img}")
            css_img = pattern.findall(css_without_comments)
            for img in css_img :
                print(f"image css : {img}")
        
        
    except requests.exceptions.RequestException as e:
        print(f"{RED}Error fetching URL: {e}{RESET}")
        return 1

    print(f"\nlist of {args}\n")
    print("program exit successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main()) #  raise SystemExit(main()) ; cest un equivalent pour return un code retour dans python