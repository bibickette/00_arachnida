import os
import io
import stat
import mimetypes
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from PIL import Image, ExifTags, ImageCms

from src.Color import Color

class BasicMetadata:
    
    @staticmethod  
    def __print_tag_value(tag, value) -> None:
        print(f"{Color.ORANGE}{tag:20}:{Color.RESET} {value}")


    @staticmethod
    def __format_permissions(mode: int) -> str:
        perms = ""
        # type de fichier
        if stat.S_ISDIR(mode):  perms += "d"
        elif stat.S_ISLNK(mode): perms += "l"
        else:                    perms += "-"

        # owner, group, other — chacun sur 3 bits : rwx
        for who in ["USR", "GRP", "OTH"]:
            perms += "r" if mode & getattr(stat, f"S_IR{who}") else "-"
            perms += "w" if mode & getattr(stat, f"S_IW{who}") else "-"
            perms += "x" if mode & getattr(stat, f"S_IX{who}") else "-"

        return perms  # → "-rw-rw-rw-"
    
    
    @classmethod
    def __print_file_metadata(cls, path: str, image: Image) -> dict:
        st = os.stat(path)
        p = Path(path)
        mime, _ = mimetypes.guess_type(path)
        
        data = {
            "Path": image.filename,
            "FileName": p.name,
            "FileSize": f"{st.st_size} bytes",
            "ImageSize": image.size,
            "ImageMode": image.mode,
            "ImageFormat": image.format,
            "FileTypeExtension": p.suffix.lstrip(".").lower(),
            "MIMEType": mime or "unknown",
            "FileModifyDate": datetime.fromtimestamp(st.st_mtime),
            "FileAccessDate": datetime.fromtimestamp(st.st_atime),
            "FileInodeChangeDate": datetime.fromtimestamp(st.st_ctime),
            "FilePermissions": cls.__format_permissions(st.st_mode)
        }
        
        for key, value in data.items():
            cls.__print_tag_value(key, value)
            

    @classmethod
    def __print_gps_data(cls, gps_data: dict) -> None:
        if gps_data:
            print(f"{Color.PURPLE}===== GPS IFD ====={Color.RESET}")
            for tag_id, value in gps_data.items():
                tag_name = ExifTags.GPSTAGS.get(tag_id, f"GPS_Tag_{tag_id}")
                cls.__print_tag_value(f"{Color.PURPLE}{tag_name:20}", cls.decode_value(value))
        else:
            print(f"{Color.RED}===== No GPS data found ====={Color.RESET}")
            
    @classmethod
    def __print_exif_data(cls, exif_data: dict) -> None:
        if exif_data:
            print(f"{Color.BLUE}===== EXIF Metadata ====={Color.RESET}")
            for tag_id in exif_data:
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                data = exif_data.get(tag_id)
                cls.__print_tag_value(f"{Color.BLUE}{tag:20}", cls.decode_value(data))
        else:
            print(f"{Color.RED}===== No EXIF data found ====={Color.RESET}")
    
    
    @classmethod
    def __print_xmp_data(cls, key, value) -> None:
        def decode_xmp_value(key: str, value: str) -> str:
            XMP_VALUE_DECODERS = {
                "tiff:ResolutionUnit": {
                    "1": "No absolute unit",
                    "2": "inch",
                    "3": "centimeter",
                },
                "tiff:Compression": {
                    "1": "Uncompressed",
                    "5": "LZW",
                    "6": "JPEG",
                    "8": "Deflate",
                },
                "tiff:PhotometricInterpretation": {
                    "0": "WhiteIsZero",
                    "1": "BlackIsZero",
                    "2": "RGB",
                    "3": "Palette color",
                },
            }
            decoder = XMP_VALUE_DECODERS.get(key, {})
            return decoder.get(str(value), value)
        
        def parse_xmp(xmp_data) -> dict:
            if isinstance(xmp_data, bytes):
                xmp_data = xmp_data.decode("utf-8", errors="replace")

            root = ET.fromstring(xmp_data)
            result = {}

            def extract(element, depth=0):
                def clean_tag(raw_tag: str) -> str:
                    XMP_NAMESPACES = {
                        "http://ns.adobe.com/tiff/1.0/"                  : "tiff",
                        "http://purl.org/dc/elements/1.1/"               : "dc",
                        "http://iptc.org/std/Iptc4xmpExt/2008-02-29/"    : "Iptc4xmpExt",
                        "http://ns.adobe.com/xap/1.0/"                   : "xmp",
                        "http://ns.adobe.com/photoshop/1.0/"             : "photoshop",
                        "http://ns.adobe.com/xap/1.0/rights/"            : "xmpRights",
                        "http://www.w3.org/1999/02/22-rdf-syntax-ns#"    : "rdf",
                        "adobe:ns:meta/"                                  : "x",
                    }
                    # raw_tag = "{http://ns.adobe.com/tiff/1.0/}DocumentName"
                    if "}" not in raw_tag:
                        return raw_tag
                    uri, localname = raw_tag[1:].split("}", 1)
                    prefix = XMP_NAMESPACES.get(uri, uri.split("/")[-1])
                    return f"{prefix}:{localname}"
                    # → "tiff:DocumentName"
                    
                    
                # extract
                for child in element:
                    tag = clean_tag(child.tag)
                    # Cas 1 : élément avec du texte direct
                    # <tiff:DocumentName>goacute</tiff:DocumentName>
                    if child.text and child.text.strip():
                        result[tag] = child.text.strip()
                    # Cas 2 : élément avec des attributs
                    # <rdf:Description rdf:about="" ...>
                    for attr_key, attr_val in child.attrib.items():
                        clean_attr = clean_tag(attr_key)
                        if clean_attr not in ("rdf:about",) and attr_val.strip():
                            result[clean_attr] = attr_val
                    # Cas 3 : élément imbriqué → descendre
                    # <dc:title><rdf:Alt><rdf:li>goacute</rdf:li></rdf:Alt></dc:title>
                    extract(child, depth + 1)
                    
                    
            # parse xmp
            extract(root)
            return result
        
        
        # print xmp data 
        data = parse_xmp(value)
        for key, value in data.items():
            readable = decode_xmp_value(key, value)
            print(f"{Color.PURPLE}{'':5}{key:20}:{Color.RESET} {readable}")

    
    @classmethod
    def __print_image_info_items(cls, image: Image) -> None:
        def decode_icc_profile(icc_bytes: bytes) -> dict:
            profile = ImageCms.ImageCmsProfile(io.BytesIO(icc_bytes))
            info = ImageCms.getProfileInfo(profile)
            data = {
                'Description': ImageCms.getProfileDescription(profile),
                'Copyright': ImageCms.getProfileCopyright(profile),
                'Manufacturer': ImageCms.getProfileManufacturer(profile),
                'Model': ImageCms.getProfileModel(profile),
                'Info': info.strip() if info else None,
            }
            for key, value in data.items():
                cls.__print_tag_value(f"{Color.PURPLE}{'':5}{key:20}", value)
        
        print(f"{Color.YELLOW}===== Image Info Items ====={Color.RESET}")
        for key, value in image.info.items():
            if "xmp" in key.lower():
                print(f"{Color.YELLOW}{key:20}:{Color.RESET} <bytes length={len(value)}>")
                cls.__print_xmp_data(key, value)
            elif isinstance(value, bytes):                
                print(f"{Color.YELLOW}{key:20}:{Color.RESET} <bytes length={len(value)}>")
                if(key.lower() == "icc_profile"):
                    decode_icc_profile(value)
                elif key.lower() != "exif":
                    cls.__print_tag_value(f"{Color.PURPLE}{'':5}{'decoded':20}", cls.decode_value(value))
            else:
                cls.__print_tag_value(f"{Color.YELLOW}{key:20}", cls.decode_value(value))
                
    @staticmethod
    def decode_value(value) -> str:
        decoded = ""
        try:
            decoded = value.decode()
        except Exception as e:
            decoded = value
            
        return decoded
                               
    @classmethod 
    def print_all_basic_metadata(cls, path: str, image: Image) -> None:
        print(f"{Color.ORANGE}===== Basic Metadata ====={Color.RESET}")
        
        cls.__print_file_metadata(path, image)
        
        exif_data = image.getexif()
        gps_ifd = exif_data.get_ifd(ExifTags.IFD.GPSInfo)
        cls.__print_exif_data(exif_data)
        cls.__print_gps_data(gps_ifd)
        
        cls.__print_image_info_items(image)
        
        # print(f"{Color.GREEN}End of Basic Metadata{Color.RESET}")
        