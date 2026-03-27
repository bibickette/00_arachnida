#!/usr/bin/env python3
import argparse
import sys
import mimetypes

from src.JPEGanalyzer import JPEGAnalyzer
from src.PNGanalyzer import PNGAnalyzer

RED = "\033[31m"
RESET = "\033[0m"

def init_arg_parse():
    parser = argparse.ArgumentParser(
        description="Analyse and extract metadata from file(s)"
    )
    parser.add_argument("files", nargs="+", help="One file or more to analyze")

    args = parser.parse_args()
    return args.files

def error(filename: str, mime: str | None):
    print(f"{RED}===========================================================================")
    print(f"The {RESET}{filename}{RED} is not a supported image format. Detected MIME type: {RESET}{mime}{RED}")
    print(f"==========================================================================={RESET}")
    
def error(filename:str):
    print(f"{RED}not available yet for {RESET}{filename}{RED} {RESET}")
    

def main() -> int:

    files = init_arg_parse()
    print(f"files = {files}")
    mime_to_function = {"image/jpeg": JPEGAnalyzer.analyze_image, 
                        "image/png": PNGAnalyzer.analyze_image, 
                        "image/gif": error, 
                        "image/bmp": error}

    for file in files:
        mime, _ = mimetypes.guess_type(file)
        if mime not in mime_to_function:
            error(file, mime)
            continue
        mime_to_function[mime](file)

    return 0

if __name__ == "__main__":
    sys.exit(main()) #  raise SystemExit(main()) ; cest un equivalent pour return un code retour dans python