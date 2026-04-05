import struct
from PIL import Image

from src.BasicMetadata import BasicMetadata
from src.Color import Color

class JPEGAnalyzer:
    @classmethod
    def parse_jpeg_sof(cls, data: bytes) -> dict:
        def get_exif_byte_order(data: bytes) -> str:
            idx = data.find(b"Exif\x00\x00")
            if idx == -1:
                return None
            tiff_start = idx + 6 # sauter exif\0\0
            order = data[tiff_start:tiff_start+2]
            if order == b"II":
                return "Little-endian (Intel, II)"
            elif order == b"MM":
                return "Big-endian (Motorola, MM)"
            return None
        
        SOF_MARKERS = {
            # Délimiteurs de base
            # 0xFFD8: "SOI - Start Of Image",
            # 0xFFD9: "EOI - End Of Image",

            # Start Of Frame (type de compression)
            0xFFC0: "SOF0 - Baseline DCT, Huffman coding",
            0xFFC1: "SOF1 - Extended sequential DCT, Huffman",
            0xFFC2: "SOF2 - Progressive DCT, Huffman",
            0xFFC3: "SOF3 - Lossless, Huffman",
            0xFFC9: "SOF9 - Extended sequential DCT, Arithmetic",
            0xFFCA: "SOF10 - Progressive DCT, Arithmetic",

            # Tables
            # 0xFFC4: "DHT - Define Huffman Table",
            # 0xFFDB: "DQT - Define Quantization Table",

            # Segments APP (métadonnées)
            # 0xFFE0: "APP0 - JFIF",
            0xFFE1: "APP1 - EXIF ou XMP",
            # 0xFFE2: "APP2 - ICC Profile",
            # 0xFFE3: "APP3 - Meta",
            # 0xFFEC: "APP12 - Meta",
            # 0xFFED: "APP13 - IPTC / Photoshop",
            # 0xFFEE: "APP14 - Adobe",

            # Autres
            # 0xFFDA: "SOS - Start Of Scan",
            # 0xFFDD: "DRI - Define Restart Interval",
            # 0xFFFE: "COM - Comment",
        }
        result = {}
        
        i = 0
        while i < len(data) - 1:
            # les marqueurs JPEG commencent par l'octet 0xFF
            if data[i] != 0xFF:
                i += 1
                continue

            marker = struct.unpack(">H", data[i:i+2])[0]

            if marker in SOF_MARKERS:
                if marker == 0xFFE1: # APP1
                    result["ExifByteOrder"] = get_exif_byte_order(data)
                else: # SOF
                    result["EncodingProcess"] = SOF_MARKERS[marker]
                    result["BitsPerSample"]   = data[i+4]
                    result["ImageHeight"]     = struct.unpack(">H", data[i+5:i+7])[0]
                    result["ImageWidth"]      = struct.unpack(">H", data[i+7:i+9])[0]
                    result["ColorComponents"] = data[i+9]

                    y_sampling = data[i+11]
                    y_h = (y_sampling >> 4) & 0xF   
                    y_v = y_sampling & 0xF

                    SUBSAMPLING_MAP = {
                        (2, 2): "YCbCr4:2:0 (2 2)",
                        (2, 1): "YCbCr4:2:2 (2 1)",
                        (1, 1): "YCbCr4:4:4 (1 1)",
                        (4, 1): "YCbCr4:1:1 (4 1)",
                    }
                    result["YCbCrSubSampling"] = SUBSAMPLING_MAP.get((y_h, y_v), f"{y_h}x{y_v}")
                    break
                
            # sauter le segment
            if marker in (0xFFD8, 0xFFD9):
                # SOI et EOI font juste 2 octets
                i += 2
            else:
                # la longueur est definie de [i+2:i+4], et inclut les 2 octets de longueur mais pas les 2 du marker
                seg_len = struct.unpack(">H", data[i+2:i+4])[0]
                i += 2 + seg_len
        
        return result


    @classmethod
    def analyze_image(cls, path: str) -> None:
        try:
            with Image.open(path) as image:
                BasicMetadata.print_all_basic_metadata(path, image)
                
            with open(path, "rb") as f:
                data = f.read()
                
            data_info = cls.parse_jpeg_sof(data)
            
            print(f"{Color.GREEN}===== SOF Data ====={Color.RESET}")
            
            for key, value in data_info.items():
                BasicMetadata.print_tag_value(f"{Color.GREEN}{key:20}", value)

        except Exception as e:
            print(f"{Color.RED}Error loading JPEG metadata: {e}{Color.RESET}")
            