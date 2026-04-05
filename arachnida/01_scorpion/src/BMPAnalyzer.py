import struct
from PIL import Image

from src.BasicMetadata import BasicMetadata
from src.Color import Color

class BMPAnalyzer:
    
    @staticmethod
    def parse_bmp_header(data: bytes):
        def get_dib_header_type(size: int) -> str:
            DIB_HEADER_TYPES = {
                12: "BITMAPCOREHEADER",
                40: "BITMAPINFOHEADER",
                108: "BITMAPV4HEADER",
                124: "BITMAPV5HEADER",
            }
            return DIB_HEADER_TYPES.get(size, f"Unknown ({size} bytes)")
        
        def get_compression_method(value: int) -> str:
            COMPRESSION_METHODS = {
                0: "BI_RGB (no compression)",
                1: "BI_RLE8 (RLE 8-bit/pixel)",
                2: "BI_RLE4 (RLE 4-bit/pixel)",
                3: "BI_BITFIELDS (bit field or Huffman 1D compression)",
                4: "BI_JPEG (JPEG image for printing devices)",
                5: "BI_PNG (PNG image for printing devices)",
                6: "BI_ALPHABITFIELDS (RGBA bit field masks)",
                11: "BI_CMYK (no compression, CMYK color space)",
                12: "BI_CMYKRLE8 (RLE-8 compression, CMYK color space)",
                13: "BI_CMYKRLE4 (RLE-4 compression, CMYK color space)",
            }
            return COMPRESSION_METHODS.get(value, f"Unknown ({value})")
        
        def get_bits_per_pixel(value: int) -> str:
            BITS_PER_PIXEL = {
                1: "monochrome palette. NumColors = 1",
                4: "4bit palletized. NumColors = 16",
                8: "8bit palletized. NumColors = 256",
                16: "16bit RGB. NumColors = 65536",
                24: "24bit RGB. NumColors = 16M",
                32: "32bit RGB",
            }
            return BITS_PER_PIXEL.get(value, f"Unknown ({value} bits per pixel)")
        
        def get_color_space_type(value: bytes) -> str:
            COLOR_SPACE_TYPES = {
                0x00000000: "LCS_CALIBRATED_RGB",
                0x73524742: "LCS_sRGB",                 # 'sRGB'
                0x57696E20: "LCS_WINDOWS_COLOR_SPACE",  # 'Win '
                0x4C494E4B: "PROFILE_LINKED",           # 'LINK'
                0x4D424544: "PROFILE_EMBEDDED",         # 'MBED'
            }
            return COLOR_SPACE_TYPES.get(value, f"Unknown ({value})")
        
        def get_intent(value: int) -> str:
            INTENTS = {
                0: "LCS_GM_ABS_COLORIMETRIC",
                1: "LCS_GM_BUSINESS",
                2: "LCS_GM_GRAPHICS",
                3: "LCS_GM_IMAGES",
            }
            return INTENTS.get(value, f"Unknown ({value})")
        
        if data[:2] != b'BM':
            raise ValueError("Not a valid BMP file")
        
        data_info = {}
        file_size, reserved, pixel_data_offset, info_header_size = struct.unpack_from('<IIII', data, 2)
        
        data_info["BMP Signature"] = data[:2].decode('ascii')
        data_info["File Size"] = f"{file_size} bytes"
        data_info["Reserved"] = reserved
        data_info["Pixel Data Offset"] = f"{pixel_data_offset} bytes"
        
        data_info["Info Header Size"] = f"{info_header_size} bytes"
        data_info["DIB Header Type"] = get_dib_header_type(info_header_size)

        if info_header_size == 12:
            core_width, core_height, core_planes, core_bits_per_pixel = struct.unpack_from('<HHHH', data, 18)
            data_info["Image Width"] = f"{core_width} pixels"
            data_info["Image Height"] = f"{core_height} pixels"
            data_info["Planes"] = core_planes
            data_info["Bits per Pixel"] = get_bits_per_pixel(core_bits_per_pixel)
        
        if info_header_size >= 40:
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

            data_info["Image Width"] = f"{width} pixels"
            data_info["Image Height"] = f"{height} pixels"
            data_info["Planes"] = planes
            data_info["Bits per Pixel"] = get_bits_per_pixel(bits_per_pixel)
            data_info["Compression Method"] = get_compression_method(compression_method)
            data_info["Image Size"] = f"{image_size} bytes"
            data_info["X Pixels per Meter"] = x_pixels_per_meter
            data_info["Y Pixels per Meter"] = y_pixels_per_meter
            data_info["Colors Used"] = colors_used
            data_info["Important Colors"] = important_colors

        if info_header_size >= 108:
            red_mask, green_mask, blue_mask, alpha_mask = struct.unpack_from('<IIII', data, 54)
            data_info["Red Mask"] = f"0x{red_mask:08X}"
            data_info["Green Mask"] = f"0x{green_mask:08X}"
            data_info["Blue Mask"] = f"0x{blue_mask:08X}"
            data_info["Alpha Mask"] = f"0x{alpha_mask:08X}"
            
            cs_type = struct.unpack_from('<I', data, 70)[0]
            data_info["Color Space Type"] = f"{get_color_space_type(cs_type)}"
            
            endp_red_x, endp_red_y, endp_red_z = struct.unpack_from('<III', data, 74)
            endp_green_x, endp_green_y, endp_green_z = struct.unpack_from('<III', data, 86)
            endp_blue_x, endp_blue_y, endp_blue_z = struct.unpack_from('<III', data, 98)
            
            data_info["Endpoint Red"] = f"X:{endp_red_x}, Y:{endp_red_y}, Z:{endp_red_z}"
            data_info["Endpoint Green"] = f"X:{endp_green_x}, Y:{endp_green_y}, Z:{endp_green_z}"
            data_info["Endpoint Blue"] = f"X:{endp_blue_x}, Y:{endp_blue_y}, Z:{endp_blue_z}"

            gamma_red, gamma_green, gamma_blue = struct.unpack_from('<III', data, 110)
            data_info["Gamma Red"] = f"{gamma_red}"
            data_info["Gamma Green"] = f"{gamma_green}"
            data_info["Gamma Blue"] = f"{gamma_blue}"
            
        if info_header_size >= 124:
            intent, profile_data, profile_size, reserved_v5 = struct.unpack_from('<IIII', data, 122)
            data_info["Intent"] = f"{get_intent(intent)}"
            data_info["Profile Data"] = f"{profile_data}"
            data_info["Profile Size"] = f"{profile_size} bytes"
            data_info["Reserved (V5)"] = f"{reserved_v5}"
        
        return data_info
                


    @classmethod
    def analyze_image(cls, path: str) -> None:
        try:
            with Image.open(path) as image:
                BasicMetadata.print_all_basic_metadata(path, image)
                
            with open(path, "rb") as f:
                data = f.read()
                
            data_info = cls.parse_bmp_header(data)
            
            print(f"{Color.BLUE}===== BMP Header Info ====={Color.RESET}")
            
            for key, value in data_info.items():
                BasicMetadata.print_tag_value(f"{Color.BLUE}{key:20}", value)

        except Exception as e:
            print(f"{Color.RED}Error loading BMP metadata: {e}{Color.RESET}")
            