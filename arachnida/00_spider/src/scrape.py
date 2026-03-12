#!/usr/bin/env python3
import os
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from src.ArgumentParser import ArgumentParser

class Scraper:
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0'
    }
    EXTENSION_IMG = ["jpg", "jpeg", "png", "gif", "bmp"]

    def __init__(self, args: ArgumentParser) -> None:
        self.url = args.url
        self.depth = args.depth
        self.path = args.path
        

    def scrape(self, url) :

        response = requests.get(url, headers=Scraper.HEADERS)
        print(f"URL : {url} | Status code : {response.status_code}\n")
        response.raise_for_status()
        content_type = response.headers.get('Content-type')
        print(f"content type : {content_type}")
        # if "text/html" in content_type :
            # print(f"cest une page html")
        soup = BeautifulSoup(response.text, 'html.parser')
        # print(f"soup : {soup}")
        if "image/" in content_type :
            img_extension = content_type.split("/")[1]
            if img_extension in Scraper.EXTENSION_IMG :
                print(f"cest une image telechargeable : {img_extension}")
                # print(f"nom de limage : {url.split('/')[-1]}") # En Python, l’index -1 veut dire “le dernier élément” d’une liste (ou d’une chaîne).
                print(f"nom de limage : {os.path.basename(urlparse(url).path)}") # os.path.basename(path) renvoie le dernier élément d’un chemin (comme “nom de fichier”). urlparse(url).path renvoie uniquement le chemin de l’URL, sans le domaine ni les paramètres.
            return
        
        elif "text/" in content_type :  
            supposedly_links = soup.find_all('a') # get tous les urls
            supposedly_img = soup.find_all('img') # get tous les src
            print(f"number of links found : {len(supposedly_links)}\nnumber of images found : {len(supposedly_img)}")
            iterator = 0
            for link in supposedly_links :
                link = link.get('href')
                if link :
                    if not link.startswith("#") :
                        iterator += 1
                        # print(f"link url {iterator}: {link}")
                    # else :
                        # print(f"anchor so not a link : {link}")
            print(f"not anchor links found : {iterator}")
            iterator = 0
            image_urls = []

            for src in supposedly_img :
                src = src.get('src')
                if src :
                    print(f"image {iterator}: {src}")
                    image_urls.append(urljoin(url, src))
                    iterator += 1
            print(f"image urls found : {image_urls}")
            print(f"images found : {iterator}")