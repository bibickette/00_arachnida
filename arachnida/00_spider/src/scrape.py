#!/usr/bin/env python3
import os
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from collections import deque

from src.ArgumentParser import ArgumentParser


class Scraper:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0"
    }
    EXTENSION_IMG = ["jpg", "jpeg", "png", "gif", "bmp"]

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
        
        self.print_image_info(image_extension, hostname, path, img_name)
        return full_path

    def download_image(self, response, url: str, image_extension: str) -> None:
        if not image_extension in self.EXTENSION_IMG :
            return
        full_path = self.build_full_path(url, image_extension)
        print(f"chemin de dl de limage complet : {full_path}")

        with open(full_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        self.nb_files_downloaded += 1
        print("File downloaded successfully.")
        
    def extract_links(self, url: str, response, depth : int) -> None :
        soup = BeautifulSoup(response.text, "html.parser")
        # print(f"soup : {soup}")
        supposedly_links = soup.find_all("a")  # get tous les urls
        iterator = 0
        for link in supposedly_links:
            link = link.get("href")
            if link:
                if not link.startswith("#"):
                    iterator += 1
                    link_to_visit = urljoin(url, link)
                    if not link_to_visit in self.links_to_visit and not link_to_visit in self.visited_links:
                        if depth - 1 >= 0 :
                            print(f"link url {iterator}: {link}")
                            self.links_to_visit[link_to_visit] = depth - 1
        
        supposedly_img = soup.find_all("img")  # get tous les src
        iterator = 0
        for src in supposedly_img:
            src = src.get("src")
            if src:
                img_to_visit = urljoin(url, src)
                if not img_to_visit in self.links_to_visit and not img_to_visit in self.visited_links:
                    if depth - 1 >= 0 :
                        print(f"image {iterator}: {src}")
                        self.links_to_visit[img_to_visit] = depth - 1
                iterator += 1
        # print(f"images found : {iterator}")
        print(f"links to visit found : {self.links_to_visit}")
        # print(f"total links to visit : {len(self.links_to_visit)}")
        print(
            f"number of links found : {len(supposedly_links)}\nnumber of images found : {len(supposedly_img)}"
        )

    def scrape(self, url, depth : int) -> None:
        if url in self.visited_links :
            return
        
        response = requests.get(url, headers=self.HEADERS, timeout=3)
        print(f"\n\nURL : {url} | Status code : {response.status_code} | Depth = {depth}\n")
        response.raise_for_status()
        
        content_type = response.headers.get("Content-type")
        print(f"content type : {content_type}")

        if "text/html" in content_type:
            self.extract_links(url, response, depth)
        
        elif "image/" in content_type:
            self.download_image(response, list(self.links_to_visit.keys())[0], content_type.split("/")[1])
            # self.download_image(response, self.links_to_visit[0], content_type.split("/")[1])
            # print(f"links to visit after download img: {self.links_to_visit}")
        self.visited_links.add(url)
        del self.links_to_visit[url]
        # self.links_to_visit.popleft()
        if len(self.links_to_visit) > 0 :
            print(f"next link to visit : {list(self.links_to_visit.keys())[0]}\n value = {self.links_to_visit.get(list(self.links_to_visit.keys())[0])}")
            self.scrape(list(self.links_to_visit.keys())[0], self.links_to_visit.get(list(self.links_to_visit.keys())[0]))