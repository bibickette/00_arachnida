#!/usr/bin/env python3
import os
from PIL import Image, ExifTags, ImageCms
import io
import mimetypes
from datetime import datetime
from pathlib import Path


class JPEGAnalyzer:
    GREEN = "\033[32m"
    RESET = "\033[0m" 
    
    def decode_icc_profile(self, icc_bytes: bytes) -> dict:
        profile = ImageCms.ImageCmsProfile(io.BytesIO(icc_bytes))
        info = ImageCms.getProfileInfo(profile)     
        # print(f"info : {info}")
        # print(f"profile : {profile}")
        # print(f"profile.profile : {profile.profile.red_colorant}")
        
        return {
            "Description"   : ImageCms.getProfileDescription(profile),
            "Copyright"     : ImageCms.getProfileCopyright(profile),
            "Manufacturer"  : ImageCms.getProfileManufacturer(profile),
            "Model"         : ImageCms.getProfileModel(profile),
            "Info"          : info.strip() if info else None,
        }
    
    def get_file_metadata(self, path: str) -> dict:
        stat = os.stat(path)
        p = Path(path)
        mime, _ = mimetypes.guess_type(path)
        return {
            "FileName"        : p.name,
            "FileSize"        : f"{stat.st_size} bytes",
            "FileTypeExtension": p.suffix.lstrip(".").lower(),
            "MIMEType"        : mime or "unknown",
            "FileModifyDate"  : datetime.fromtimestamp(stat.st_mtime),
            "FileAccessDate"  : datetime.fromtimestamp(stat.st_atime),
            "FileInodeChangeDate": datetime.fromtimestamp(stat.st_ctime),
            "FilePermissions" : oct(stat.st_mode),
        }

    def print_exif_data(self, image: Image) -> None:
        exif_data = image.getexif()
        if exif_data:
            print(f"{self.GREEN}\nEXIF Metadata:{self.RESET}")
            for tag_id in exif_data:
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                data = exif_data.get(tag_id)
                if isinstance(data, bytes):
                    data = data.decode()
                print(f"{tag:25}: {data}")
            print(f"{self.GREEN}End of EXIF Metadata{self.RESET}\n")
            

    def print_image_info_items(self, image: Image) -> None:
        print(f"{self.GREEN}\nImage Info Items:{self.RESET}")
        for key, value in image.info.items():
            if isinstance(value, bytes):
                print(f"{key:20}: <bytes length={len(value)}>")
                if(key.lower() == "icc_profile"):
                    print(f"{self.GREEN}Decoded ICC Profile:{self.RESET}")
                    decoded = self.decode_icc_profile(value)
                    for subkey, subvalue in decoded.items():
                        print(f"{subkey}: {subvalue}")
                    print(f"{self.GREEN}End of ICC Profile{self.RESET}\n")
                elif (key.lower() == "exif"):
                    self.print_exif_data(image)

            elif isinstance(value, tuple):
                print(f"{key:20}: {', '.join(map(str, value))}")

            else:
                print(f"{key:20}: {value}")
                
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
    
    def analyze_image(self, path: str) -> None:
        try:
            image = Image.open(path)
            print(f"Filename: {image.filename}")
            print(f"Image Size: {image.size}")
            print(f"Image Format: {image.format}")
            print(f"Image Mode: {image.mode}")
            
            self.print_exif_data(image)
            self.print_image_info_items(image)
            
            file_data = self.get_file_metadata(path)
            for subkey, subvalue in file_data.items():
                print(f"{subkey}: {subvalue}")
                
            print(f"EXIF Byte Order: {self.get_exif_byte_order(path)}")
        
        except Exception as e:
            print(f"Error loading metadata: {e}")