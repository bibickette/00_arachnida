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

        self.file_downloaded = set()  # pour eviter de dl plusieurs fois la meme image
        self.nb_files_downloaded = 0
        self.nb_links_visited = 0
        self.links_to_visit = deque()
        self.visited_links = set()  # pour eviter de visiter plusieurs fois le meme lien

    def print_total(self) -> None:
        print(f"\nTotal links visited : {self.nb_links_visited}\nTotal files downloaded : {self.nb_files_downloaded}")

    def define_img_name(self, url: str, extension: str) -> str:
        return os.path.basename(urlparse(url).path) or f"image_without_name.{extension}"

    def build_full_path(self, url: str, image_extension: str) -> str:
        print(f"cest une image de type : {image_extension}")
        hostname = urlparse(url).hostname.strip("/")
        img_name = self.define_img_name(url, image_extension).strip("/")
        path = urlparse(url).path.replace(img_name, "").strip("/")
        print(f"nom de domaine/dossier : {hostname}")
        print(f"chemin sans nom : {path}")
        os.makedirs(os.path.join(self.path, hostname, path), exist_ok=True)  # creer les dossiers si ils n'existent pas deja, exist_ok=True evite de lever une exception si le dossier existe deja
        # print(f"nom de limage : {url.split('/')[-1]}") # En Python, l’index -1 veut dire “le dernier élément” d’une liste (ou d’une chaîne).
        print(f"nom : {img_name}")  # os.path.basename(path) renvoie le dernier élément d’un chemin (comme “nom de fichier”). urlparse(url).path renvoie uniquement le chemin de l’URL, sans le domaine ni les paramètres.
        full_path = os.path.join(self.path, hostname, path, img_name)  # joindre intelligement les parties du chemin pour créer un chemin complet

        return full_path

    def download_image(self, response, url: str, image_extension: str) -> None:
        if not image_extension in self.EXTENSION_IMG:
            return
        full_path = self.build_full_path(url, image_extension)
        print(f"chemin de dl de limage complet : {full_path}")

        if full_path in self.file_downloaded:
            print("File already downloaded, skipping.")
            return

        with open(full_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        self.file_downloaded.add(full_path)
        self.visited_links.add(url)
        self.nb_links_visited += 1
        if self.links_to_visit:
            self.links_to_visit.pop()
        self.nb_files_downloaded += 1
        print("File downloaded successfully.")

    def scrape(self, url) -> None:

        response = requests.get(url, headers=self.HEADERS)
        print(f"URL : {url} | Status code : {response.status_code}\n")
        response.raise_for_status()
        content_type = response.headers.get("Content-type")
        print(f"content type : {content_type}")

        if "text/html" in content_type:
            soup = BeautifulSoup(response.text, "html.parser")
            # print(f"soup : {soup}")
            supposedly_links = soup.find_all("a")  # get tous les urls
            supposedly_img = soup.find_all("img")  # get tous les src
            print(
                f"number of links found : {len(supposedly_links)}\nnumber of images found : {len(supposedly_img)}"
            )
            iterator = 0
            for link in supposedly_links:
                link = link.get("href")
                if link:
                    if not link.startswith("#"):
                        iterator += 1
                        # print(f"link url {iterator}: {link}")
                    # else :
                    # print(f"anchor so not a link : {link}")
            print(f"not anchor links found : {iterator}")
            iterator = 0
            image_urls = []

            for src in supposedly_img:
                src = src.get("src")
                if src:
                    # print(f"image {iterator}: {src}")
                    image_urls.append(urljoin(url, src))
                    iterator += 1
            print(f"image urls found : {image_urls}")
            print(f"images found : {iterator}")
            self.links_to_visit.appendleft(image_urls)
            print(f"links to visit : {self.links_to_visit}")

        response = requests.get(image_urls[0], headers=self.HEADERS)
        content_type = response.headers.get("Content-type")
        print(f"content type : {content_type}")
        if "image/" in content_type:
            self.download_image(response, image_urls[0], content_type.split("/")[1])
            print(f"links to visit after download img: {self.links_to_visit}")
            return
