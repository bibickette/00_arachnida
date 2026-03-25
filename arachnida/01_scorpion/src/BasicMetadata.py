import mimetypes
import stat
import os
from pathlib import Path
from datetime import datetime
from PIL import Image

class BasicMetadata:
    ORANGE = "\033[38;5;208m"
    RESET = "\033[0m"
    
    @classmethod
    def __print_tag_value(cls, tag, value) -> None:
        print(f"{cls.ORANGE}{tag:20}:{cls.RESET} {value}")


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
        
        cls.__print_tag_value("Path", image.filename)
        cls.__print_tag_value("FileName", p.name)
        cls.__print_tag_value("FileSize", f"{st.st_size} bytes")
        cls.__print_tag_value("ImageSize", image.size)
        cls.__print_tag_value("ImageMode", image.mode)
        cls.__print_tag_value("ImageFormat", image.format)
        cls.__print_tag_value("FileTypeExtension", p.suffix.lstrip(".").lower())
        cls.__print_tag_value("MIMEType", mime or "unknown")
        cls.__print_tag_value("FileModifyDate", datetime.fromtimestamp(st.st_mtime))
        cls.__print_tag_value("FileAccessDate", datetime.fromtimestamp(st.st_atime))
        cls.__print_tag_value("FileInodeChangeDate", datetime.fromtimestamp(st.st_ctime))
        cls.__print_tag_value("FilePermissions", cls.__format_permissions(st.st_mode))
        
        
    @classmethod 
    def print_all_basic_metadata(cls, path: str, image: Image) -> None:
        print(f"{cls.ORANGE}===== Basic Metadata ====={cls.RESET}")
        
        cls.__print_file_metadata(path, image)
        
        # print(f"{cls.GREEN}End of Basic Metadata{cls.RESET}")
        