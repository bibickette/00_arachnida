#!/usr/bin/env python3
import os
import sys
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
    YELLOW = "\033[33m"
    RESET = "\033[0m"


    def __init__(self, args: ArgumentParser) -> None:
        self.recursive = args.recursive
        self.url = args.url
        self.depth = args.depth
        self.path = args.path
        
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

        self.links_to_visit = dict() # dict pour stocker url : depth
        self.links_to_visit[self.url] = self.depth
        self.visited_links = set()  # pour eviter de visiter plusieurs fois le meme lien
        
        self.image_to_download = set() # pour stocker les urls des images a dl
        self.img_found = 0
        self.nb_files_downloaded = 0
        

    def print_image_info(self, extension : str, hostname : str, path :  str, img_name : str) ->  None :
        print(f"cest une image de type : {extension}")
        print(f"nom de domaine/dossier : {hostname}")
        print(f"chemin sans nom : {path}")
        print(f"nom : {img_name}")

        
    def print_total(self) -> None:
        print(f"\nTotal links visited : {len(self.visited_links)}")
        print(f"Total images found : {self.img_found}")
        print(f"Total files downloaded : {self.nb_files_downloaded}")

    # ========================== DOWNLOAD IMAGES ==========================
    
    def define_img_name(self, url: str, extension: str) -> str:
        return os.path.basename(urlparse(url).path) or f"image_without_name.{extension}"


    def build_full_path(self, url: str, image_extension: str) -> str:
        hostname = urlparse(url).hostname.strip("/")
        img_name = self.define_img_name(url, image_extension).strip("/")
        path = urlparse(url).path.replace(img_name, "").strip("/")
        full_path = os.path.join(self.path, hostname, path, img_name)  # joindre intelligement les parties du chemin pour créer un chemin complet
        if os.path.exists(full_path):
            raise ValueError(f"Skipping download, file already exists : {full_path}")
        os.makedirs(os.path.join(self.path, hostname, path), exist_ok=True)  # creer les dossiers si ils n'existent pas deja, exist_ok=True evite de lever une exception si le dossier existe deja
        # self.print_image_info(image_extension, hostname, path, img_name)
        return full_path


    def write_image(self, response, url: str, image_extension: str) -> None:
        full_path = self.build_full_path(url, image_extension)
        with open(full_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        self.nb_files_downloaded += 1
        print(f"{self.GREEN}Download success : {full_path}{self.RESET}")       


    def download_images(self) -> None:
        print(f"{self.GREEN}Start downloading images.{self.RESET}")
        for img_url in self.image_to_download:
            try:
                response = self.session.get(img_url, stream=True, timeout=3)
                response.raise_for_status()
                content_type = response.headers.get("Content-Type")
                if "image/" in content_type:
                    extension = content_type.split("/")[-1]
                    if extension in self.EXTENSION_IMG :
                        self.write_image(response, img_url, extension)
                    else :
                        raise ValueError(f"{self.RED}Unsupported image format: {extension}{self.RESET}")
            except requests.exceptions.RequestException as e:
                print(f"{self.RED}Error downloading image: {e}{self.RESET}", file=sys.stderr)
            except ValueError as e:
                print(f"{self.YELLOW}Warning : {e}{self.RESET}", file=sys.stderr)
    
    # ========================== GET ALL URLS ==========================

    def extract_all_images(self, url: str, soup) -> None :
        supposedly_imgs = soup.find_all("img")  # get tous les urls
        iterator = 0
        for img in supposedly_imgs:
            img = img.get("src")
            if img:
                img_to_visit = urljoin(url, img)
                if not img_to_visit in self.image_to_download:
                    self.image_to_download.add(img_to_visit)
                    self.img_found += 1
                    iterator += 1
        if iterator != 0 :
            print(f"{self.GREEN}Number of new images found = {iterator} {self.RESET}")


    def extract_all_links(self, url: str, soup, depth : int) -> None :
        supposedly_links = soup.find_all("a")  # get tous les urls
        iterator = 0
        for link in supposedly_links:
            link = link.get("href") 
            if link:
                if not link.startswith("#"):
                    link_to_visit = urljoin(url, link)
                    if not link_to_visit in self.links_to_visit and not link_to_visit in self.visited_links:
                        self.links_to_visit[link_to_visit] = depth
                        iterator += 1
        if iterator != 0 :
            print(f"{self.GREEN}Number of new links found = {iterator} {self.RESET}")
       
            
    def extract_url(self, url: str, response, depth : int) -> None :
        soup = BeautifulSoup(response.text, "html.parser")
        self.extract_all_images(url, soup)
        if depth >= 0 and self.recursive:
            self.extract_all_links(url, soup, depth)
         
            
    def crawl_url(self, url: str, depth : int) -> None:
        while(url) :
            try:
                print(f"Depth = {depth} | URL : {url}")
                response = self.session.get(url, stream=True, timeout=3)
                response.raise_for_status()
                
                content_type = response.headers.get("Content-Type")
                if "text/html" in content_type:
                    self.extract_url(url, response, depth - 1)
                
            except requests.exceptions.RequestException as e:
                print(f"{self.RED}Error fetching URL: {e}{self.RESET}", file=sys.stderr)
            except ValueError as e:
                print(f"{self.YELLOW}Warning : {e}{self.RESET}", file=sys.stderr)

            self.visited_links.add(url)
            del self.links_to_visit[url]
            if len(self.links_to_visit) > 0 : 
                url = next(iter(self.links_to_visit))
                depth = self.links_to_visit[url]
            else :
                url = None


    def scrape(self) -> None:
        try:
            self.crawl_url(self.url, self.depth)
            print(f"\n{self.GREEN}====== Crawling completed. ======{self.RESET}\n")
            if self.img_found == 0:
                print(f"{self.YELLOW}No images found to download.{self.RESET}")
                return
            print(f"{self.YELLOW}Do you want to download {self.img_found} images? [y/n] {self.RESET}", end="")
            input_user = input().strip().lower()
            if input_user != "y":
                print(f"{self.YELLOW}Download cancelled by user.{self.RESET}")
                return
            self.download_images()
        except KeyboardInterrupt:
            print(f"{self.RED}Scraping interrupted with CTRL+C.{self.RESET}")
            return 1
        return 0
    