
# PNG — Analyzer Documentation

*This document complements the **Scorpion** documentation. For project overview and usage instructions, see the main README [here](../README.md).*

This documentation is written to **match what `PNGAnalyzer.parse_png_ihdr()` currently extracts** in your Scorpion project, while also describing the general structure of a PNG file.

---

## 1) What is a PNG file?

**PNG (Portable Network Graphics)** is a lossless raster image format designed around:
- a fixed 8-byte signature (to identify the file),
- a sequence of **chunks** that store image properties and optional metadata,
- compressed image data stored in one or more `IDAT` chunks.

PNG is *chunk-based* (similar idea to “boxes” or “records”): you can iterate through the file without decoding pixels, and still recover useful metadata (dimensions, color type, embedded text, etc.).

### General structure (high-level)

```
Signature (8 bytes)
Chunk #1 (usually IHDR)
Chunk #2 ...
...
Chunk (IEND)
```

Each chunk has the structure:

```
Length (4) + Type (4) + Data (Length) + CRC (4)
```

Your analyzer focuses on:
- validating/printing the PNG signature,
- parsing the `IHDR` chunk fields,
- decoding `tEXt` chunks into key/value pairs,
- listing all other chunks by name and size.

---

## 2) Endianness & primitive types

PNG uses **big-endian** for:
- chunk `Length` (4 bytes)
- IHDR `width` and `height` (4 bytes each)
- CRC (4 bytes)

Your analyzer uses:
- `int.from_bytes(..., "big")`

---

## 3) PNG signature (8 bytes) — extracted by the analyzer

At file offset `0x00`:

- Hex: `89 50 4E 47 0D 0A 1A 0A`

Your analyzer stores:
- `PNG Signature` = `data[:8].hex(' ').upper()`

If you want strict validation, you could compare against the known signature bytes, but currently the analyzer prints it as metadata.

---

## 4) Chunk parsing loop (matches your code)

Your code starts reading chunks at:

- `i = 8` (right after the signature)

For each chunk:

1. `length = int.from_bytes(data[i:i+4], "big")`
2. `chunk_type = data[i+4:i+8].decode("ascii")`
3. `chunk_data = data[i+8 : i+8+length]`
4. (CRC exists but is not used)  
   `crc = data[i+8+length : i+12+length]` (commented in your code)
5. Advance:
   - `i += 12 + length`

### Chunk structure (file offsets relative to `i`)
| Part | Size | Meaning |
|---|---:|---|
| `data[i:i+4]` | 4 | Data length |
| `data[i+4:i+8]` | 4 | Chunk type ASCII |
| `data[i+8:i+8+length]` | length | Chunk data |
| `data[i+8+length:i+12+length]` | 4 | CRC |

---

## 5) IHDR chunk — fields extracted by the analyzer

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

### Value decoding (your implementation)
Your `decode_png_value()` maps:

- `color_type`:
  - 0 → Grayscale
  - 2 → Truecolor
  - 3 → Indexed-color
  - 4 → Grayscale with alpha
  - 6 → Truecolor with alpha

- `compression_method`:
  - 0 → Deflate/inflate

- `filter_method`:
  - 0 → Adaptive filtering with five basic filter types

- `interlace_method`:
  - 0 → No interlace
  - 1 → Adam7 interlace

---

## 6) tEXt chunk — extracted by the analyzer

Chunk type: `tEXt`

Your analyzer does:

```python
key, val = chunk_data.split(b"\x00", 1)
data_info[f"Text - {BasicMetadata.decode_value(key)}"] = BasicMetadata.decode_value(val)
```

Meaning:
- `tEXt` stores **keyword\0text**
- you split at the first `NULL` byte and print it as:
  - `Text - <keyword>` → `<value>`

Notes:
- This handles classic text metadata such as Software, Author, Comment, etc. when stored as `tEXt`.
- Your analyzer does not currently decode `iTXt` or `zTXt` (it will list them as `Chunk - iTXt: N bytes`).

---

## 7) Other chunks — what the analyzer prints

For any chunk that is not `IHDR` or `tEXt`, your analyzer prints:

- `Chunk - <TYPE>` → `"<length> bytes"`

Examples you might see:
- `Chunk - PLTE` (palette)
- `Chunk - IDAT` (compressed image data; may appear multiple times)
- `Chunk - IEND` (end marker)
- `Chunk - iTXt` (international text, often used for XMP)
- `Chunk - pHYs`, `sRGB`, `gAMA`, etc.

---

## 8) CRC in PNG (present but not validated in current code)

Each PNG chunk includes a CRC-32 checksum (4 bytes) computed over:

- `chunk_type + chunk_data`

Your code currently ignores CRC (commented line).

If you want to add validation later:
- compare stored CRC with `zlib.crc32(chunk_type_bytes + chunk_data)`

---

## 9) What this analyzer does NOT parse (yet)

Currently, `PNGAnalyzer` does not:
- validate the signature strictly (it prints it)
- validate CRC values
- decode and interpret `iTXt` / `zTXt` (only lists them)
- reconstruct or decompress `IDAT` pixel data (scanlines + filters)
- interpret palette entries (`PLTE`) for indexed-color images

That’s totally fine for a metadata-oriented assignment; the current output is mainly:
- IHDR properties
- textual metadata from `tEXt`
- an inventory of chunks present in the file

---

## 10) Output summary (what you should expect)

- `PNG Signature`
- `width`, `height`
- `bit_depth`, `color_type`
- `compression_method`, `filter_method`, `interlace_method`
- `Text - <key>` entries for each `tEXt`
- `Chunk - <TYPE>` entries for every other chunk