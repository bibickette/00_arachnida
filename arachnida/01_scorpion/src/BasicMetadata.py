import mimetypes
import stat
import os
from pathlib import Path
from datetime import datetime
from PIL import Image

class BasicMetadata:
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RESET = "\033[0m"
    
    @classmethod
    def __print_tag_value(cls, tag, value) -> None:
        print(f"{cls.YELLOW}{tag:20}:{cls.RESET} {value}")
        
    @classmethod
    def __print_basic_info(cls, image: Image) -> None:
        cls.__print_tag_value("Filename", image.filename)
        cls.__print_tag_value("Image Size", image.size)
        cls.__print_tag_value("Image Format", image.format)
        cls.__print_tag_value("Image Mode", image.mode)


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
    def __get_file_metadata(cls, path: str) -> dict:
        st = os.stat(path)
        p = Path(path)
        mime, _ = mimetypes.guess_type(path)
        return {
            "FileName"        : p.name,
            "FileSize"        : f"{st.st_size} bytes",
            "FileTypeExtension": p.suffix.lstrip(".").lower(),
            "MIMEType"        : mime or "unknown",
            "FileModifyDate"  : datetime.fromtimestamp(st.st_mtime),
            "FileAccessDate"  : datetime.fromtimestamp(st.st_atime),
            "FileInodeChangeDate": datetime.fromtimestamp(st.st_ctime),
            "FilePermissions" : cls.__format_permissions(st.st_mode),
        }
        
        
    @classmethod    
    def __print_basic_metadata(cls, metadata: dict) -> None:
        for key, value in metadata.items():
            cls.__print_tag_value(key, value)
        
        
    @classmethod 
    def print_all_basic_metadata(cls, path: str) -> None:
        print(f"{cls.GREEN}Basic Metadata:{cls.RESET}")
        
        with Image.open(path) as image:
            cls.__print_basic_info(image)
        
        metadata = cls.__get_file_metadata(path)
        cls.__print_basic_metadata(metadata)
        
        print(f"{cls.GREEN}End of Basic Metadata{cls.RESET}")
        