from PIL import Image
import struct


from src.BasicMetadata import BasicMetadata
from src.Color import Color

class GIFAnalyzer:
    @staticmethod
    def parse_gif(data: bytes, data_info: dict) -> int:
        def skip_sub_blocks(data: bytes, i: int) -> int:
            # sub-blocks: [size][payload...][size][payload...] ... [0x00]
            while i < len(data):
                size = data[i]
                i += 1
                if size == 0:
                    break
                i += size
            return i

        # Skip color table if present, return new index
        def skip_color_table(packed: bytes, i: int) -> int:
            ct_flag = (packed >> 7) & 1
            ct_size = 2 ** ((packed & 0b111) + 1)
            if ct_flag:
                i += 3 * ct_size  # 3 bytes per color
            return i
        
        def handle_extension(data: bytes, i: int, data_info: dict) -> int:
            i += 1  # skip extension introducer (0x21)
            if i >= len(data):
                return -1
            label = data[i]
            i += 1  # skip label
            match label:
                case 0xF9:  # Graphic Control Extension
                    block_size = data[i]
                    if block_size != 4:
                        raise ValueError(f"Unexpected Global Control Extension block size: {block_size}")
                    # skip graphic control extension block 
                    # + 1 byte block size 
                    # + 4 bytes data(1 packed fields + 2 bytes delay time + 1 byte transparent color index) 
                    # + 1 byte block terminator
                    i += 6
                case 0xFE:  # Comment Extension
                    comment = ""
                    while i < len(data):
                        block_size = data[i]
                        i += 1
                        if block_size == 0:  # bloc de taille 0 = fin
                            break
                        comment += data[i : i + block_size].decode("latin-1", errors="replace")
                        i += block_size
                    data_info.update({
                        f"{Color.BLUE}===== Chunk Comment Extension ": "",
                        f"{Color.BLUE}Comment": comment})
                case 0xFF:  # Application Extension
                    block_size = data[i]
                    if block_size != 11:
                        raise ValueError(f"Unexpected Application Extension block size: {block_size}")
                    
                    data_info.update({
                        f"{Color.BLUE}===== Chunk Application Extension ": "",
                        f"{Color.BLUE}App Identifier": BasicMetadata.decode_value(data[i+1:i+9]),
                        f"{Color.BLUE}App Auth Code": BasicMetadata.decode_value(data[i+9:i+12])})

                    i += 12 # skip application block header (1 size + 8 identifier + 3 auth code)
                    i = skip_sub_blocks(data, i)
                case 0x01: # PlainText
                    i = skip_sub_blocks(data, i)

            return i
        
        def handle_image_descriptor(data: bytes, i: int) -> int:
            i += 1  # skip image separator
            if i + 9 > len(data):
                return -1

            left, top, w, h, ipacked = struct.unpack_from("<HHHHB", data, i)
            i += 9  # skip image descriptor: left(2), top(2), w(2), h(2), packed(1)

            i = skip_color_table(ipacked, i)

            if i >= len(data):
                return -1

            i += 1  # skip LZW min code size (toujours 1 octet)

            i = skip_sub_blocks(data, i)  # skip image data sub-blocks
            return i
        
        def parse_gif_header(data: bytes, i: int, data_info: dict) -> int:
            signature = data[0:6]
            if signature[:3] != b"GIF":
                raise ValueError("Not a GIF")
            # screen descriptor: ( 2 + 2 + 1 + 1 + 1 )
            screen_width, screen_height, packed, bg_color_index, aspect = (
                struct.unpack_from("<HHBBB", data, i)
            )
            
            data_info.update({
                f"{Color.GREEN}===== GIF Header ": "",
                f"{Color.GREEN}Signature": BasicMetadata.decode_value(signature.decode()),
                f"{Color.GREEN}Signature hex": signature.hex(' ').upper(),
                f"{Color.GREEN}Screen Width": screen_width,
                f"{Color.GREEN}Screen Height": screen_height,
                f"{Color.GREEN}Backgrnd Color Idx": bg_color_index,
                f"{Color.GREEN}G Color Table Flag": (packed >> 7) & 1
            })
            if aspect != 0:
                data_info[f"{Color.GREEN}Pixel Aspect Ratio"] = f"{(aspect + 15) / 64:.2f}"
            else:
                data_info[f"{Color.GREEN}Pixel Aspect Ratio"] = "Not specified"
            
            return packed
        
        i = 6 # après la signature de 6 octets
        packed = parse_gif_header(data, i, data_info)
        i += 7  # skip screen descriptor ( 2 + 2 + 1 + 1 + 1 )
        
        # skip global color table if present
        ct_flag = (packed >> 7) & 1
        ct_size = 2 ** ((packed & 0b111) + 1)
        if ct_flag:
            data_info.update({
                f"{Color.GREEN}G Color Table Size": ct_size,
                f"{Color.GREEN}G Color Table Bytes": ct_size * 3})
            i += 3 * ct_size 
            
        frames = 0
        while i < len(data):
            if i == -1:
                break
            match data[i]:
                case 0x3B:  # Trailer
                    break
                case 0x21:  # Extension
                    i = handle_extension(data, i, data_info)
                case 0x2C:  # Image Descriptor (frame)
                    frames += 1
                    i = handle_image_descriptor(data, i)
                case _:  # Invalide
                    i += 1

        data_info.update({
            f"{Color.ORANGE}===== Frames Info ": "",
            f"{Color.ORANGE}Frame Count": frames})
        
        return frames
    
    @classmethod
    def analyze_image(cls, path: str) -> None:
        try:
            with Image.open(path) as image:
                BasicMetadata.print_all_basic_metadata(path, image)
                duration = image.info.get('duration')
                
            with open(path, "rb") as f:
                data = f.read()
            
            data_info  = {}
            frames = cls.parse_gif(data, data_info)
            
            if duration is not None:
                data_info.update({f"{Color.ORANGE}One frame duration (ms)": duration,
                                  f"{Color.ORANGE}Total time (s)": f"{(duration * frames / 1000):.2f}"})
            
            for key, value in data_info.items():
                BasicMetadata.print_tag_value(f"{key:25}", value)
                
        except Exception as e:
            print(f"{Color.RED}Error loading GIF metadata: {e}{Color.RESET}")
