# BMP (Bitmap) — Analyzer Documentation

*This document complements the **Scorpion** documentation. For project overview and usage instructions, see the main README [here](../README.md).*

This document is meant to match what a `BMPAnalyzer` typically does in Scorpion: parse headers, compute palette size, locate pixel data, and display meaningful fields (offsets, sizes, values).

> Key idea: BMP is a **little-endian** container built around a 14-byte file header + a DIB header (variable size) + optional palette/bitfields + pixel array.

---

## 0) Endianness & primitive types

BMP uses **little-endian** integers.

Typical `struct` formats:
- `"<H"`: 2-byte unsigned (WORD)
- `"<I"`: 4-byte unsigned (DWORD)
- `"<i"`: 4-byte signed (LONG) — important for height

---

## 1) High-level file layout

```
0x0000  BITMAPFILEHEADER (14 bytes)
0x000E  DIB HEADER (biSize bytes) (variable size: 12/40/108/124…)
...     Optional: Color Table / Palette (RGBQUAD entries) (mainly for 1/4/8 bpp)
...     Optional: Bitfields masks (if BI_BITFIELDS / BI_ALPHABITFIELDS) 
bfOffBits  Pixel Array (scanlines with 4-byte padding)
```

The **only reliable** way to find pixel data is reading `bfOffBits` (Pixel Data Offset).

---

## 2) BITMAPFILEHEADER (14 bytes) — file offsets

| File Offset | Size | Field | Meaning |
|---:|---:|---|---|
| 0x00 | 2 | `bfType` | Signature: `"BM"` |
| 0x02 | 4 | `bfSize` | Total file size in bytes |
| 0x06 | 2 | `bfReserved1` | Reserved (should be 0) |
| 0x08 | 2 | `bfReserved2` | Reserved (should be 0) |
| 0x0A | 4 | `bfOffBits` | Offset to pixel array |

Example reads:
- signature: `data[0:2]`
- file size: `struct.unpack_from("<I", data, 0x02)[0]`
- pixel offset: `struct.unpack_from("<I", data, 0x0A)[0]`

---

## 3) DIB headers (start at file offset 0x0E)

At file offset `0x0E`, read:
- `biSize = DWORD` — tells DIB type and length.

### Common DIB types
- `biSize = 12`  → BITMAPCOREHEADER (legacy)
- `biSize = 40`  → BITMAPINFOHEADER (most common)
- `biSize = 108` → BITMAPV4HEADER
- `biSize = 124` → BITMAPV5HEADER

---

## 4) BITMAPINFOHEADER (biSize = 40) — DIB-relative offsets

DIB starts at `dib_off = 0x0E` (14). The offsets below are **relative to dib_off**.

| DIB Offset | File Offset | Size | Field | Notes |
|---:|---:|---:|---|---|
| 0 | 0x0E | 4 | `biSize` | = 40 |
| 4 | 0x12 | 4 | `biWidth` | width in pixels |
| 8 | 0x16 | 4 | `biHeight` | signed! negative => top-down |
| 12 | 0x1A | 2 | `biPlanes` | must be 1 |
| 14 | 0x1C | 2 | `biBitCount` | 1/4/8/16/24/32 |
| 16 | 0x1E | 4 | `biCompression` | BI_RGB, BI_RLE8, BI_BITFIELDS... |
| 20 | 0x22 | 4 | `biSizeImage` | may be 0 for BI_RGB |
| 24 | 0x26 | 4 | `biXPelsPerMeter` | density |
| 28 | 0x2A | 4 | `biYPelsPerMeter` | density |
| 32 | 0x2E | 4 | `biClrUsed` | palette entries used (if palettized) |
| 36 | 0x32 | 4 | `biClrImportant` | “important” colors |

### How to interpret biHeight
- If `biHeight > 0`: pixel array stored **bottom-up**
- If `biHeight < 0`: pixel array stored **top-down**; actual height is `abs(biHeight)`

---

## 5) Color table / palette (for 1/4/8 bpp)

### When is a palette present?
Usually if `biBitCount <= 8`.

### Number of palette entries
- If `biClrUsed != 0` → palette_entries = `biClrUsed`
- Else → palette_entries = `2 ** biBitCount`

### Entry format
Typically **RGBQUAD** (4 bytes):
- byte0: Blue
- byte1: Green
- byte2: Red
- byte3: Reserved (0)

Palette size:
- `palette_bytes = palette_entries * 4`

### Offset of palette
Palette begins immediately after the DIB header:
- `palette_off = dib_off + biSize`

---

## 6) Pixel array offset & row padding

### Pixel array offset
Always trust:
- `pixel_off = bfOffBits`

Sanity check:
- computed offset ≈ `14 + biSize + palette_bytes (+ masks if present)`

### Bytes per pixel (for direct-color formats)
- 24 bpp → 3 bytes/pixel (B, G, R)
- 32 bpp → 4 bytes/pixel (often B, G, R, A or unused)

### Row padding (important)
BMP aligns each row to a **4-byte boundary**.

Let:
- `bytes_per_pixel = biBitCount // 8` (for 16/24/32; for 1/4/8 it’s indexed bits)
- `row_unpadded = width * bytes_per_pixel`
- `row_size = (row_unpadded + 3) & ~3`

Total image bytes for uncompressed direct color:
- `row_size * height`

---

## 7) BI_BITFIELDS & masks (16/32 bpp)

If `biCompression` is:
- `BI_BITFIELDS` (3) or `BI_ALPHABITFIELDS` (6)

Then masks define how to extract R/G/B/(A) from pixel values.

### Masks location rules
- For V4/V5 headers (biSize >= 108): masks are in the header (see below).
- For BITMAPINFOHEADER (biSize=40) + BI_BITFIELDS: masks are stored **immediately after** the 40-byte header (3 DWORD masks, plus optional alpha).

### Extracting channels (concept)
For a pixel integer `px`:
- `raw = (px & mask) >> shift`
Where:
- `shift` = number of trailing zeros in mask
- bits per channel = popcount(mask)

---

## 8) BITMAPV4HEADER (biSize = 108) — added offsets

V4 includes INFOHEADER (40) + masks + colorspace fields.

| DIB Offset | Size | Field |
|---:|---:|---|
| 40 | 4 | `bV4RedMask` |
| 44 | 4 | `bV4GreenMask` |
| 48 | 4 | `bV4BlueMask` |
| 52 | 4 | `bV4AlphaMask` |
| 56 | 4 | `bV4CSType` |
| 60 | 36 | `bV4Endpoints` (CIEXYZTRIPLE) |
| 96 | 4 | `bV4GammaRed` |
| 100 | 4 | `bV4GammaGreen` |
| 104 | 4 | `bV4GammaBlue` |

Notes:
- `bV4Endpoints` = 3 CIEXYZ structures (R, G, B), each CIEXYZ = 3 signed LONG (often fixed-point 16.16).
- For many files, endpoints/gamma are 0 if using sRGB.

---

## 9) BITMAPV5HEADER (biSize = 124) — added offsets

V5 includes V4 (108) plus ICC/profile-related fields:

| DIB Offset | Size | Field |
|---:|---:|---|
| 108 | 4 | `bV5Intent` |
| 112 | 4 | `bV5ProfileData` |
| 116 | 4 | `bV5ProfileSize` |
| 120 | 4 | `bV5Reserved` |

### bV5Intent values (rendering intent)
- 0: Perceptual
- 1: Relative Colorimetric
- 2: Saturation
- 3: Absolute Colorimetric

---

## 10) What Scorpion should print (recommended)

- Signature, file size, pixel offset
- DIB header size + DIB type (CORE/INFO/V4/V5)
- width, height (and top-down vs bottom-up)
- planes, bpp, compression
- x/y pixels per meter (and optional DPI conversion)
- palette: present? number of entries? (for <=8 bpp)
- masks: only if BI_BITFIELDS or header is V4/V5 and bpp is 16/32
- profile info (V5): intent + profile size presence

---

## 11) Quick DPI conversion
If `x_ppm` is pixels-per-meter:
- `dpi ≈ x_ppm * 0.0254`
