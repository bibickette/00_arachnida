# JPEG — Analyzer Documentation

*This document complements the **Scorpion** documentation. For project overview and usage instructions, see the main README [here](../README.md).*

This document is a practical reference for `JPEGAnalyzer.py` in Scorpion.

> Key idea: JPEG is a sequence of **markers**. You iterate `0xFF xx` markers, parse segment lengths, and extract metadata from APP/SOF segments.

---

## 0) Endianness & types

- JPEG marker bytes are raw.
- Segment length fields are **big-endian** (2 bytes).
- EXIF content inside APP1 is a TIFF structure that can be little-endian or big-endian (specified inside the EXIF block).

---

## 1) Marker overview

All markers start with `0xFF`.

Common markers:

| Marker | Hex | Meaning |
|---|---:|---|
| SOI | FFD8 | Start of Image |
| EOI | FFD9 | End of Image |
| APP0 | FFE0 | JFIF |
| APP1 | FFE1 | EXIF and/or XMP |
| APP2 | FFE2 | ICC profile (often split) |
| DQT | FFDB | Quantization tables |
| DHT | FFC4 | Huffman tables |
| SOF0 | FFC0 | Baseline DCT frame header |
| SOF2 | FFC2 | Progressive DCT frame header |
| SOS | FFDA | Start of Scan (compressed data follows) |

---

## 2) Segment structure (most markers)

For most segments (APPn, DQT, SOF, DHT, COM, etc.):

```
FF xx  (marker)
00 LL  (2-byte length, big-endian; includes these 2 bytes)
...    (payload of length-2)
```

So payload length is:
- `seg_len - 2`

Special case:
- After **SOS**, the compressed entropy-coded data continues until EOI; it’s not broken into length-prefixed segments.

---

## 3) How to parse dimensions and encoding (SOF segments)

SOF payload typically contains:

| Offset in SOF payload | Size | Meaning |
|---:|---:|---|
| 0 | 1 | sample precision (bits per sample) |
| 1 | 2 | height (big-endian) |
| 3 | 2 | width (big-endian) |
| 5 | 1 | number of components |
| 6.. | 3 * components | component data |

Each component entry (3 bytes):
- component id
- sampling factors (hi nibble H, lo nibble V)
- quant table id

Scorpion can display:
- baseline/progressive (based on which SOF marker appears)
- width/height
- components count (1,3,4)
- subsampling derived from sampling factors (e.g., 4:2:0)

---

## 4) JFIF (APP0)

APP0 payload often begins with:
- ASCII `"JFIF\0"`

Contains:
- version
- density units
- X/Y density (DPI-ish)
- thumbnail info

Good fields for output:
- jfif_version
- dpi / density

---

## 5) EXIF (APP1) — structure

APP1 can contain EXIF:
- starts with ASCII: `Exif\0\0`

Then a TIFF header:

| TIFF Offset | Size | Field |
|---:|---:|---|
| 0 | 2 | byte order: `II` or `MM` |
| 2 | 2 | 0x002A |
| 4 | 4 | offset to 0th IFD |

IFDs (Image File Directories) contain entries:
- tag id (2)
- type (2)
- count (4)
- value or offset (4)

Important:
- If the value doesn’t fit in 4 bytes, the entry stores an **offset** to the actual data.

Common tags:
- Make/Model, DateTimeOriginal, Orientation
- GPSInfo pointer (leads to GPS IFD)

---

## 6) GPS IFD (EXIF)

GPS tags commonly used:
- LatitudeRef (N/S), Latitude (rationals)
- LongitudeRef (E/W), Longitude (rationals)
- GPSTimeStamp, GPSDateStamp
- ImgDirection

Analyzer output suggestions:
- print DMS tuples
- optionally compute decimal degrees

* * *

## 7) SOF (frame) fields
From SOF0/SOF2 you can extract:
- Encoding process (baseline/progressive)
- Bits per sample
- Image width/height
- Number of components (1 gray / 3 YCbCr / 4 CMYK)
- Sampling factors (subsampling)

---

## 8) ICC profile (APP2)

APP2 may contain ICC profile data, sometimes split across multiple APP2 segments.
If you don’t fully rebuild it, it’s still useful to show:
- ICC present (yes/no)
- total ICC bytes (sum)

---

## 9) Recommended analyzer output

- file signature SOI/EOI presence
- SOF: width, height, bits per sample, components, subsampling, baseline/progressive
- APP0 (JFIF) summary if present
- APP1 EXIF summary + GPS if present
- APP2 ICC presence if present
