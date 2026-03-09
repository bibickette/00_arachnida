#!/usr/bin/env python3
import argparse
import sys
from dataclasses import dataclass # permet des creer des classes

@dataclass
class Args:
    r: bool = False
    l: bool = False
    depth: int = 5
    p: bool = False
    path: str = "./data/"
    url: str | None = None

    
def parse_depth(val):
    try:
        return int(val)
    except ValueError:
        return None

## questce qui est accepté :
# repetition de la meme lettre uniquement cote a cote
# repetition colle de plusieurs lettre
# si apparition dune lettre/repetition dune lettre, elle ne peut plus etre repetée

# refusé
# pas de repetition de -

def flag_letter_checker(flag_value : str, compare : str, iterator : int, flag_setted : bool) : 
    if iterator >= len(flag_value) :
        return None, flag_setted
    print(f"letter : {flag_value[iterator]}")
    if flag_value[iterator] == compare :
            if  flag_setted == True :
                print(f"previous {flag_setted} ")
                print("flag already used", file=sys.stderr)
                
                return False,  flag_setted
            flag_setted = True
            while(iterator < len(flag_value) and flag_value[iterator] == compare) :
                iterator += 1
    elif  flag_value[iterator] != "r" and flag_value[iterator] != "l" and flag_value[iterator] != "p" :
        print(f"wrong char : {flag_value[iterator]}", file=sys.stderr)
        return False, flag_setted
    return iterator, flag_setted

def is_valid_flag(flag_value : str, r_used, l_used, p_used) :
    i = 1  # car le char 0 est un -
    value_len = len(flag_value)

    while(i < value_len) :
        i, r_used = flag_letter_checker(flag_value, 'r',  i, r_used)
        i, l_used = flag_letter_checker(flag_value, 'l',  i, l_used)
        i, p_used = flag_letter_checker(flag_value, 'p',  i, p_used)
        if not i or i == False :
            break
        i += 1
    
    if i == False:
        return False, r_used, l_used, p_used
    
    print("end of valid flag")
    return True, r_used, l_used, p_used


def flag_checker(argv, i : int, r_used : bool, l_used : bool, p_used : bool) :
    # print(f"i = {i}")
    if i >= len(argv):
        return False, r_used, l_used, p_used
    arg = sys.argv[i]
    # print(f"arg ===== {arg}")
    if arg.startswith("-") :
            print(f"start analyze ===== {arg}")
            # validation dun flag
            ret, r_used, l_used, p_used = is_valid_flag(arg, r_used, l_used, p_used)
            if not ret :
                return None, r_used, l_used, p_used
    ret, r_used, l_used, p_used = flag_checker(argv, i+1, r_used, l_used, p_used)
    return ret, r_used, l_used, p_used

def arg_check():
    argc = len(sys.argv)
    
    if argc > 7:
        print("Usage: spider.py -r [-l DEPTH] [-p PATH] URL\n", file=sys.stderr)
        print("Maximum of 6 arguments", file=sys.stderr)
        return False

    if argc < 3 :
        print("Usage: spider.py -r [-l DEPTH] [-p PATH] URL\n", file=sys.stderr)
        print("Minimum of 3 arguments", file=sys.stderr)
        return False
    args = Args()
    i = 1
    r_used = False
    l_used = False
    p_used = False 
    ret, r_used, l_used, p_used = flag_checker(sys.argv, i, r_used, l_used, p_used);
    if ret == None:
        print("ret = none")
        print(f"r {r_used} l {l_used} p {p_used}")
        return False
    # while(i < argc):
    #     arg = sys.argv[i]
    #     # detection dun flag
    #     if arg.startswith("-") :
    #         print(f"start analyze ===== {arg}")
    #         # validation dun flag
    #         ret, r_used, l_used, p_used = is_valid_flag(arg, r_used, l_used, p_used)
    #         if not ret :
    #             return False
    #         print(f"{arg} is a flag")
    #     i += 1
    if not r_used :
        # print("Usage: spider.py -r [-l DEPTH] [-p PATH] URL\n", file=sys.stderr)
        # print("Flag -r is needed", file=sys.stderr)
        return False
    return args;
    
    
    
    
    # parser = argparse.ArgumentParser(
    # description="Spider: download images from a website recursively"
    # )
    
    # parser.add_argument(
    # "-r",
    # action="store_true",
    # help="Download recursively",
    # )
    
    # parser.add_argument(
    # "-l",
    # type=parse_depth, # parse la valeur recue juste apres -l et la convertit en int, si la conversion echoue alors parse_depth retourne None
    # nargs='?',       # zéro ou une valeur après -l
    # const=5,         # valeur par défaut si -l est fourni sans valeur
    # default=5,
    # help="Maximum depth for recursion (default 5)",
    # dest="depth" # remplace aussi le L dans le help
    # )
    
    # parser.add_argument(
    # "-p",
    # type=str,
    # nargs='?',       # zéro ou une valeur après -p
    # const="./data/", # valeur par défaut si -p est fourni sans valeur
    # default="./data/", # indique la valeur par defaut
    # help="Path to save images (default ./data/)", # ce qui est ecrit dans le help
    # dest="path" #pour acceder a la donnée ca sera ce nom, si pas definit alors cest le nom de l'argument
    # )
    
    # parser.add_argument(
    # "url",
    # type=str,
    # help="URL to crawl",
    # metavar="URL"
    # )
    
    # # parser.print_help()
    
    # args = parser.parse_args() # parse_args() va parser les arguments et les stocker dans un objet args
    
    # if not args.r or not args.url:
    #     print("Please provide an URL and the -r flag", file=sys.stderr)
    #     return False

    
    # return args