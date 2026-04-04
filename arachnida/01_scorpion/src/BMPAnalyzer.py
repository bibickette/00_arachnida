import struct
from PIL import Image

from src.BasicMetadata import BasicMetadata
from src.Color import Color

class BMPAnalyzer:
    
    @staticmethod
    def parse_bmp_header(data: bytes):
        def get_compression_method(value: int) -> str:
            COMPRESSION_METHODS = {
                0: "BI_RGB (no compression)",
                1: "BI_RLE8 (RLE 8-bit/pixel)",
                2: "BI_RLE4 (RLE 4-bit/pixel)",
            }
            return COMPRESSION_METHODS.get(value, f"Unknown ({value})")
        
        def get_bits_per_pixel(value: int) -> str:
            BITS_PER_PIXEL = {
                1: "monochrome palette. NumColors = 1  ",
                4: "4bit palletized. NumColors = 16",
                8: "8bit palletized. NumColors = 256",
                16: "16bit RGB. NumColors = 65536",
                24: "24bit RGB. NumColors = 16M",
            }
            return BITS_PER_PIXEL.get(value, f"Unknown ({value} bits per pixel)")
        
        
        if data[:2] != b'BM':
            raise ValueError("Not a valid BMP file")
                
        # struct.unpack_from('<I', data, 2)[0] veut dire : “lis 4 octets à partir de l’offset 2 dans data, interprète-les comme un unsigned int 32-bit en little‑endian, et retourne la valeur”.
        file_size = struct.unpack_from('<I', data, 2)[0]
        reserved = struct.unpack_from('<I', data, 6)[0]
        pixel_data_offset = struct.unpack_from('<I', data, 10)[0]
        info_header_size = struct.unpack_from('<I', data, 14)[0]
        width = struct.unpack_from('<I', data, 18)[0]
        height = struct.unpack_from('<I', data, 22)[0]
        planes = struct.unpack_from('<H', data, 26)[0]
        bits_per_pixel = struct.unpack_from('<H', data, 28)[0]
        compression_method = struct.unpack_from('<I', data, 30)[0]
        image_size = struct.unpack_from('<I', data, 34)[0]
        x_pixels_per_meter = struct.unpack_from('<I', data, 38)[0]
        y_pixels_per_meter = struct.unpack_from('<I', data, 42)[0]
        colors_used = struct.unpack_from('<I', data, 46)[0]
        important_colors = struct.unpack_from('<I', data, 50)[0]
        
        data = {
            "BMP Signature": data[:2].decode('ascii'),
            "File Size": f"{file_size} bytes",
            "Reserved": reserved,
            "Pixel Data Offset": f"{pixel_data_offset} bytes",
            "Info Header Size": f"{info_header_size} bytes",
            "Image Width": f"{width} pixels",
            "Image Height": f"{height} pixels",
            "Planes": planes,
            "Bits per Pixel": get_bits_per_pixel(bits_per_pixel),
            "Compression Method": get_compression_method(compression_method),
            "Image Size": f"{image_size} bytes",
            "X Pixels per Meter": x_pixels_per_meter,
            "Y Pixels per Meter": y_pixels_per_meter,
            "Colors Used": colors_used,
            "Important Colors": important_colors
        }
        
        for key, value in data.items():
            BasicMetadata.print_tag_value(f"{Color.BLUE}{key:20}", value)
        
        if bits_per_pixel <= 8:
            num_colors_in_palette = colors_used if colors_used > 0 else (1 << bits_per_pixel)
            BasicMetadata.print_tag_value(f"{Color.BLUE}{'Colors Palette':20}", num_colors_in_palette)
            # i = 54 #sauter les 54 octets de l'entête d'information (header 14 + 40 info header)
            # for idx in range(num_colors_in_palette):
            #     b, g, r, _ = struct.unpack_from('<BBBB', data, i + idx*4)
            #     print(f"Palette Color {idx}: R={r} G={g} B={b}")
            # i += num_colors_in_palette * 4
        else:
            BasicMetadata.print_tag_value(f"{Color.BLUE}{'Color Palette':20}", "No color palette for this BMP (bits per pixel > 8)")


    @classmethod
    def analyze_image(cls, path: str) -> None:
        try:
            with Image.open(path) as image:
                BasicMetadata.print_all_basic_metadata(path, image)
                
                with open(path, "rb") as f:
                    data = f.read()
                    
                cls.parse_bmp_header(data)

        except Exception as e:
            print(f"{Color.RED}Error loading BMP metadata: {e}{Color.RESET}")
            