#!/usr/bin/env python3
import os
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from src.ArgumentParser import ArgumentParser


class Scraper:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0"
    }
    EXTENSION_IMG = ["jpg", "jpeg", "png", "gif", "bmp"]
    GREEN = "\033[32m"
    RED = "\033[31m"
    RESET = "\033[0m"


    def __init__(self, args: ArgumentParser) -> None:
        self.url = args.url
        self.depth = args.depth
        self.path = args.path

        self.links_to_visit = dict() # dict pour stocker url : depth
        self.links_to_visit[self.url] = 0
        self.visited_links = set()  # pour eviter de visiter plusieurs fois le meme lien
        self.nb_files_downloaded = 0
        

    def print_image_info(self, extension : str, hostname : str, path :  str, img_name : str) ->  None :
        print(f"cest une image de type : {extension}")
        print(f"nom de domaine/dossier : {hostname}")
        print(f"chemin sans nom : {path}")
        print(f"nom : {img_name}")

        
    def print_total(self) -> None:
        print(f"\nTotal links visited : {len(self.visited_links)}")
        print(f"Total files downloaded : {self.nb_files_downloaded}")


    def define_img_name(self, url: str, extension: str) -> str:
        return os.path.basename(urlparse(url).path) or f"image_without_name.{extension}"

    def build_full_path(self, url: str, image_extension: str) -> str:
        hostname = urlparse(url).hostname.strip("/")
        img_name = self.define_img_name(url, image_extension).strip("/")
        path = urlparse(url).path.replace(img_name, "").strip("/")
        full_path = os.path.join(self.path, hostname, path, img_name)  # joindre intelligement les parties du chemin pour créer un chemin complet
        os.makedirs(os.path.join(self.path, hostname, path), exist_ok=True)  # creer les dossiers si ils n'existent pas deja, exist_ok=True evite de lever une exception si le dossier existe deja
        
        # self.print_image_info(image_extension, hostname, path, img_name)
        return full_path

    def download_image(self, response, url: str, image_extension: str) -> None:
        if not image_extension in self.EXTENSION_IMG :
            return
        full_path = self.build_full_path(url, image_extension)

        with open(full_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        self.nb_files_downloaded += 1
        print(f"{self.GREEN}File downloaded successfully : {full_path}{self.RESET}")
    
    
    def extract_from_balise(self, url: str, soup, depth : int, balise : str) -> None :
        supposedly_links = soup.find_all(balise)  # get tous les urls
        iterator = 0
        for link in supposedly_links:
            if balise == "a" :
                link = link.get("href") 
            else :
                link = link.get("src")
            if link:
                if not link.startswith("#"):
                    link_to_visit = urljoin(url, link)
                    if not link_to_visit in self.links_to_visit and not link_to_visit in self.visited_links:
                            # print(f"link url {iterator}: {link_to_visit}")
                            self.links_to_visit[link_to_visit] = depth - 1
                            iterator += 1
        if iterator != 0 :
            print(f"{self.GREEN}Number of new balise '{balise}' found = {iterator} {self.RESET}")


    def extract_links(self, url: str, response, depth : int) -> None :
        soup = BeautifulSoup(response.text, "html.parser")
        self.extract_from_balise(url, soup, depth, "img")
        self.extract_from_balise(url, soup, depth, "a")
            

    def scrape(self, url, depth : int) -> None:
        
        if url in self.visited_links :
            return
        try:
            print(f"Depth = {depth} | URL : {url}")
            response = requests.get(url, headers=self.HEADERS, timeout=3)
            response.raise_for_status()
            
            content_type = response.headers.get("Content-type")
            # print(f"content type : {content_type}")

            if "text/html" in content_type:
                if depth - 1 >= 0 :
                    self.extract_links(url, response, depth)
            
            elif "image/" in content_type:
                self.download_image(response, list(self.links_to_visit.keys())[0], content_type.split("/")[1])

        except requests.exceptions.RequestException as e:
            print(f"{self.RED}Error fetching URL: {e}{self.RESET}")

        self.visited_links.add(url)
        del self.links_to_visit[url]
        if len(self.links_to_visit) > 0 :
            # print(f"\n\nnext link to visit : {list(self.links_to_visit.keys())[0]}\n value = {self.links_to_visit.get(list(self.links_to_visit.keys())[0])}")
            self.scrape(list(self.links_to_visit.keys())[0], self.links_to_visit.get(list(self.links_to_visit.keys())[0]))