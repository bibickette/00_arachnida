# GIF — Analyzer Documentation

*This document complements the **Scorpion** documentation. For project overview and usage instructions, see the main README [here](../README.md).*

This document is a practical reference for `GIFAnalyzer.py` in Scorpion.

> Key idea: GIF is block-based. You parse the header, logical screen descriptor, optional global color table, then walk blocks until the trailer (0x3B).

---

## 0) Endianness

Most multi-byte integers in GIF are **little-endian** (notably width/height, delays).

---

## 1) File structure overview

```
Header  `GIF87a` or `GIF89a` (6)
Logical Screen Descriptor (7)
[Optional Global Color Table (0..) (size depends on LSD flags)]
{ sequence of blocks...
Image Descriptor + (optional Local Color Table) + Image Data
Extension blocks (Graphic Control Extension, Comment, Application, Plain Text)}
Trailer (1) = 0x3B
```

Blocks are introduced by a single byte:
- `0x2C` Image Descriptor
- `0x21` Extension Introducer
- `0x3B` Trailer (end)

---

## 2) Header (6 bytes)

At offset 0:
- ASCII `"GIF87a"` or `"GIF89a"`

Analyzer prints:
- version (87a/89a)

---

## 3) Logical Screen Descriptor (7 bytes)

Immediately after header (offset 6):

| Offset | Size | Field |
|---:|---:|---|
| 0 | 2 | canvas width (LE) |
| 2 | 2 | canvas height (LE) |
| 4 | 1 | packed fields |
| 5 | 1 | background color index |
| 6 | 1 | pixel aspect ratio |

Packed fields bits:
- bit 7: Global Color Table flag (GCTF)
- bits 6-4: color resolution (CR)
- bit 3: sort flag
- bits 2-0: GCT size (N) → table size = `2^(N+1)`

---

## 4) Global Color Table (optional)

If GCT flag is set:
- size = `2^(N+1)` entries
- each entry is 3 bytes: R, G, B

So:
- `gct_bytes = 3 * gct_entries`

---

## 5) Blocks parsing loop

### A) Image Descriptor (0x2C)

Structure:

| Part | Size | Notes |
|---|---:|---|
| 0x2C | 1 | separator |
| left | 2 | LE |
| top | 2 | LE |
| width | 2 | LE |
| height | 2 | LE |
| packed | 1 | local table flag, interlace, sort, LCT size |

If Local Color Table (LCT) flag set:
- LCT entries = `2^(N+1)` (from packed)
- LCT bytes = `3 * entries`

Then image data:
- LZW minimum code size (1 byte)
- sub-blocks: `[block_size][data...]*` until block_size=0

For metadata-only, you can:
- count frames (number of image descriptors)
- collect per-frame width/height and interlace flag
- optionally skip decoding LZW data by jumping sub-blocks

### B) Extension blocks (0x21)

After `0x21`, a label byte identifies extension type:

- `0xF9` Graphic Control Extension (GCE)
- `0xFE` Comment Extension
- `0xFF` Application Extension
- `0x01` Plain Text Extension (rare)

#### Graphic Control Extension (0x21 0xF9)
Structure:
- block size (1) = 4
- packed (1):
  - disposal method bits
  - transparency flag
- delay time (2 LE) in 1/100s
- transparent color index (1)
- block terminator (1) = 0

Analyzer extracts:
- delay
- transparency index (if enabled)
- disposal method

#### Comment Extension (0x21 0xFE)
Data is stored in sub-blocks until 0 size.
Analyzer can concatenate and print comment text (best effort).

#### Application Extension (0x21 0xFF)
Starts with block size 11 then application identifier + auth code.
Common: `"NETSCAPE2.0"` indicates looping:
- sub-block contains loop count (0 = infinite)

Analyzer prints:
- loop count if present

---

## 6) Trailer (0x3B)

One byte `0x3B` ends the file.
