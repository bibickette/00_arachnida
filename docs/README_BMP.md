# BMP (Bitmap) - Analyzer Documentation

*This document complements the **Scorpion** documentation. For project overview and usage instructions, see the main README [here](../README.md).*

---

## 1) What is a BMP file?

**BMP (Bitmap)** is a simple raster image format historically used on Windows.  
A BMP file typically stores:

- a **file header** (signature, file size, where pixels start),
- a **DIB header** (image width/height, color depth, compression, masks, color space),
- an optional **palette** and/or **bit masks**,
- the **pixel array** (raw image data), usually stored as scanlines with padding.

`BMPAnalyzer` focuses on **reading headers**, not decoding pixels.

### General structure (high-level)

```
┌─────────────────────────────────────┐
│ BMP File Header (14 bytes)          │ <-- always at the start of the file
│ (Signature, File size, Offset)      │
├─────────────────────────────────────┤
│ DIB Header (Info Header)            │ <-- begins at file offset 14 (0x0E)
│ (Width, Height, Colors...)          │
├─────────────────────────────────────┤
│ Color Table (Palette)               │
│ (Optional, mainly for <= 8bpp)      │
├─────────────────────────────────────┤
│ Pixel Data (Bitmap Data)            │ <-- starts at bfOffBits (Pixel Data Offset)
│ (The actual image pixels)           │
└─────────────────────────────────────┘
```

---

## 2) Endianness & primitive types

BMP is **little-endian**.

Typical `struct` formats:
1. `"<H"`: 2-byte unsigned (WORD)
2. `"<I"`: 4-byte unsigned (DWORD)
3. `"<i"`: 4-byte signed (LONG) : important for height (top-down vs bottom-up)

### Top-down vs bottom-up (scanline order)

In BMP files, the **pixel array always starts at** `bfOffBits`.  
The sign of the height field (in DIB headers where height is **signed**, i.e. `BITMAPINFOHEADER` and later) determines the **vertical order** of scanlines in the pixel array:

- **Bottom-up (`height > 0`)**  
  The *first* scanline stored in the file corresponds to the **bottom** row of the image.  
  To display the image correctly, the row order must be reversed when mapping file rows to image rows.

- **Top-down (`height < 0`)**  
  The *first* scanline stored in the file corresponds to the **top** row of the image.  
  The actual height is `abs(height)`.

Important:
- This does **not** move or reorder headers. Headers are always at the beginning of the file.
- It only affects **how to interpret the pixel array** (the image rows).
- `BITMAPCOREHEADER` uses an **unsigned** height (`bcHeight`), so it does not support the negative-height top-down convention.

---

## 3) BITMAPFILEHEADER (14 bytes)

This header identifies the BMP file and provides the pixel data offset.

| File Offset | Size | Field | Analyzer key | Notes |
|:---:|:---:|---|---|---|
| `0x00` | 2 | `bfType` | `BMP Signature` | Must be `BM` |
| `0x02` | 4 | `bfSize` | `File Size` | File size in bytes |
| `0x06` | 4 | `bfReserved1 + bfReserved2` | `Reserved` | `BMPAnalyzer` reads both reserved WORDs as one DWORD |
| `0x0A` | 4 | `bfOffBits` | `Pixel Data Offset` | Where the pixel array begins |
| `0x0E` | 4 | `biSize` | `Info Header Size` | DIB header size (12/40/108/124…) |

### DIB header type

`BMPAnalyzer` maps `biSize` to:

| Size | Header |
|:----:|--------|
| 12 | BITMAPCOREHEADER |
| 40 | BITMAPINFOHEADER |
| 108 | BITMAPV4HEADER |
| 124 | BITMAPV5HEADER |

---

## 4) BITMAPCOREHEADER case (biSize == 12)

| File Offset | Size | Field | Meaning |
|:----------:|:----:|---------|---|
| `0x0E` | 4 | `bcSize` | Size of this header (**12 bytes**) |
| `0x12` | 2 | `bcWidth` | Bitmap width in pixels (unsigned 16-bit) |
| `0x14` | 2 | `bcHeight` | Bitmap height in pixels (unsigned 16-bit) |
| `0x16` | 2 | `bcPlanes` | Number of color planes (**must be 1**) |
| `0x18` | 2 | `bcBitCount` | Bits per pixel (e.g., 1, 4, 8, 24) |

Note: With BITMAPCOREHEADER, the image is treated as **bottom-up**.

---

## 5) BITMAPINFOHEADER case (biSize >= 40)

When `info_header_size >= 40`, the analyzer reads these fields:

| File Offset | Size | Field | Meaning |
|:---:|:---:|---|---|
| `0x12` | 4 | `biWidth` | Image width (pixels) |
| `0x16` | 4 | `biHeight` | Signed height (pixels) |
| `0x1A` | 2 | `biPlanes` | Must be 1 |
| `0x1C` | 2 | `biBitCount` | Bits per pixel (bpp) |
| `0x1E` | 4 | `biCompression` | Compression method |
| `0x22` | 4 | `biSizeImage` | Image size (may be 0 for BI_RGB) |
| `0x26` | 4 | `biXPelsPerMeter` | X pixels per meter |
| `0x2A` | 4 | `biYPelsPerMeter` | Y pixels per meter |
| `0x2E` | 4 | `biClrUsed` | Colors used (palette entries) |
| `0x32` | 4 | `biClrImportant` | Important colors |

---

## 6) BITMAPV4HEADER case (biSize >= 108)

When `info_header_size >= 108`, `BMPAnalyzer` reads masks and color space fields.

### A) RGBA masks (file offset 0x36)

| File Offset | Size | Field |
|:-----------:|:----:|-------|
| `0x36` | 4 | Red Mask |
| `0x3A` | 4 | Green Mask |
| `0x3E` | 4 | Blue Mask |
| `0x42` | 4 | Alpha Mask |

### B) Color space type (file offset 0x46)

Common values `BMPAnalyzer` recognizes:

| Value (hex) | Name | Meaning |
|:----------:|------|---------|
| `0x00000000` | `LCS_CALIBRATED_RGB` | Endpoints and gamma values are provided in the header. |
| `0x73524742` | `LCS_sRGB` | The bitmap is in the sRGB color space. |
| `0x57696E20` | `LCS_WINDOWS_COLOR_SPACE` | The bitmap is in the system default color space (sRGB). |
| `0x4C494E4B` | `PROFILE_LINKED` | `bV5ProfileData` points to a profile filename (endpoints/gamma ignored). |
| `0x4D424544` | `PROFILE_EMBEDDED` | `bV5ProfileData` points to an embedded profile buffer (endpoints/gamma ignored). |

### C) Endpoints (CIEXYZTRIPLE)

`BMPAnalyzer` currently reads endpoints as **3 groups of 3 DWORDs**:

- Red endpoint at file offset `0x4A`
- Green endpoint at file offset `0x56`
- Blue endpoint at file offset `0x62`

And prints:
- `Endpoint Red: X:..., Y:..., Z:...`
- `Endpoint Green: ...`
- `Endpoint Blue: ...`

### D) Gamma values (file offset 0x6E)

`BMPAnalyzer` reads gamma values as **3 DWORDs**:

- Gamma Red: `0x6E`
- Gamma Green: `0x72`
- Gamma Blue: `0x76`

---

## 7) BITMAPV5HEADER case (biSize >= 124)

| File Offset | Size | Field | Analyzer key |
|------------:|-----:|------------------|-----------------|
| `0x7A` | 4 | `bV5Intent` | `Intent` |
| `0x7E` | 4 | `bV5ProfileData` | `Profile Data` |
| `0x82` | 4 | `bV5ProfileSize` | `Profile Size` |
| `0x86` | 4 | `bV5Reserved` | `Reserved (V5)` |

### Intent mapping (correct BMP V5 values)

`bV5Intent` is a DWORD and should be one of these values:

| Value | Value                     | Meaning                                                                                                      |
|------:|---------------------------|--------------------------------------------------------------------------------------------------------------|
|     1 | `LCS_GM_BUSINESS`         | Maintains saturation. Used for business charts and other situations in which undithered colors are required. |
|     2 | `LCS_GM_GRAPHICS`         | Maintains colorimetric match. Used for graphic designs and named colors.                                     |
|     4 | `LCS_GM_IMAGES`           | Maintains contrast. Used for photographs and natural images.                                                 |
|     8 | `LCS_GM_ABS_COLORIMETRIC` | Maintains the white point. Matches the colors to their nearest color in the destination gamut.               |

