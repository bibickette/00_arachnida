#!/usr/bin/env python3
import argparse
import sys
import mimetypes

from src.JPEGAnalyzer import JPEGAnalyzer
from src.PNGAnalyzer import PNGAnalyzer
from src.GIFAnalyzer import GIFAnalyzer
from src.BMPAnalyzer import BMPAnalyzer
from src.Color import Color


def main() -> int:
    def init_arg_parse():
        parser = argparse.ArgumentParser(
            description="Analyse and extract metadata from file(s)"
        )
        parser.add_argument("files", nargs="+", help="One file or more to analyze")

        args = parser.parse_args()
        return args.files

    def error(filename: str, mime: str | None):
        print(f"{Color.RED}===========================================================================")
        print(f"The {Color.RESET}{filename}{Color.RED} is not a supported image format. Detected MIME type: {Color.RESET}{mime}{Color.RED}")
        print(f"==========================================================================={Color.RESET}")

    files = init_arg_parse()
    # print(f"files = {files}")
    mime_to_function = {"image/jpeg": JPEGAnalyzer.analyze_image, 
                        "image/png": PNGAnalyzer.analyze_image, 
                        "image/gif": GIFAnalyzer.analyze_image, 
                        "image/bmp": BMPAnalyzer.analyze_image}

    for file in files:
        mime, _ = mimetypes.guess_type(file)
        if mime not in mime_to_function:
            error(file, mime)
            continue
        print("\n===========================================================================")
        print("===========================================================================")
        print(f"Extract Metadata from {Color.GREEN}{mime.split('/')[-1].upper()}{Color.RESET} file -> {file}")
        print("===========================================================================\n")
        mime_to_function[mime](file)

    return 0

if __name__ == "__main__":
    sys.exit(main()) #  raise SystemExit(main()) ; cest un equivalent pour return un code retour dans python
    