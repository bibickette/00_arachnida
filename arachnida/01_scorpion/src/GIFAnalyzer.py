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

def count_gif_frames(data: bytes) -> int:
    if len(data) < 13 or data[:3] != b"GIF":
        raise ValueError("Not a GIF")

    i = 6  # header
    # LSD
    width, height, packed, bg, aspect = struct.unpack_from("<HHBBB", data, i)
    i += 7

    # Global Color Table?
    gct_flag = (packed >> 7) & 1
    gct_size = 2 ** ((packed & 0b111) + 1)
    if gct_flag:
        i += 3 * gct_size  # 3 bytes per color

    frames = 0

    while i < len(data):
        b = data[i]

        if b == 0x3B:  # Trailer
            break

        if b == 0x21:  # Extension
            if i + 1 >= len(data):
                break
            label = data[i + 1]
            i += 2

            if label == 0xF9:  # Graphic Control Extension
                # block size should be 4, then 4 bytes, then terminator 0
                if i >= len(data):
                    break
                block_size = data[i]
                i += 1 + block_size  # skip fixed data
                if i < len(data) and data[i] == 0x00:
                    i += 1
            else:
                # Comment(0xFE), Application(0xFF), PlainText(0x01)
                # They all use sub-blocks after an initial fixed part in some cases.
                if label == 0xFE:  # Comment Extension
                    comment = ""
                    while i < len(data):
                        block_size = data[i]
                        i += 1
                        if block_size == 0:    # bloc de taille 0 = fin
                            break
                        comment += data[i:i+block_size].decode("latin-1", errors="replace")
                        i += block_size
                    print(f"{Color.BLUE}Comment Extension:{Color.RESET} {comment}")
                elif label == 0x01:
                    # plain text extension has 1 byte block size (should be 12) + that many bytes
                    if i >= len(data):
                        break
                    pt_block_size = data[i]
                    i += 1 + pt_block_size
                # then sub-blocks
                i = skip_sub_blocks(data, i)

            continue

        if b == 0x2C:  # Image Descriptor (frame)
            frames += 1
            i += 1
            if i + 9 > len(data):
                break

            # descriptor: left(2), top(2), w(2), h(2), packed(1)
            left, top, w, h, ipacked = struct.unpack_from("<HHHHB", data, i)
            i += 9

            # Local Color Table?
            lct_flag = (ipacked >> 7) & 1
            lct_size = 2 ** ((ipacked & 0b111) + 1)
            if lct_flag:
                i += 3 * lct_size

            # LZW min code size
            if i >= len(data):
                break
            i += 1

            # image data sub-blocks
            i = skip_sub_blocks(data, i)
            continue

        # Si on tombe sur un octet inattendu, on avance (ou on peut raise)
        i += 1

    return frames

class GIFAnalyzer:
    @classmethod
    def analyze_image(cls, path: str) -> None:
        # Implement GIF analysis logic here
        try:
            with Image.open(path) as image:
                BasicMetadata.print_all_basic_metadata(path, image)
                exif_data = image.getexif()
                JPEGAnalyzer.print_exif_data(exif_data)
                JPEGAnalyzer.print_image_info_items(image)
                with open(path, "rb") as f:
                    data = f.read()
                print(f"gif signature : {data[0:6].decode()}")
                print(f"gif signature hex: {data[0:6].hex(' ').upper()}")
                print(f"screen width : {int.from_bytes(data[6:8], 'little')}")
                print(f"screen height : {int.from_bytes(data[8:10], 'little')}")
                print(f"global color table flag : {data[10] >> 7}")
                print(f"background color index : {data[11]}")

                print(f"count gif frames : {count_gif_frames(data)}")
                # frame_count = 0
                # while i < len(data):  # Look for gif terminator
                #     if data[i] == 0x3B:  # Trailer
                #         print(f"Trailer found at offset: {i}, data: {data[i]}")
                #     if data[i] == 0x2C:  # Image Descriptor
                #         print(f"Image Descriptor found at offset: {i}, data: {data[i]}")
                #         frame_count += 1
                #     i += 1
                # print(f"i : {i}, data[i]: {data[i] if i < len(data) else 'EOF'}")
                # print(f"Frame Count: {frame_count}")
                # # # print(f"data : {data[i:i+10]}")
                # while i < len(data):
                #     print(f"data : {data[i:i+10]}")
                #     i += 10
        
                
                
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
