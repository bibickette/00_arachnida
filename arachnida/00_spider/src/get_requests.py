#!/usr/bin/env python3
import requests

def get_requests(args) :
    try :
        response = requests.get(args.url)
        print(f"URL : {args.url} | Status code : {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")