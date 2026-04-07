from PIL import Image

from src.BasicMetadata import BasicMetadata
from src.Color import Color
class PNGAnalyzer:
    @staticmethod
    def parse_png_ihdr(data: bytes) -> dict:
        def decode_png_value(key: str, value: str) -> str:
            PNG_VALUE_DECODER = {
                "color_type": {
                    "0": "Grayscale",
                    "2": "Truecolor",
                    "3": "Indexed-color",
                    "4": "Grayscale with alpha",
                    "6": "Truecolor with alpha"
                },
                "compression_method": {
                    "0": "Deflate/inflate"
                },
                "filter_method": {
                    "0": "Adaptive filtering with five basic filter types"
                },
                "interlace_method": {
                    "0": "No interlace",
                    "1": "Adam7 interlace"
                }
            }
            
            decoder = PNG_VALUE_DECODER.get(key, {})
            return decoder.get(str(value), value)
        data_info = {}
        data_info["PNG Signature"] = data[:8].hex(' ').upper()
        i = 8
        while i < len(data):
            length = int.from_bytes(data[i:i+4], 'big')
            
            chunk_type = data[i+4:i+8].decode('ascii')
            chunk_data = data[i+8:i+8+length]
            # CRC = data[i+8+length:i+12+length]
            
            if chunk_type == 'IHDR':
                data_info['width']  = int.from_bytes(chunk_data[0:4], 'big')
                data_info['height'] = int.from_bytes(chunk_data[4:8], 'big')
                data_info['bit_depth'] = chunk_data[8]
                data_info['color_type'] = decode_png_value('color_type', chunk_data[9])
                data_info['compression_method'] = decode_png_value('compression_method', chunk_data[10])
                data_info['filter_method'] = decode_png_value('filter_method', chunk_data[11])
                data_info['interlace_method'] = decode_png_value('interlace_method', chunk_data[12])
            elif chunk_type == 'tEXt':
                key, val = chunk_data.split(b'\x00', 1)
                data_info[f"Text - {BasicMetadata.decode_value(key)}"] = BasicMetadata.decode_value(val)
            else:
                data_info[f"Chunk - {chunk_type}"] = f"{length} bytes"
            
            i += 12 + length  # 4 length + 4 type + data + 4 CRC
        return data_info
    
    @classmethod
    def analyze_image(cls, path: str) -> None:
        try:
            with Image.open(path) as image:
                BasicMetadata.print_all_basic_metadata(path, image)
                
            with open(path, 'rb') as f:
                data = f.read()
            
            data_info = {}    
            data_info = cls.parse_png_ihdr(data)
            
            print(f"\n{Color.BLUE}===== PNG Metadata from IHDR Chunk ====={Color.RESET}")
            
            for key, value in data_info.items():
                BasicMetadata.print_tag_value(f"{Color.BLUE}{key:20}", value)
                        
        except Exception as e:
            print(f"{Color.RED}Error loading PNG metadata: {e}{Color.RESET}")
            