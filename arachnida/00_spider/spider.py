#!/usr/bin/env python3
import sys
import time

from src.ArgumentParser import ArgumentParser
from src.scrape import Scraper

def main() -> int:
    RED = "\033[31m"
    RESET = "\033[0m"
    try:
        args = ArgumentParser(sys.argv)
    except ValueError as e:
        print(f"Usage: spider.py [-r] [-l DEPTH] [-p PATH] URL\n\n{RED}Error : {e}{RESET}", file=sys.stderr)
        return 1
    
    ret = 0
    
    date = time.time()
    try:
        spider = Scraper(args)
        spider.scrape()
    except KeyboardInterrupt:
        print(f"{RED}Scraping interrupted with CTRL+C.{RESET}")
        ret = 1
        
    spider.print_total()
    print(f"Time taken for scraping : {int(time.time() - date)} seconds")
    args.print_args()
    
    return ret

if __name__ == "__main__":
    sys.exit(main()) #  raise SystemExit(main()) ; cest un equivalent pour return un code retour dans python