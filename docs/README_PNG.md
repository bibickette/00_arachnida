# PNG - Analyzer Documentation

*This document complements the **Scorpion** documentation. For project overview and usage instructions, see the main README [here](../README.md).*

---

## 1) What is a PNG file?

**PNG (Portable Network Graphics)** is a lossless raster image format designed around:
- a fixed 8-byte signature (to identify the file),
- a sequence of **chunks** that store image properties and optional metadata,
- compressed image data stored in one or more `IDAT` chunks.

### General structure (high-level)

```
┌─────────────────────────────────────┐
│ PNG Signature (8 bytes)             │
├─────────────────────────────────────┤
│ IHDR Chunk (image header)           │
├─────────────────────────────────────┤
│ Other Chunks (PLTE, tRNS, tEXt...)  │
├─────────────────────────────────────┤
│ IDAT Chunk(s) (compressed image)    │
│ (may be split across multiple)      │
├─────────────────────────────────────┤
│ IEND Chunk (end of file)            │
└─────────────────────────────────────┘
```

Each chunk has the structure:

| Part | Size | Description |
|:----:|:----:|-------------|
| Length | 4 bytes | Number of bytes in the **Data** field only (big-endian) |
| Type | 4 bytes | 4-letter ASCII chunk type (e.g., `"IHDR"`) |
| Data | variable | Chunk payload (may be empty) |
| CRC | 4 bytes | CRC-32 over `Type + Data` (big-endian stored value) |

---

## 2) Endianness & primitive types

PNG uses **big-endian** for:
- chunk `Length` (4 bytes)
- IHDR `width` and `height` (4 bytes each)
- CRC (4 bytes)

In the analyzer, these are decoded using:
- `struct.unpack(">I", ...)`

---

## 3) PNG signature (8 bytes)

At file offset `0x00`:

- Hex: `89 50 4E 47 0D 0A 1A 0A`

This signature indicates the file contains a PNG image made of a series of chunks beginning with `IHDR` and ending with `IEND`.

---

## 4) Chunk structure (file offsets relative to `i`)

When the parser is positioned at a chunk start index `i`:

| Part | Size | Meaning |
|---|---:|---|
| `data[i:i+4]` | 4 | Data length (big-endian) |
| `data[i+4:i+8]` | 4 | Chunk type ASCII |
| `data[i+8:i+8+length]` | length | Chunk data |
| `data[i+8+length:i+12+length]` | 4 | CRC |

Cursor advance:
- `i += 12 + length`

---

## 5) IHDR chunk

Chunk type: `IHDR`  
IHDR data length is always **13 bytes**.

Your analyzer extracts:

| IHDR Data Offset | Size | Field | Analyzer key |
|---:|---:|---|---|
| 0 | 4 | width (BE) | `width` |
| 4 | 4 | height (BE) | `height` |
| 8 | 1 | bit depth | `bit_depth` |
| 9 | 1 | color type | `color_type` (decoded) |
| 10 | 1 | compression method | `compression_method` (decoded) |
| 11 | 1 | filter method | `filter_method` (decoded) |
| 12 | 1 | interlace method | `interlace_method` (decoded) |

### Decoded values

- `color_type`:
  - 0 → Grayscale
  - 2 → Truecolor (RGB)
  - 3 → Indexed-color (palette)
  - 4 → Grayscale with alpha
  - 6 → Truecolor with alpha (RGBA)

- `compression_method`:
  - 0 → Deflate/inflate

- `filter_method`:
  - 0 → Adaptive filtering (5 filter types)

- `interlace_method`:
  - 0 → No interlace
  - 1 → Adam7 interlace

