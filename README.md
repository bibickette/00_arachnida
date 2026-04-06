# Project presentation - `arachnida`
**Introduction**

This README is organized as follows:
- [Description](#description)
- [Repository layout](#repository-layout)
- [Setup Python environment](#setup-python-environment)
- [00 - Spider](#00---spider)
  - [Arguments](#arguments)
  - [Tools used](#tools-used)
  - [Scripts behavior](#scripts-behavior)
  - [Notes / limitations](#notes--limitations)
- [01 - Scorpion](#01---scorpion)
  - [Arguments](#arguments-1)
  - [Tools used](#tools-used-1)
  - [Scripts behavior](#scripts-behavior-1)
  - [Notes](#notes)
- [Using `arachnida`](#using-arachnida)
  - [How to use `spider`](#how-to-use-spider)
  - [How to use `scorpion`](#how-to-use-scorpion)
 
* * *

## Description

This project contains two exercises:

1. **Spider - Web scraping**  
   Crawl an HTML page (and optionally its linked pages depending on options), then **download images**.

2. **Scorpion - Image metadata analysis**  
   Analyze local image files (**BMP / PNG / JPEG / GIF**) and extract meaningful information such as:
   - **Basic file metadata** (path, size, timestamps, permissions)
   - **Image-level metadata** (format, dimensions, mode)
   - **Format-specific metadata** (headers / chunks / segments)

This repository follows a “small tools” approach: each exercise is a standalone CLI program with its own source folder and utilities.


* * *

## Repository layout

```
.
├── arachnida/
│   ├── 00_spider/
│   │   ├── spider.py
│   │   └── src/
│   │
│   └── 01_scorpion/
│       ├── scorpion.py
│       ├── src/
│       └── img_extension/
│           ├── bmp/
│           ├── gif/
│           ├── jpeg/
│           └── png/
│
├── docs/
│   ├── README_BMP.md
│   ├── README_PNG.md
│   ├── README_JPEG.md
│   └── README_GIF.md
│
├── README.md
└── requirements.txt
```

* * *

## Setup Python environment

*This project use Python **3.12+**.*

Before running the executables, create and activate a virtual environment :
1. Create the environment with : `python3 -m venv .venv`
2. Lauch the Python environment with : `source .venv/bin/activate`
3. Install dependencies with :  `pip install -r requirements.txt`
4. *List all the packages (optional) : `pip list`*
5. When finished, quit the environment with : `deactivate`

* * *

## 00 - Spider
### Arguments
- `-r`  
  Recursively downloads images from the URL and its linked pages.  
  If not specified, stays at **depth 0** (only the given page).

- `-r -l <N>`  
  Sets the maximum recursion depth.  
  If not specified, the default is **5**.

- `-p <PATH>`  
  Sets the output directory where downloaded files will be saved.  
  If not specified, `./data/` is used.
  
```bash
./spider.py [flags...] <url>
```

### Tools used

- **requests** : HTTP requests (GET) to fetch HTML pages (and potentially files)
- **BeautifulSoup (bs4)** : HTML parsing and extraction of `<img>` and links
- **urllib** : URL handling and path building (normalization, joining, safe filesystem paths)

### Scripts behavior
- Downloads images with the following extensions:
  - `jpg`, `jpeg`, `png`, `gif`, `bmp`
- Asks the user whether the crawler should **stay on the same hostname**
  (to avoid leaving the target domain).
- Uses up to **10 workers** with `ThreadPoolExecutor`.
- Handles `Ctrl+C` cleanly.

Tip for testing scraping:
- `https://webscraper.io/test-sites`

### Notes / limitations

- No built-in delay between requests: you may hit **HTTP 429 (Too Many Requests)** on some sites.
- Only downloads supported image extensions.
- Output structure depends on implementation details (paths built using `urllib`).


* * *

## 01 - Scorpion
### Arguments
Scorpion takes **one or more image files** as positional arguments.  
Some sample assets are already available in `arachnida/01_scorpion/img_extension/`, so you can test the program immediately without downloading anything.

```bash
./scorpion.py <file1> [file2 ...]
```

### Tools used
- **Pillow (PIL)**: open images and get high-level info (format, size, mode, `img.info`)
- Custom analyzers:
  - `BMPAnalyzer.py` : BMP headers, DIB types, palette, masks
  - `PNGAnalyzer.py` : PNG signature, IHDR, chunk listing (tEXt/iTXt, etc.)
  - `JPEGAnalyzer.py` : markers, SOF, APP segments, EXIF/GPS (when present)
  - `GIFAnalyzer.py` : GIF header, color tables, extensions (comments, looping)
 

### Scripts behavior
The script prints :
- **Basic file metadata** (name, size, timestamps, permissions)
- **Image-level metadata** (format, dimensions, mode)
- **Format-specific metadata**, for example:
  - PNG : IHDR fields + chunk list (sRGB, pHYs, iTXt, IDAT…)
  - JPEG : SOF (baseline/progressive), EXIF byte order, GPS IFD if present
  - GIF : version, canvas size, frame count/delays, comments if any
  - BMP : DIB type/size, bpp, compression, palette size, pixel offset, masks
  
### Notes
More informations about each formats :
1. BMP (`.bmp`)  *(see [BMP documentation](./docs/README_BMP.md))*
2. PNG (`.png`)  *(see [PNG documentation](./docs/README_PNG.md))*
3. JPEG (`.jpg`, `.jpeg`)  *(see [JPEG documentation](./docs/README_JPEG.md))*
4. GIF (`.gif`)  *(see [GIF documentation](./docs/README_GIF.md))*

* * *
# Using `arachnida`

1. Clone `00_arachnida` in a folder first  : `git clone git@github.com:bibickette/00_arachnida.git`
2. Go to the `00_arachnida` folder and install the Python environment *(see [setup environement](#setup-python-environment) for more details)*
3. Activate the environment with : `source .venv/bin/activate`

## How to use `spider`
4. Go to the folder first : `cd arachnida/00_spider`
5. Make the script executable : `chmod +x spider.py`
6. Run it as a program : `./spider.py [flags...] <url>` *(see [spider arguments](#arguments) for more details)*

## How to use `scorpion`
4. Go to the folder first : `cd arachnida/01_scorpion`
5. Make the script executable : `chmod +x scorpion.py`
6. Run it as a program : `./scorpion.py file1 file2 ...` *(see [scorpion arguments](#arguments-1) for more details)*


* * *
*Project validation date : TBD*
