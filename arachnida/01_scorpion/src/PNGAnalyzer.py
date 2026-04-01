# import struct
from PIL import Image


from src.BasicMetadata import BasicMetadata
from src.JPEGAnalyzer import JPEGAnalyzer
from src.Color import Color
class PNGAnalyzer:
    
    @classmethod
    def analyze_image(cls, path: str) -> None:
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
        
        # analyze png image
        try:
            
            
            with Image.open(path) as image:
                BasicMetadata.print_all_basic_metadata(path, image)
                
                def parse_png_ihdr(data: bytes) -> dict:
                    print(f"{Color.BLUE}{'PNG Signature':20}:{Color.RESET} {data[:8].hex(' ').upper()}")
                    # Sauter la signature (8 octets)
                    i = 8
                    chunks = {}
                    while i < len(data):
                        length = int.from_bytes(data[i:i+4], 'big')
                        
                        chunk_type = data[i+4:i+8].decode('ascii')
                        chunk_data = data[i+8:i+8+length]
                        # CRC = data[i+8+length:i+12+length]
                        
                        if chunk_type == 'IHDR':   # dimensions, bit depth...
                            chunks['width']  = int.from_bytes(chunk_data[0:4], 'big')
                            chunks['height'] = int.from_bytes(chunk_data[4:8], 'big')
                            chunks['bit_depth'] = chunk_data[8]
                            chunks['color_type'] = decode_png_value('color_type', chunk_data[9])
                            chunks['compression_method'] = decode_png_value('compression_method', chunk_data[10])
                            chunks['filter_method'] = decode_png_value('filter_method', chunk_data[11])
                            chunks['interlace_method'] = decode_png_value('interlace_method', chunk_data[12])

                        elif chunk_type == 'tEXt': # métadonnées texte
                            key, val = chunk_data.split(b'\x00', 1)
                            chunks[BasicMetadata.decode_value(key)] = BasicMetadata.decode_value(val)

                        
                        i += 12 + length  # 4 length + 4 type + data + 4 CRC
                    return chunks
                
                with open(path, 'rb') as f:
                    data = f.read()
                print(f"\n{Color.BLUE}===== PNG Metadata from IHDR Chunk ====={Color.RESET}")
                png_metadata = parse_png_ihdr(data)
                for key, value in png_metadata.items():
                    JPEGAnalyzer.print_tag_value(f"{Color.BLUE}{key:20}", decode_png_value(key, value))
                        
        except Exception as e:
            print(f"{Color.RED}Error loading PNG metadata: {e}{Color.RESET}")
            
# The IHDR chunk must appear FIRST. It contains:

#    Width:              4 bytes
#    Height:             4 bytes
#    Bit depth:          1 byte
#    Color type:         1 byte
#    Compression method: 1 byte
#    Filter method:      1 byte
#    Interlace method:   1 byte
# The iTXt, tEXt, and zTXt chunks are used for conveying textual information associated with the image. This specification refers to them generically as "text chunks".

# Each of the text chunks contains as its first field a keyword that indicates the type of information represented by the text string. The following keywords are predefined and should be used where appropriate:

#    Title            Short (one line) title or caption for image
#    Author           Name of image's creator
#    Description      Description of image (possibly long)
#    Copyright        Copyright notice
#    Creation Time    Time of original image creation
#    Software         Software used to create the image
#    Disclaimer       Legal disclaimer
#    Warning          Warning of nature of content
#    Source           Device used to create the image
#    Comment          Miscellaneous comment; conversion from
#                     GIF comment

# 3.1. PNG file signature
# The first eight bytes of a PNG file always contain the following (decimal) values: