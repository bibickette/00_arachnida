# GIF - Analyzer Documentation

*This document complements the **Scorpion** documentation. For project overview and usage instructions, see the main README [here](../README.md).*

---

## 1) What is a GIF file?

**GIF (Graphics Interchange Format)** is an indexed-color image format that can store:
- a single static image, or
- multiple frames (animation)

GIF is block-based: after a small header and a **Logical Screen Descriptor**, the file is made of a sequence of **blocks** (image descriptors and extensions) until the trailer byte.

### General structure (high-level)

```
┌─────────────────────────────────────┐
│ Header (6 bytes)                    │
├─────────────────────────────────────┤
│ Logical Screen Descriptor (7 bytes) │
├─────────────────────────────────────┤
│ Global Color Table (optional)       │
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │ Extensions (GIF89a)             │ │
│ │ - Graphic Control Extension     │ │
│ │ - Comment Extension             │ │
│ │ - Application Extension         │ │
│ │ - Plain Text Extension          │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │ Image Descriptor (one frame)    │ │
│ │ Local Color Table (optional)    │ │
│ │ Image Data (LZW-compressed)     │ │
│ └─────────────────────────────────┘ │
│            (repeated per image)     │
├─────────────────────────────────────┤
│ Trailer (1 byte: 0x3B)              │
└─────────────────────────────────────┘
```

---

## 2) Endianness & primitive types

GIF multi-byte integers are mostly **little-endian** (`<H`).

Typical `struct` formats:
1. `"<B"`: 1-byte unsigned integer (BYTE)
2. `"<H"`: 2-byte unsigned integer (WORD), little-endian  
3. `"<HHBBB"`: Logical Screen Descriptor payload (width, height, packed, bg index, aspect)
4. `"<HHHHB"`: Image Descriptor payload (left, top, width, height, packed)

---

## 3) File header (6 bytes)

| Offset | Size | Description | Value |
|:------:|:----:|-------------|-------|
| 0-2 | 3 bytes | Signature | `"GIF"` |
| 3-5 | 3 bytes | Version | `"87a"` or `"89a"` |

`GIFAnalyzer` prints both the ASCII and hexadecimal values.

---

## 4) Logical Screen Descriptor (LSD) (7 bytes)

Immediately after the 6-byte header, at file offset `0x06`:

| File Offset | Size | Field | Analyzer key |
|:-----------:|:----:|-------|--------------|
| `0x06` | 2 | Logical Screen Width (LE) | `Screen Width` |
| `0x08` | 2 | Logical Screen Height (LE) | `Screen Height` |
| `0x0A` | 1 | Packed fields | used for `G Color Table Flag` + (skipping GCT) |
| `0x0B` | 1 | Background Color Index | `Backgrnd Color Idx` |
| `0x0C` | 1 | Pixel Aspect Ratio | *(read but not printed)* |

### Packed fields (LSD packed byte)

Bit layout:
| Bits | Field | Meaning |
|:---:|-------|---------|
| 7 | Global Color Table Flag | 1 = present, 0 = absent |
| 6-4 | Color Resolution | (number of bits per primary color) - 1 |
| 3 | Sort Flag | 1 = sorted, 0 = not sorted |
| 2-0 | Global Color Table Size | table size = `2^(N+1)` |

Example:
```
Packed Fields = 0xF7 = 11110111
│││└┴┴─ GCT Size: 111 = 7 → 2^(7+1) = 256 colors
││└─── Sort Flag: 0 (not sorted)
│└┴──── Color Resolution: 111 = 7 → 8 bits per color
└────── GCT Flag: 1 (present)
```

### Pixel Aspect Ratio

The LSD includes a **Pixel Aspect Ratio** byte. It indicates the pixel width/height ratio for non-square pixels (legacy feature).

| Value | Meaning |
|:-----:|---------|
| 0 | Not specified (assume square pixels) |
| != 0 | Ratio can be computed as `(value + 15) / 64` |

---

## 5) Global / Local Color Tables

GIF can have:
- a **Global Color Table** (after the LSD)
- a **Local Color Table** (inside each Image Descriptor)

Each color table entry is **3 bytes**: `R, G, B`.

`GIFAnalyzer` does not decode the table contents; it only skips them so parsing stays aligned.

---

## 6) Blocks parsing loop (extensions and image descriptors)

After the LSD (+ optional GCT), a GIF file is a sequence of blocks. `GIFAnalyzer` loops until it finds:
- `0x3B` Trailer (end)

The analyzer reacts to these introducers:
- `0x21` → Extension block
- `0x2C` → Image Descriptor (counts as a frame)
- `0x3B` → Trailer (stop)

Any other byte:
- it increments `i += 1` (best-effort recovery)

---

## 7) Image Descriptor (0x2C)

Each **Image Descriptor** corresponds to **one frame**.

| Offset | Size | Description |
|:------:|:----:|-------------|
| 0 | 1 byte | Image Separator (`0x2C`) |
| 1-2 | 2 bytes | Left Position (LE) |
| 3-4 | 2 bytes | Top Position (LE) |
| 5-6 | 2 bytes | Width (LE) |
| 7-8 | 2 bytes | Height (LE) |
| 9 | 1 byte | Packed Fields (Local Color Table flag + interlace/sort + LCT size) |
| 10.. | var. | Local Color Table (optional) — present if LCT flag is set; size = `3 * 2^(N+1)` bytes |
| ... | 1 byte | LZW Minimum Code Size — 1 byte, immediately after the Image Descriptor **and optional LCT** |
| ... | var. | Image Data sub-blocks: `[block_size][data...]...` terminated by `block_size = 0x00` |

### Sub-blocks

GIF stores some payloads (image data, comments, application data, etc.) as a series of sub-blocks:

```
[size][payload...][size][payload...]...[0x00]
```

---

## 8) Extensions (0x21)

When the analyzer sees `0x21`, it reads the next byte as the **extension label**.

> Offsets below are **relative to the start of the extension block** (i.e., at the `0x21` byte).

### A) Graphic Control Extension (label `0xF9`)

| Offset | Size | Description |
|:-----:|:----:|-------------|
| 0 | 1 byte | Extension Introducer (`0x21`) |
| 1 | 1 byte | Extension Label (`0xF9`) |
| 2 | 1 byte | Block Size (`0x04`) |
| 3 | 1 byte | Packed Fields |
| 4-5 | 2 bytes | Delay Time (1/100s, little-endian) |
| 6 | 1 byte | Transparent Color Index |
| 7 | 1 byte | Block Terminator (`0x00`) |

`GIFAnalyzer` checks the block size (must be 4) and then skips the GCE payload to keep parsing aligned.

### B) Comment Extension (label `0xFE`)

| Offset | Size | Description |
|:-----:|:----:|-------------|
| 0 | 1 byte | Extension Introducer (`0x21`) |
| 1 | 1 byte | Comment Label (`0xFE`) |
| 2.. | var. | Comment sub-blocks: `[block_size][comment bytes...]...` |
| .. | 1 byte | Block Terminator (`0x00`) |

`GIFAnalyzer` concatenates the sub-block text (latin-1 best effort) and prints the comment.

### C) Application Extension (label `0xFF`)

| Offset | Size | Description |
|:-----:|:----:|-------------|
| 0 | 1 byte | Extension Introducer (`0x21`) |
| 1 | 1 byte | Application Label (`0xFF`) |
| 2 | 1 byte | Block Size (`0x0B` = 11) |
| 3-10 | 8 bytes | Application Identifier (e.g., `"NETSCAPE"`) |
| 11-13 | 3 bytes | Application Authentication Code (e.g., `"2.0"`) |
| 14.. | var. | Application Data sub-blocks: `[block_size][data bytes...]...` |
| .. | 1 byte | Block Terminator (`0x00`) |

`GIFAnalyzer` prints the identifier and auth code, then skips the application data sub-blocks.

### D) Plain Text Extension (label `0x01`)

The Plain Text Extension is rare. It is meant to render simple text on top of the image.

`GIFAnalyzer` currently skips its sub-blocks.

---

## 9) Trailer (0x3B)

`GIFAnalyzer` stops when it encounters the Trailer byte `0x3B`.