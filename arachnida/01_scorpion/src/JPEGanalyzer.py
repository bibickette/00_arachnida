import struct
from PIL import Image, ExifTags, ImageCms
import io

from src.BasicMetadata import BasicMetadata

    
class JPEGAnalyzer:
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RESET = "\033[0m" 
    
    @classmethod
    def print_tag_value(cls, tag, value) -> None:
        print(f"{cls.YELLOW}{tag:20}:{cls.RESET} {value}")
    
    @staticmethod
    def decode_icc_profile(icc_bytes: bytes) -> dict:
        profile = ImageCms.ImageCmsProfile(io.BytesIO(icc_bytes))
        info = ImageCms.getProfileInfo(profile)     
        return {
            "Description"   : ImageCms.getProfileDescription(profile),
            "Copyright"     : ImageCms.getProfileCopyright(profile),
            "Manufacturer"  : ImageCms.getProfileManufacturer(profile),
            "Model"         : ImageCms.getProfileModel(profile),
            "Info"          : info.strip() if info else None,
        }
    
    @classmethod
    def print_exif_data(cls, exif_data: dict) -> None:
        if exif_data:
            print(f"{cls.GREEN}EXIF Metadata:{cls.RESET}")
            for tag_id in exif_data:
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                data = exif_data.get(tag_id)
                if isinstance(data, bytes):
                    data = data.decode()
                cls.print_tag_value(tag, data)
            print(f"{cls.GREEN}End of EXIF Metadata{cls.RESET}")
            

    def print_image_info_items(self, image: Image) -> None:
        print(f"{self.GREEN}Image Info Items:{self.RESET}")
        for key, value in image.info.items():
            if isinstance(value, bytes):                
                print(f"{self.YELLOW}{key:20}:{self.RESET} <bytes length={len(value)}>")
                if(key.lower() == "icc_profile"):
                    print(f"{self.GREEN}Decoded ICC Profile:{self.RESET}")
                    decoded = self.decode_icc_profile(value)
                    for subkey, subvalue in decoded.items():
                        print(f"{self.YELLOW}{'':5}{subkey:20}:{self.RESET} {subvalue}")
                    print(f"{self.GREEN}End of ICC Profile{self.RESET}")
                elif key.lower() == "xmp":
                    print(f"{self.GREEN}Decoded XMP Metadata:{self.RESET}")
                    # print(f"{'':5}XMP Data: {value.decode()}")
                    print(f"{self.GREEN}End of XMP Metadata{self.RESET}")
            elif isinstance(value, tuple):
                print(f"{self.YELLOW}{key:20}:{self.RESET} {', '.join(map(str, value))}")
                
            elif(isinstance(value, dict)):
                print(f"{self.YELLOW}{key:20}:{self.RESET} {value}")
                for subkey, subvalue in value.items():
                    if(isinstance(subvalue, bytes)):
                        print(f"{self.YELLOW}{'':5}{subkey}:{self.RESET} <bytes length={len(subvalue)}>")
                        subvalue = subvalue.decode()
                    print(f"{self.YELLOW}{'':5}{subkey} decoded :{self.RESET} '{subvalue}'")

            else:
                if "xml" in key.lower():
                    print(f"{self.GREEN}XML data{self.RESET}")
                    # print(f"{key:20}: {value}")
                    print(f"{self.GREEN}end XML data{self.RESET}")
                    
                else:
                    self.print_tag_value(key, value)
        print(f"{self.GREEN}End of Info Items{self.RESET}")
        
                                    
    def get_exif_byte_order(self, path: str) -> str:
        with open(path, "rb") as f:
            data = f.read()
        # chercher "Exif\x00\x00" puis lire II ou MM juste après
        idx = data.find(b"Exif\x00\x00")
        if idx == -1:
            return None
        tiff_start = idx + 6
        order = data[tiff_start:tiff_start+2]
        if order == b"II":
            return "Little-endian (Intel, II)"
        elif order == b"MM":
            return "Big-endian (Motorola, MM)"
        return None
    
    
    def parse_jpeg_sof(self, path: str) -> dict:
        SOF_MARKERS = {
            # Délimiteurs de base
            0xFFD8: "SOI - Start Of Image",
            0xFFD9: "EOI - End Of Image",

            # Start Of Frame (type de compression)
            0xFFC0: "SOF0 - Baseline DCT, Huffman coding",
            0xFFC1: "SOF1 - Extended sequential DCT, Huffman",
            0xFFC2: "SOF2 - Progressive DCT, Huffman",
            0xFFC3: "SOF3 - Lossless, Huffman",
            0xFFC9: "SOF9 - Extended sequential DCT, Arithmetic",
            0xFFCA: "SOF10 - Progressive DCT, Arithmetic",

            # Tables
            0xFFC4: "DHT - Define Huffman Table",
            0xFFDB: "DQT - Define Quantization Table",

            # Segments APP (métadonnées)
            0xFFE0: "APP0 - JFIF",
            0xFFE1: "APP1 - EXIF ou XMP",
            0xFFE2: "APP2 - ICC Profile",
            0xFFE3: "APP3 - Meta",
            0xFFEC: "APP12 - Meta",
            0xFFED: "APP13 - IPTC / Photoshop",
            0xFFEE: "APP14 - Adobe",

            # Autres
            0xFFDA: "SOS - Start Of Scan",
            0xFFDD: "DRI - Define Restart Interval",
            0xFFFE: "COM - Comment",
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
                if marker == 0xFFC0:
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
    
    
    def print_sof_data(self, sof_data: dict) -> None:
        if sof_data:
            print(f"{self.GREEN}SOF Data:{self.RESET}")
            for key, value in sof_data.items():
                self.print_tag_value(key, value)

            print(f"{self.GREEN}End of SOF Data{self.RESET}")
        else:
            print(f"{self.GREEN}No SOF data found or unable to parse.{self.RESET}")


    def print_gps_data(self, gps_data: dict) -> None:
        if gps_data:
            print(f"{self.GREEN}\nGPS IFD:{self.RESET}")
            for tag_id, value in gps_data.items():
                tag_name = ExifTags.GPSTAGS.get(tag_id, f"GPS_Tag_{tag_id}")
                if isinstance(value, bytes):
                    value = value.decode()
                self.print_tag_value(tag_name, value)
        else:
            print(f"{self.GREEN}No GPS data found.{self.RESET}")
    
    
    def analyze_image(self, path: str) -> None:
        try:
            image = Image.open(path)
            
            exif_data = image.getexif()
            sof = self.parse_jpeg_sof(path)
            gps_ifd = image.getexif().get_ifd(ExifTags.IFD.GPSInfo)

            BasicMetadata.print_all_basic_metadata(path)
            self.print_exif_data(exif_data)
            self.print_image_info_items(image)
            self.print_sof_data(sof)
            print(f"{self.GREEN}EXIF Byte Order:{self.RESET} {self.get_exif_byte_order(path)}")
            self.print_gps_data(gps_ifd)

        except Exception as e:
            print(f"Error loading metadata: {e}")
            
            
            
# alors le plan cest
# 1. ouvrir limage avec PIL
# 2. afficher les infos de base (filename, size, format, mode)
# 3. afficher les données EXIF (en décodant les bytes si besoin)
# 4. afficher les items de image.info (en décodant les bytes si besoin)
# 5. lire les octets du fichier pour trouver le SOF et extraire les infos de compression, dimensions, échantillonnage
# 6. afficher les métadonnées de base du fichier (taille, dates, permissions)
# 7. afficher l'ordre des octets dans l'EXIF (II ou MM)
# 8. afficher les données GPS si présentes (en décodant les bytes si besoin)
# 9. gérer les erreurs lors de l'ouverture ou de la lecture des métadonnées