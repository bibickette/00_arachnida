# GIF — Analyzer Documentation

*This document complements the **Scorpion** documentation. For project overview and usage instructions, see the main README [here](../README.md).*

This documentation is written to **match what `GIFAnalyzer.parse_gif()` currently extracts** in your Scorpion project, and to explain the general structure of a GIF file.

---

## 1) What is a GIF file?

**GIF (Graphics Interchange Format)** is an indexed-color image format that can store:
- a single static image, or
- multiple frames (animation)

GIF is block-based: after a small header and a “logical screen” descriptor, the file is made of a sequence of **blocks** (image descriptors and extensions) until the trailer byte.

### General structure (high-level)

```
Header (6 bytes): "GIF87a" or "GIF89a"
Logical Screen Descriptor (7 bytes)
[Global Color Table (optional)]
{ Blocks... (Image Descriptors and Extensions) }
Trailer (1 byte): 0x3B
```

Your analyzer does **metadata parsing**:
- validates signature
- reads Logical Screen Descriptor fields
- skips global/local color tables
- iterates blocks to count frames and extract some extension info (comment/app)
- prints a frame count and timing (using Pillow for duration)

---

## 2) Endianness

Most multi-byte integers in GIF are **little-endian**, including:
- screen width/height
- image descriptor geometry
- delay time (in Graphic Control Extension)

---

## 3) File header (6 bytes) — extracted by the analyzer

At file offset `0x00`:
- ASCII `"GIF87a"` or `"GIF89a"`

Your analyzer checks:

- `signature[:3] == b"GIF"` (otherwise error)
- prints:
  - `Signature` (string)
  - `Signature hex`

It does not currently print “version” explicitly, but the signature includes it (`87a` / `89a`).

---

## 4) Logical Screen Descriptor (7 bytes) — extracted by the analyzer

Immediately after the 6-byte header, at file offset `0x06`:

| File Offset | Size | Field | Analyzer key |
|---:|---:|---|---|
| 0x06 | 2 | Logical Screen Width (LE) | `Screen Width` |
| 0x08 | 2 | Logical Screen Height (LE) | `Screen Height` |
| 0x0A | 1 | Packed fields | used for `G Color Table Flag` + (skipping GCT) |
| 0x0B | 1 | Background Color Index | `Backgrnd Color Idx` |
| 0x0C | 1 | Pixel Aspect Ratio | (currently read but not printed) |

### Packed fields — what your analyzer uses
Your analyzer extracts:
- Global Color Table Flag: `(packed >> 7) & 1`  
  Printed as `G Color Table Flag`.

It also uses the size bits to skip the Global Color Table (see below):
- `N = packed & 0b111`
- `gct_entries = 2 ** (N + 1)`
- if flag set: skip `3 * gct_entries` bytes

> The analyzer does not currently print the computed GCT size; it only uses it to move the read cursor correctly.

---

## 5) Global / Local Color Tables — how the analyzer handles them

GIF can have:
- a **Global Color Table** (after LSD)
- a **Local Color Table** (inside each Image Descriptor)

Each color table entry is **3 bytes**: `R, G, B`.

Your analyzer does not decode the table contents; it only skips them so that parsing stays aligned.

Skipping logic:
- Uses `skip_color_table(packed, i)` where:
  - flag is bit 7
  - size is derived from bits 0..2

---

## 6) Blocks loop (extensions and image descriptors)

After LSD (+ optional GCT), GIF is a sequence of blocks. Your analyzer loops until it finds:
- `0x3B` Trailer (end)

The analyzer reacts to these introducers:
- `0x21` → Extension block
- `0x2C` → Image Descriptor (counts as a frame)
- `0x3B` → Trailer (stop)

Any other byte:
- it increments `i += 1` (attempts to recover)

---

## 7) Image Descriptor (0x2C) — how frames are counted

When the analyzer sees `0x2C`:
- it increments `frames += 1`
- it parses and skips the image descriptor:

### Image Descriptor structure (10 bytes total incl. 0x2C)
After the `0x2C` separator, the descriptor fields are:

| Field | Size | Notes |
|---|---:|---|
| left | 2 | LE |
| top | 2 | LE |
| width | 2 | LE |
| height | 2 | LE |
| packed | 1 | contains Local Color Table flag + size |

Your code reads:
```python
left, top, w, h, ipacked = struct.unpack_from("<HHHHB", data, i)
```

Then it:
1) skips an optional **Local Color Table** using `ipacked`  
2) skips the **LZW minimum code size** (1 byte)  
3) skips image data **sub-blocks** until a 0-size terminator

### Sub-blocks (important)
GIF stores some payloads as a series of sub-blocks:

```
[size][payload...][size][payload...]...[0x00]
```

Your analyzer skips these using `skip_sub_blocks()`.

---

## 8) Extensions (0x21) — what your analyzer extracts

When the analyzer sees `0x21`, it reads the label byte:

### A) Graphic Control Extension (label 0xF9)
Your analyzer:
- checks the block size byte must be `4`
- then skips the whole GCE block with `i += 6`

It does **not** currently decode:
- disposal method
- transparency index
- delay time (your total timing comes from Pillow instead)

### B) Comment Extension (label 0xFE)
Your analyzer:
- reads all sub-blocks
- concatenates them as Latin-1
- prints:
  - a “Comment Extension” section header
  - `Comment: ...`

### C) Application Extension (label 0xFF)
Your analyzer:
- prints:
  - `App Identifier` (bytes `i+1:i+9`)
  - `App Auth Code` (bytes `i+9:i+12`)
- then skips sub-blocks

Important note (matching your current code):
- It does not currently parse NETSCAPE loop count, it only prints identifier/auth code.

### D) Plain Text Extension (label 0x01)
Your analyzer:
- simply skips sub-blocks

---

## 9) Trailer (0x3B)

The analyzer stops when it sees `0x3B`.

---

## 10) What gets printed (current output behavior)

From `parse_gif()`:
- `===== GIF Header`
  - Signature, Signature hex, Screen Width, Screen Height, G Color Table Flag, Backgrnd Color Idx
- optional:
  - `===== Chunk Comment Extension` + Comment
  - `===== Chunk Application Extension` + App Identifier + App Auth Code
- `===== Frames Info` + Frame Count

From `analyze_image()` (Pillow):
- it reads `image.info.get("duration")` (ms per frame, if present)
- if duration exists, it prints:
  - `One frame duration (ms)`
  - `Total time (s)` = duration * frames / 1000

---

## 11) Things the analyzer does not parse (yet)

Currently, it does not:
- decode LZW image data
- decode GCE fields (delay/disposal/transparency) from bytes
- compute loop count from NETSCAPE application extension sub-block
- print pixel aspect ratio
- print local/global color table sizes

These could be added later, but the current document reflects the current analyzer behavior.
