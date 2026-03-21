#!/usr/bin/env python3
import sys
import time

from src.ArgumentParser import ArgumentParser
from src.scrape import Scraper

def main() -> int:
    args = ArgumentParser().arg_check(sys.argv) 
    if args is None:
        return 1
    
    date = time.time()
    spider = Scraper(args)
    ret = spider.scrape()
    
    args.print_args()
    spider.print_total()
    print(f"\nTime taken for scraping : {(time.time() - date):.2f} seconds")
    
    return ret

if __name__ == "__main__":
    sys.exit(main()) #  raise SystemExit(main()) ; cest un equivalent pour return un code retour dans python