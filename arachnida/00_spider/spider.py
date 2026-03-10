#!/usr/bin/env python3
import sys

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
        print(f"URL : {args.url} | Status code : {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"{RED}Error fetching URL: {e}{RESET}")
        return 1

    print(f"\nlist of {args}\n")
    print("program exit successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main()) #  raise SystemExit(main()) ; cest un equivalent pour return un code retour dans python