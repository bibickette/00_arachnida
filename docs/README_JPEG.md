
# JPEG — Analyzer Documentation

*This document complements the **Scorpion** documentation. For project overview and usage instructions, see the main README [here](../README.md).*

This documentation is written to **match what `JPEGAnalyzer.parse_jpeg_sof()` currently extracts** in your Scorpion project, while also describing the general structure of a JPEG file.

---

## 1) What is a JPEG file?

**JPEG (Joint Photographic Experts Group)** is a compressed raster image format.  
A JPEG file is organized as a sequence of **markers** (small tagged blocks). Some markers carry metadata (JFIF/EXIF/XMP/ICC), while others describe the encoded image (SOF/SOS/tables).

### General structure (high-level)

```
SOI (FFD8)
[APPn / COM / DQT / DHT / SOFn / ... segments]
SOS (FFDA)
  entropy-coded scan data (compressed image stream)
EOI (FFD9)
```

Your analyzer **does not decode the image stream**; it scans the file to find:
- the encoding process + image size from a **SOF** marker, and
- the EXIF TIFF byte order if an **APP1** segment is present.

---

## 2) Endianness rules (important)

- JPEG **segment lengths** are **big-endian** (`>H`).
- The EXIF data inside APP1 is a TIFF structure that declares its own byte order:
  - `"II"` = little-endian
  - `"MM"` = big-endian

Your code uses:
- `struct.unpack(">H", ...)` for markers and segment lengths
- a string search for `Exif\0\0` to locate the TIFF header

---

## 3) Marker basics

Every JPEG marker begins with `0xFF` followed by a marker byte.

Examples:
- SOI = `FFD8`
- EOI = `FFD9`
- APP1 = `FFE1`
- SOF0 = `FFC0`
- SOF2 = `FFC2`
- SOS = `FFDA`

> In your analyzer, the marker is read as a 16-bit big-endian value:
> `marker = struct.unpack(">H", data[i:i+2])[0]`

---

## 4) Segment structure (what your parser relies on)

Most markers (APPn, SOFn, DQT, DHT, COM, etc.) are followed by a 2-byte length:

```
FF xx    marker
00 LL    length (big-endian)  -> includes the 2 length bytes, but NOT the marker bytes
...      payload (length - 2 bytes)
```

This matches your skip logic:

```python
seg_len = struct.unpack(">H", data[i+2:i+4])[0]
i += 2 + seg_len
```

Special cases:
- SOI (FFD8) and EOI (FFD9) are exactly 2 bytes (no length field)

---

## 5) What `JPEGAnalyzer.parse_jpeg_sof()` extracts

Your parser walks the file and looks for:
- **APP1 (FFE1)** to detect EXIF byte order
- **SOF markers** (FFC0/FFC1/FFC2/FFC3/FFC9/FFCA) to extract image properties

It stops as soon as it finds and parses a SOF marker (it `break`s).

### A) APP1 (FFE1): EXIF byte order detection

Your helper:

```python
idx = data.find(b"Exif\x00\x00")
tiff_start = idx + 6
order = data[tiff_start:tiff_start+2]
```

If it finds EXIF, it prints:
- `ExifByteOrder`:
  - `"Little-endian (Intel, II)"` if bytes are `II`
  - `"Big-endian (Motorola, MM)"` if bytes are `MM`

Notes (matching current behavior):
- It does not parse IFD tags (Make/Model/GPS/etc.); it only detects byte order.
- It searches the entire file for `Exif\0\0` rather than parsing the APP1 payload boundaries. This is OK for many files, but can be fooled by unusual content.

### B) SOF: encoding process + dimensions + sampling

When a SOF marker is found, your analyzer prints:

- `EncodingProcess` (based on marker type, e.g. SOF0 baseline / SOF2 progressive)
- `BitsPerSample`
- `ImageHeight`
- `ImageWidth`
- `ColorComponents`
- `YCbCrSubSampling` (derived from the sampling factors of the first component)

#### SOF payload layout (as used by your code)

Your code uses offsets relative to the marker position `i`:

| Bytes in file | Meaning | Code |
|---:|---|---|
| `i+0..i+1` | marker | `marker` |
| `i+2..i+3` | segment length | used to skip segments |
| `i+4` | Sample precision (bits per sample) | `BitsPerSample = data[i+4]` |
| `i+5..i+6` | Height (big-endian) | `ImageHeight` |
| `i+7..i+8` | Width (big-endian) | `ImageWidth` |
| `i+9` | Number of components | `ColorComponents` |
| `i+10..` | Component descriptors | used for sampling |

Component descriptor (3 bytes each):
- Component ID (1 byte)
- Sampling factors (1 byte): high nibble = H, low nibble = V
- Quant table selector (1 byte)

Your analyzer reads the sampling byte for the **first component** at `i+11`:
- `y_sampling = data[i+11]`
- `y_h = (y_sampling >> 4) & 0xF`
- `y_v = y_sampling & 0xF`

Then maps some common cases:
- (2,2) → 4:2:0
- (2,1) → 4:2:2
- (1,1) → 4:4:4
- (4,1) → 4:1:1

---

## 6) What this analyzer does NOT parse (yet)

To keep expectations aligned with your current implementation, `JPEGAnalyzer` does not currently:

- Parse APP0 (JFIF) fields (version, density, etc.)
- Parse EXIF tags (DateTimeOriginal, Orientation, GPS, etc.)
- Parse ICC profile (APP2)
- Parse comments (COM)
- Decode compressed scan data (SOS stream)

It focuses on a minimal but useful subset:
- **SOF** image characteristics
- **EXIF byte order** detection

---

## 7) Typical output keys

You should expect keys such as:

- `ExifByteOrder` (only if EXIF is found)
- `EncodingProcess`
- `BitsPerSample`
- `ImageHeight`
- `ImageWidth`
- `ColorComponents`
- `YCbCrSubSampling`

---

## 8) Known implementation notes (worth documenting)

These are not “bugs” per se, but they explain behavior:

1. **Stops at the first SOF found**  
   Many JPEGs contain a single SOF; this is usually fine.

2. **Height/Width come from SOF, not from Pillow**  
   Pillow already knows dimensions, but this proves you can parse the binary structure.

3. **APP1 is not bounded to the segment**  
   The EXIF detection searches globally for `Exif\0\0`. A stricter parser would:
   - parse APP1 segments properly
   - then look inside the APP1 payload

If you want, I can show you a “strict APP1 parsing” approach that still stays simple and only reads the EXIF byte order.