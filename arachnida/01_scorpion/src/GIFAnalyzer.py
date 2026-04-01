from PIL import Image
import struct


from src.BasicMetadata import BasicMetadata
from src.JPEGAnalyzer import JPEGAnalyzer
from src.Color import Color


# print tous les attributs dans image
def print_all_image_attributes(image: Image.Image) -> None:
    try:
        for attr in dir(image):
            if not attr.startswith("_") and not callable(getattr(image, attr)):
                print(f"{Color.YELLOW}{attr:20}:{Color.RESET} {getattr(image, attr)}")
    except Exception as e:
        print(f"{Color.RED}Error loading GIF metadata: {e}{Color.RESET}")


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


def parse_gif(data: bytes):
    def handle_extension(data: bytes, i: int) -> int:
        i += 1  # skip extension introducer (0x21)
        if i >= len(data):
            return -1
        label = data[i]
        i += 1  # skip label
        match label:
            case 0xF9:  # Graphic Control Extension
                # block size should be 4, then 4 bytes, then terminator 0
                i = skip_sub_blocks(data, i)  # skip fixed data
                if i < len(data) and data[i] == 0x00:
                    i += 1
            case 0xFE:  # Comment Extension
                comment = ""
                while i < len(data):
                    block_size = data[i]
                    i += 1
                    if block_size == 0:  # bloc de taille 0 = fin
                        break
                    comment += data[i : i + block_size].decode("latin-1", errors="replace")
                    i += block_size
                print(f"{Color.BLUE}Comment Extension:{Color.RESET} {comment}")
            case 0x01:  # Plain Text Extension
                print(f"plain text value: {data[i:i+12]}")  # 12 bytes de données fixes
            case _: # Comment(0xFE), Application(0xFF), PlainText(0x01)
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
    
    def parse_gif_header(data: bytes, i: int)-> int:
        signature = data[0:6]
        if signature[:3] != b"GIF":
            raise ValueError("Not a GIF")
        # screen descriptor: ( 2 + 2 + 1 + 1 + 1 )
        screen_width, screen_height, packed, bg_color_index, aspect = (
            struct.unpack_from("<HHBBB", data, i)
        )
        
        data = {
            "Signature": BasicMetadata.decode_value(signature.decode()),
            "Signature hex": signature.hex(' ').upper(),
            "Screen Width": screen_width,
            "Screen Height": screen_height,
            "Global Color Table Flag": (packed >> 7) & 1,
            "Background Color Index": bg_color_index
        }
        
        print(f"{Color.GREEN}===== GIF Header ====={Color.RESET}")
        for key, value in data.items():
            BasicMetadata.print_tag_value(f"{Color.GREEN}{key:25}", value)
        return packed

    
    i = 6 # après la signature de 6 octets
    packed = parse_gif_header(data, i)
    i += 7  # skip screen descriptor ( 2 + 2 + 1 + 1 + 1 )
    
    i = skip_color_table(packed, i)
    frames = 0
    while i < len(data):
        if i == -1:
            break
        match data[i]:
            case 0x3B:  # Trailer
                break
            case 0x21:  # Extension
                i = handle_extension(data, i)
            case 0x2C:  # Image Descriptor (frame)
                frames += 1
                i = handle_image_descriptor(data, i)
            case _:  # Invalide
                i += 1
    return frames


class GIFAnalyzer:
    @classmethod
    def analyze_image(cls, path: str) -> None:
        # Implement GIF analysis logic here
        try:
            with Image.open(path) as image:
                BasicMetadata.print_all_basic_metadata(path, image)

                with open(path, "rb") as f:
                    data = f.read()
                    
                print(f"count gif frames parse : {parse_gif(data)}")
                
                n = getattr(image, "n_frames", 1)
                print("n_frames:", n)
                print("is_animated:", getattr(image, "is_animated", n > 1))

                # n = getattr(image, "n_frames", 1)
                # durations = []

                # for i in range(n):
                #     image.seek(i)
                #     durations.append(image.info.get("duration", 0))  # ms

                # total_ms = sum(durations)
                # print("FrameCount:", n)
                # print("FrameDuration (ms):", durations[0] if len(set(durations)) == 1 else "variable")
                # print("TotalDuration:", f"{total_ms/1000:.2f} s")
                # print("Min/Max frame duration (ms):", min(durations), max(durations))
        except Exception as e:
            print(f"{Color.RED}Error loading GIF metadata: {e}{Color.RESET}")
