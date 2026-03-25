#!/usr/bin/env python3
import argparse
import sys
from src.JPEGanalyzer import JPEGAnalyzer
import mimetypes

RED = "\033[31m"
RESET = "\033[0m"

def init_arg_parse():
    parser = argparse.ArgumentParser(
        description="Analyse and extract metadata from file(s)"
    )
    parser.add_argument("files", nargs="+", help="One files or more to analyze")

    args = parser.parse_args()
    return args.files

def error(filename):
    print(f"{RED}The file '{filename}' is not a supported image format for analysis.{RESET}")

def main() -> int:

    files = init_arg_parse()
    print(f"files = {files}")
    mime_to_function = {"image/jpeg": JPEGAnalyzer.analyze_image, 
                        "image/png": error, 
                        "image/gif": error, 
                        "image/bmp": error}

    for file in files:
        mime, _ = mimetypes.guess_type(file)
        if mime not in mime_to_function:
            print(f"{RED}The file is not a supported image format. Detected MIME type: {mime}{RESET}")
            return 1
        mime_to_function[mime](file)

    return 0

if __name__ == "__main__":
    sys.exit(main()) #  raise SystemExit(main()) ; cest un equivalent pour return un code retour dans python