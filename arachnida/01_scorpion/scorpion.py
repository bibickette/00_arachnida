#!/usr/bin/env python3
import sys
from src.JPEGanalyzer import JPEGAnalyzer
import mimetypes

GREEN = "\033[32m"
RESET = "\033[0m"

def main() -> int:

    mime, _ = mimetypes.guess_type("img_extension/img_jpg.jpg")
    if mime != "image/jpeg":
        print(f"{GREEN}The file is not a JPEG image. Detected MIME type: {mime}{RESET}")
        return 1
    analyzer = JPEGAnalyzer()
    analyzer.analyze_image("img_extension/IMG_20260215_195801.jpg")

    return 0

if __name__ == "__main__":
    sys.exit(main()) #  raise SystemExit(main()) ; cest un equivalent pour return un code retour dans python