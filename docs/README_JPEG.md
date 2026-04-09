# JPEG — Analyzer Documentation

*This document complements the **Scorpion** documentation. For project overview and usage instructions, see the main README [here](../README.md).*

This documentation is written to **match what `JPEGAnalyzer.parse_jpeg_sof()` currently extracts** in your Scorpion project, while also describing the general structure of a JPEG file.

---

## 1) What is a JPEG file?

**JPEG (Joint Photographic Experts Group)** is a compressed raster image format.  
A JPEG file is organized as a sequence of **markers** (small tagged blocks). Some markers carry metadata (JFIF/EXIF/XMP/ICC), while others describe the encoded image (SOF/SOS/tables).

### General structure (high-level)

```
┌─────────────────────────────────────┐
│ SOI (Start of Image)                │
├─────────────────────────────────────┤
│ APPn (Metadata: JFIF, EXIF, XMP...) │
├─────────────────────────────────────┤
│ DQT (Quantization Tables)           │
├─────────────────────────────────────┤
│ SOF (Start of Frame: dimensions)    │
├─────────────────────────────────────┤
│ DHT (Huffman Tables)                │
├─────────────────────────────────────┤
│ SOS (Start of Scan)                 │
├─────────────────────────────────────┤
│ Compressed image data (scan data)   │
├─────────────────────────────────────┤
│ EOI (End of Image)                  │
└─────────────────────────────────────┘
```

`JPEGAnalyzer` scans the file to find:
- the encoding process + image size from a **SOF** marker, and
- the EXIF/TIFF byte order if an **APP1** segment is present.

---

## 2) Endianness rules

- JPEG **marker values** and **segment lengths** are read as **big-endian**.
  - In code: `struct.unpack(">H", ...)`

- EXIF inside APP1 is a TIFF structure that declares its own byte order:
  - `"II"` = little-endian (Intel)
  - `"MM"` = big-endian (Motorola)

`JPEGAnalyzer` detects EXIF by searching for `Exif\0\0`, then reads the TIFF byte-order bytes.

---

## 3) Marker basics

Every JPEG marker begins with `0xFF` followed by a marker byte.

Common markers:

| Marker | Hex | Meaning |
|:---:|:---:|---|
| `SOI` | `FFD8` | Start of Image |
| `EOI` | `FFD9` | End of Image |
| `APP0` | `FFE0` | JFIF |
| `APP1` | `FFE1` | EXIF and/or XMP |
| `APP2` | `FFE2` | ICC profile (often split) |
| `DQT` | `FFDB` | Quantization tables |
| `DHT` | `FFC4` | Huffman tables |
| `SOF0` | `FFC0` | Baseline DCT frame header |
| `SOF2` | `FFC2` | Progressive DCT frame header |
| `SOS` | `FFDA` | Start of Scan (compressed data follows) |

---

## 4) Segment structure

### A) JPEG segment structure (most markers)

Most markers (APPn, SOFn, DQT, DHT, COM, etc.) are followed by a 2-byte length:

| Bytes | Size | Name | Description |
|:-----:|:----:|------|-------------|
| `FF xx` | 2 bytes | Marker | Identifies the segment (`0xFF` + marker code `xx`) |
| `00 LL` | 2 bytes | Length | Big-endian length **including these 2 length bytes**, but **excluding** the 2 marker bytes |
| `...` | `Length - 2` bytes | Payload | Segment data (payload size is `Length - 2`) |

### B) Special cases (no length field)

| Marker |  Hex   |  Size   | Description                                     |
|:------:|:------:|:-------:|-------------------------------------------------|
|  `SOI`   | `FFD8` | 2 bytes | Start of Image — marker only, no length/payload |
|  `EOI`   | `FFD9` | 2 bytes | End of Image — marker only, no length/payload   |

---

## 5) SOF (Start Of Frame) layout (offsets from the start of the marker)

Offsets below are counted from the first `0xFF` byte of the SOF marker (i.e., from the start of `FF C0`, `FF C2`, ...).

| Offset | Size | Field | Description |
|:-----:|:----:|------|-------------|
| 0-1 | 2 bytes | Marker | `FF C0` (SOF0), `FF C1`, `FF C2` (SOF2), etc. |
| 2-3 | 2 bytes | Length | Big-endian. Includes these 2 bytes, excludes the marker. |
| 4 | 1 byte | Sample Precision | Bits per sample (commonly 8). |
| 5-6 | 2 bytes | Image Height | Big-endian. |
| 7-8 | 2 bytes | Image Width | Big-endian. |
| 9 | 1 byte | Number of Components (N) | e.g., 1 (grayscale), 3 (YCbCr/RGB), 4 (CMYK). |
| 10.. | `3*N` bytes | Component Descriptors | Repeated N times (see below). |
| `10 + 3k` | 1 byte | Component ID | Identifier (often 1=Y, 2=Cb, 3=Cr). |

### How to read `10 + 3k` (component descriptor indexing)

In SOF, component descriptors start at **offset 10**.  
Each component descriptor is exactly **3 bytes** long:

1. Component ID (1 byte)  
2. Sampling Factors (1 byte)  
3. Quantization Table ID (1 byte)

So for component index `k` (0-based), the descriptor begins at:

- `base_offset = 10`
- `descriptor_offset = 10 + (3 * k)`  (often written as `10 + 3k`)

#### Example offsets (common case: N = 3 components)

| Component index `k` | Descriptor start offset | Bytes covered (ID, Samp, QT) | Typical meaning |
|:-------------------:|:-----------------------:|:-----------------------------:|----------------|
| 0 | `10 + 3*0 = 10` | 10, 11, 12 | Y (luma) |
| 1 | `10 + 3*1 = 13` | 13, 14, 15 | Cb (chroma) |
| 2 | `10 + 3*2 = 16` | 16, 17, 18 | Cr (chroma) |