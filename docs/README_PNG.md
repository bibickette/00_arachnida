# PNG — Analyzer Documentation

*This document complements the **Scorpion** documentation. For project overview and usage instructions, see the main README [here](../README.md).*

This document is a practical reference for `PNGAnalyzer.py` in Scorpion.

> Key idea: PNG is chunk-based. You read the 8-byte signature, then iterate chunks:
> `Length (4) + Type (4) + Data (Length) + CRC (4)`.

---

## 0) Endianness & types

PNG uses **big-endian** for:
- chunk Length (4 bytes)
- IHDR width/height (4 bytes each)
- CRC (4 bytes)

Use:
- `int.from_bytes(..., "big")`

---

## 1) PNG signature (8 bytes)

At file offset `0x00`:
- `89 50 4E 47 0D 0A 1A 0A`

If it doesn’t match, it’s not a valid PNG.

---

## 2) Chunk structure (repeats until IEND)

Each chunk:

| Part | Size | Description |
|---|---:|---|
| Length | 4 | number of bytes in Data |
| Type | 4 | ASCII name (e.g. `IHDR`, `IDAT`) |
| Data | Length | payload |
| CRC | 4 | CRC-32(Type + Data) |

So the cursor moves by:
- `12 + length`

---

## 3) Essential chunks

### IHDR (must be first)
Chunk type: `IHDR`  
Data length: 13 bytes

| IHDR Data Offset | Size | Field |
|---:|---:|---|
| 0 | 4 | width (big-endian) |
| 4 | 4 | height (big-endian) |
| 8 | 1 | bit depth |
| 9 | 1 | color type |
| 10 | 1 | compression method (0 = deflate) |
| 11 | 1 | filter method (0 = adaptive) |
| 12 | 1 | interlace method (0 none, 1 Adam7) |

Common color types:
- 0: grayscale
- 2: truecolor (RGB)
- 3: indexed-color (palette)
- 4: grayscale + alpha
- 6: truecolor + alpha (RGBA)

### IDAT (one or many)
Holds the compressed image stream.
- If multiple IDAT chunks exist, they **must be consecutive**.
- The complete stream is `b"".join(all_idat_data)`.

### IEND (must be last)
Signals end of PNG.
- Data length is 0.

---

## 4) CRC (chunk integrity)

CRC is a 32-bit checksum stored per chunk.

It is computed over:
- `Type + Data`

Python validation:
```python
import zlib
crc_computed = zlib.crc32(chunk_type_bytes + chunk_data) & 0xffffffff
```

In Scorpion, you can optionally print:
- stored CRC
- computed CRC
- valid/invalid

---

## 5) Decoding image data (IDAT) — high level
Even if your analyzer doesn’t fully reconstruct pixels, it’s important to understand the pipeline:

1. Concatenate `IDAT` payloads
2. `zlib.decompress()` → filtered scanlines
3. Each scanline begins with **one filter byte** (0..4)
4. Unfilter scanlines using prior row (filter algorithms)

Filter types:
- 0 None
- 1 Sub
- 2 Up
- 3 Average
- 4 Paeth

---

## 6) Useful metadata chunks to recognize

Scorpion can list chunk presence and/or decode some:

- `PLTE`: palette (required for color type 3; optional for 2/6 sometimes)
- `tEXt`: uncompressed key/value text (`keyword\0text`)
- `zTXt`: compressed text
- `iTXt`: international text (can embed XMP)
- `pHYs`: pixel density (pixels per unit + unit specifier)
- `sRGB`: standard RGB info (rendering intent)
- `iCCP`: embedded ICC profile
- `gAMA`: gamma
- `cHRM`: chromaticities
- `tIME`: last-modification time
- `eXIf`: EXIF block (optional)

