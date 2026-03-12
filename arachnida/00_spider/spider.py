#!/usr/bin/env python3
import sys
import requests

from src.ArgumentParser import ArgumentParser
from src.scrape import Scraper

def main() -> int:
    RED = "\033[31m"
    RESET = "\033[0m"
    try:
        args = ArgumentParser(sys.argv)
    except ValueError as e:
        print(f"Usage: spider.py -r [-l DEPTH] [-p PATH] URL\n\n{RED}Error : {e}{RESET}", file=sys.stderr)
        return 1
    
    try:
        Scraper(args).scrape(args.url)
        
    except KeyboardInterrupt:
        print(f"{RED}Scraping interrupted with CTRL+C.{RESET}")
        return 1
    except requests.exceptions.RequestException as e:
        print(f"{RED}Error fetching URL: {e}{RESET}")
        return 1
    
    
    args.print_args()
    return 0

if __name__ == "__main__":
    sys.exit(main()) #  raise SystemExit(main()) ; cest un equivalent pour return un code retour dans python