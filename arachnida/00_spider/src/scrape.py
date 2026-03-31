import os
import sys
import threading
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor
from queue import Empty, Queue

from src.ArgumentParser import ArgumentParser

class Scraper:
    HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0"
    }
    EXTENSION_IMG = ["jpg", "jpeg", "png", "gif", "bmp"]
    MAX_WORKER = 10
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    RESET = "\033[0m"


    def __init__(self, args: ArgumentParser) -> None:
        self.recursive = args.recursive
        self.url = args.url
        if not self.recursive:
            self.depth = 0 # si pas recursive, on met la profondeur a 0 pour ne pas visiter les liens trouvés
        else :
            self.depth = args.depth
        self.path = args.path
        
        self.stay_on_same_hostname = True
        self.hostname = None # spider stay at the same hostname
        
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

        self.queue = Queue() # conserve les liens
        self.queue.put((self.url, self.depth))
        
        self.visited_lock = threading.Lock()
        self.visited_links = set()  # pour eviter de visiter plusieurs fois le meme lien
        
        self.img_found_lock = threading.Lock()
        self.img_found = 0
        
        self.nb_files_downloaded_lock = threading.Lock()
        self.nb_files_downloaded = 0
        
        self.stop_event = threading.Event() # pour signaler aux threads de s'arrêter en cas d'interruption (CTRL+C)
        
    # ========================== PRINT ==========================
        

    def print_image_info(self, extension : str, path :  str, img_name : str) ->  None :
        print(f"cest une image de type : {extension}")
        print(f"nom de domaine/dossier : {self.hostname}")
        print(f"chemin sans nom : {path}")
        print(f"nom : {img_name}")

        
    def print_total(self) -> None:
        print(f"\nTotal links visited : {len(self.visited_links)}")
        print(f"Total images visited : {self.img_found}")
        print(f"Total files downloaded : {self.nb_files_downloaded}")
        print(f"hostname : {self.hostname}")
        
        
        
    # ========================== UTILS ==========================
        
    def empty_queue(self) -> None:
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except Empty:
                break
            
    # ========================== DOWNLOAD IMAGES ==========================
    
    def define_img_name(self, url: str, extension: str) -> str:
        return os.path.basename(urlparse(url).path) or f"image_without_name.{extension}"


    def build_full_path(self, url: str, image_extension: str) -> str:
        img_name = self.define_img_name(url, image_extension).strip("/")
        path = urlparse(url).path.replace(img_name, "").strip("/")
        full_path = os.path.join(self.path, self.hostname, path, img_name)  # joindre intelligement les parties du chemin pour créer un chemin complet
        if os.path.exists(full_path):
            print(f"{self.YELLOW}Skipping download, file already exists : {full_path}{self.RESET}")
            return None
        os.makedirs(os.path.join(self.path, self.hostname, path), exist_ok=True)  # creer les dossiers si ils n'existent pas deja, exist_ok=True evite de lever une exception si le dossier existe deja
        # self.print_image_info(image_extension, path, img_name)
        return full_path


    def write_image(self, response, url: str, image_extension: str) -> None:
        full_path = self.build_full_path(url, image_extension)
        if full_path is None:
            return
        with open(full_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        with self.nb_files_downloaded_lock:
            self.nb_files_downloaded += 1
        print(f"{self.GREEN}Download success : {full_path}{self.RESET}")       


    # ========================== EXTRACT FROM SOUP : URL/IMG ==========================

    def extract_all_images(self, url: str, soup, depth: int) -> None :
        supposedly_imgs = soup.find_all("img")  # get tous les urls
        iterator = 0
        for img in supposedly_imgs:
            img = img.get("src")
            if not img:
                continue
            img_to_visit = urljoin(url, img)
            img_hostname = urlparse(img_to_visit).hostname
            if img_hostname is None:
                continue
            if self.stay_on_same_hostname and img_hostname.strip("/") != self.hostname:
                continue
            with self.visited_lock:
                if not img_to_visit in self.visited_links:
                    self.queue.put((img_to_visit, depth))
                    iterator += 1
        if iterator != 0 :
            print(f"{self.GREEN}Number of new images found = {iterator} {self.RESET}")


    def extract_all_links(self, url: str, soup, depth : int) -> None :
        supposedly_links = soup.find_all("a")  # get tous les urls
        iterator = 0
        for link in supposedly_links:
            link = link.get("href") 
            if not link:
                continue
            if not link.startswith("#"):
                link_to_visit = urljoin(url, link)
                link_hostname = urlparse(link_to_visit).hostname
                if link_hostname is None:
                    continue
                if self.stay_on_same_hostname and link_hostname.strip("/") != self.hostname:
                    continue
                with self.visited_lock:
                    if not link_to_visit in self.visited_links:
                        self.queue.put((link_to_visit, depth))
                        iterator += 1
        if iterator != 0 :
            print(f"{self.GREEN}Number of new links found = {iterator} {self.RESET}")
       
            
    def extract_from_soup(self, url: str, response, depth : int) -> None :
        soup = BeautifulSoup(response.text, "html.parser")
        self.extract_all_images(url, soup, depth)
        if depth - 1 >= 0 and self.recursive:
            self.extract_all_links(url, soup, depth - 1)


    def process_url(self, response, url: str, depth: int) -> None:
        print(f"Depth = {depth} | URL : {url}")
        content_type = response.headers.get("Content-Type")
        if "text/html" in content_type:
            self.extract_from_soup(url, response, depth)
        elif "image/" in content_type:
            extension = content_type.split("/")[1]
            with self.img_found_lock:
                self.img_found += 1
            if extension in self.EXTENSION_IMG :
                self.write_image(response, url, extension)
            else :
                print(f"{self.RED}Unsupported image format: {extension}{self.RESET}")
    
    
    # ========================== ASK USER PREFERENCES ==========================
        
    def ask_user_preferences(self) -> int:
        try:
            print(f"Do you want to stay on the same hostname ? (y/n) : ", end="")
            choice = input().strip().lower()
            while choice != "y" and choice != "n":
                print(f"Invalid choice. Please enter 'y' or 'n': ", end="")
                choice = input().strip().lower()
            if choice == "n":
                self.stay_on_same_hostname = False # si on ne veut pas rester sur le meme hostname
            else:
                self.hostname = urlparse(self.url).hostname
                if self.hostname is None:
                    print(f"{self.RED}Invalid URL provided, cannot determine hostname. Exiting.{self.RESET}")
                    return 1
                self.hostname = self.hostname.strip("/")
        except KeyboardInterrupt:
            print(f"{self.RED}Scraping interrupted with CTRL+C before started.{self.RESET}")
            return 1
        return 0
    
    
    # ========================== SCRAPER FUNCTION ==========================
                        
    def worker(self) -> None:
        while(not self.stop_event.is_set()) :
            try:
                url, depth = self.queue.get(timeout=5) # quand on get il est automatiquement retiré de la queue, timeout pour éviter de rester bloqué indéfiniment si la queue est vide
            except Empty:
                self.queue.task_done()
                return
            
            try:
                with self.visited_lock:
                    if url in self.visited_links:
                        # print(f"{self.YELLOW}Skipping already visited URL: {url}{self.RESET}")
                        continue
                    self.visited_links.add(url)
                response = self.session.get(url, stream=True, timeout=5)
                response.raise_for_status()
                self.process_url(response, url, depth)
            except requests.exceptions.RequestException as e:
                print(f"{self.RED}Error fetching URL: {e}{self.RESET}", file=sys.stderr)
            except Exception as e:
                # attrape le reste : AttributeError, TypeError, etc.
                print(f"{self.RED}Unexpected error on {url}: {type(e).__name__}: {e}{self.RESET}", file=sys.stderr)
            finally:
                if response is not None:
                    response.close()
                self.queue.task_done() # indique que la tache est terminée pour le lien traité
    
            
    def launch_threads(self) -> int:
        try:
            with ThreadPoolExecutor(max_workers=self.MAX_WORKER) as executor:
                for _ in range(self.MAX_WORKER):
                    executor.submit(self.worker)
                self.queue.join()
        except KeyboardInterrupt:
            print(f"{self.RED}Scraping interrupted with CTRL+C.{self.RESET}")
            self.stop_event.set()
            self.empty_queue()
            return 1
        return 0
        
    # ========================== MAIN FUNCTION ==========================
    
    def scrape(self) -> int:
        ret = self.ask_user_preferences()
        if ret != 0:
            return ret
        
        return self.launch_threads()
