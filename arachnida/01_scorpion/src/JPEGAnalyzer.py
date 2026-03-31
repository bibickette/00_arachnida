import struct
from PIL import Image

from src.BasicMetadata import BasicMetadata
from src.Color import Color

class JPEGAnalyzer:
    @staticmethod
    def print_tag_value(tag, value) -> None:
        print(f"{tag}:{Color.RESET} {value}")
            
    
    @classmethod
    def parse_jpeg_sof(cls, path: str) -> dict:
        def get_exif_byte_order(data: bytes) -> str:
            # chercher "Exif\x00\x00" puis lire II ou MM juste après
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
        
        # On lit tous les octets du fichier
        with open(path, "rb") as f:
            data = f.read()

        i = 0
        while i < len(data) - 1:
            
            # Étape 1 : est-ce qu'on est sur un marqueur ?
            # Tous les marqueurs JPEG commencent par l'octet 0xFF
            if data[i] != 0xFF:
                i += 1
                continue

            # Étape 2 : lire les 2 octets du marqueur
            # ">H" = big-endian, unsigned short (2 octets)
            marker = struct.unpack(">H", data[i:i+2])[0]
            # ex: data[i:i+2] = b'\xFF\xC0' → marker = 0xFFC0

            # Étape 3 : est-ce un marqueur SOF ?
            if marker in SOF_MARKERS:
                if marker == 0xFFE1: # APP1
                    result["ExifByteOrder"] = get_exif_byte_order(data)
                else: # SOF
                    result["EncodingProcess"] = SOF_MARKERS[marker]
                    # SOF_MARKERS[0xFFC0] = "Baseline DCT, Huffman coding"

                    # Structure du segment SOF après le marker (2 octets) :
                    # [i]   [i+1]  → marker        (FF C0) déjà lu
                    # [i+2] [i+3]  → longueur      (00 11) = 17 octets
                    # [i+4]        → bits/sample   (08)    = 8
                    # [i+5] [i+6]  → hauteur       (07 D0) = 2000
                    # [i+7] [i+8]  → largeur       (0B B8) = 3000
                    # [i+9]        → nb composants (03)    = 3
                    result["BitsPerSample"]   = data[i+4]
                    # data[i+4] est un seul octet, pas besoin de struct

                    result["ImageHeight"]     = struct.unpack(">H", data[i+5:i+7])[0]
                    result["ImageWidth"]      = struct.unpack(">H", data[i+7:i+9])[0]
                    result["ColorComponents"] = data[i+9]

                    # Étape 4 : lire le sous-échantillonnage
                    # Après [i+9] (nb composants), chaque composant = 3 octets :
                    # [i+10] → id composant  (01 = Y, 02 = Cb, 03 = Cr)
                    # [i+11] → sampling byte (22 = 0010 0010)
                    # [i+12] → table quant.  (on s'en fiche)

                    # Le byte sampling 0x22 = 0010 0010 en binaire
                    # 4 bits de gauche = échantillonnage horizontal = 2
                    # 4 bits de droite = échantillonnage vertical   = 2
                    # → sous-échantillonnage Y = 2x2

                    y_sampling = data[i+11]
                    y_h = (y_sampling >> 4) & 0xF   # décale 4 bits à droite → garde les 4 de gauche
                    y_v = y_sampling & 0xF           # masque → garde les 4 bits de droite

                    SUBSAMPLING_MAP = {
                        (2, 2): "YCbCr4:2:0 (2 2)",
                        (2, 1): "YCbCr4:2:2 (2 1)",
                        (1, 1): "YCbCr4:4:4 (1 1)",
                        (4, 1): "YCbCr4:1:1 (4 1)",
                    }
                    result["YCbCrSubSampling"] = SUBSAMPLING_MAP.get((y_h, y_v), f"{y_h}x{y_v}")

                    break  # on a trouvé le SOF, inutile de continuer
                
            # Étape 5 : si ce n'est pas un SOF, sauter ce segment
            if marker in (0xFFD8, 0xFFD9):
                # SOI et EOI n'ont pas de longueur, juste 2 octets
                i += 2
            else:
                # Les autres segments ont une longueur encodée en [i+2:i+4]
                # Cette longueur INCLUT ses propres 2 octets mais PAS les 2 du marker
                seg_len = struct.unpack(">H", data[i+2:i+4])[0]
                i += 2 + seg_len
                # ex: longueur = 16 → on saute 2 (marker) + 16 (segment) = 18 octets
            

        return result
    
    
    @classmethod
    def print_sof_data(cls, sof_data: dict) -> None:
        if sof_data:
            print(f"{Color.GREEN}===== SOF Data ====={Color.RESET}")
            for key, value in sof_data.items():
                cls.print_tag_value(f"{Color.GREEN}{key:20}", value)
        else:
            print(f"{Color.RED}===== No SOF data found or unable to parse ====={Color.RESET}")


    @classmethod
    def analyze_image(cls, path: str) -> None:
        try:
            with Image.open(path) as image:
                BasicMetadata.print_all_basic_metadata(path, image)
                
                sof = cls.parse_jpeg_sof(path)
                cls.print_sof_data(sof)

        except Exception as e:
            print(f"{Color.RED}Error loading JPEG metadata: {e}{Color.RESET}")
            