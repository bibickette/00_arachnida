#!/usr/bin/env python3

# import argparse

import sys
from dataclasses import dataclass # permet des creer des classes

@dataclass
class Args:
    l: bool = False
    depth: int | None = None
    p: bool = False
    path: str | None = None
    url: str | None = None

    
def parse_depth(val):
    try:
        return int(val)
    except ValueError:
        return None

# ce qui est accepté :
# repetition de la meme lettre uniquement cote a cote : -rrr
# repetition colle de plusieurs lettre differentes : -rrrlllppp
# si apparition dune lettre/repetition dune lettre, elle ne peut plus etre repetée : -r -r

# refusé
# pas de repetition de - : ---r

def is_valid_flag(flag_value : str, char_used : set, iterator : int) :
    previous = None
    if len(flag_value) == 1 :
        raise ValueError(f"Flag Error : {flag_value}\nMissing option")

    previous = flag_value[0]
    for char in flag_value[1:] :
        # print(f"looking at : {char}")
        # print(f"previous at : {previous}")
        if char != "r" and char != "l" and char != "p" :
            raise ValueError(f"Error : wrong char : {char}")
        # -rlr => char != previous 
        if (char != previous) and char in char_used : 
            raise ValueError(f"Flag Error : {flag_value}\nFlag already used: {char}")
        char_used.add(char)
        previous = char
        
    # print(f"char_used {char_used}")
    return char_used, iterator



def options_verify(args : Args, value : str, char_used : set) -> (Args) :
    if(value.startswith("-")) :
        if "l" in char_used :
            args.l = True
            if value[len(value) - 1] == "l":
                print("verify l argument")
            # verifier si largument dapres est un flag : ne rien faire, sinon : doit etre un int ou une str ( si -rl 4 url ; -rl url)
        if "p" in char_used :
            args.p = True
            if value[len(value) - 1] == "p":
                print("verify p argument")
            # verifier si largument dapres est un flag : ne rien faire, sinon : doit etre une str
        
    return args

def flag_letter_repetition_checker(args : Args, argv, char_used: set) -> (tuple[Args, set]) :
    iterator = 0
    for arg in argv[1:] :
        if arg.startswith("-") :
            char_used, iterator = is_valid_flag(arg, char_used, iterator)
        args = options_verify(args, arg, char_used)
        iterator +=1
    return args, char_used

def arg_check(argv) -> (Args | bool) :
    argc = len(argv)
    
    if argc > 7:
        raise ValueError(f"Maximum of 6 arguments")
    elif argc < 3 :
        raise ValueError(f"Minimum of 3 arguments")

    # si le dernier est un flag alors cest faux
    if argv[len(argv) - 1 ].startswith("-"): 
        raise ValueError(f"Missing URL")
    
    # pour stocker les lettres deja utilisées
    char_used = set() 
    args = Args()
    args, char_used = flag_letter_repetition_checker(args, sys.argv, char_used)
    
    if not "r" in char_used :
        raise ValueError(f"Flag -r is needed")

    # need to check : si ya un flag l alors ce qui doit arriver apres est un int ou le flag r ou p, sinon false
    # ne doit pas etre accepter : -lr 4 => refuser ; ok : -rl 4
    # pareil pour p : -pr /data/ => refuser ; ok : -rp /data/
    if args.l and (args.depth is None) :
        raise ValueError(f"Missing depth value for -l flag")
    if args.p and (args.path is None) :
        raise ValueError(f"Missing path value for -p flag")
   

    return args;



# pourquoi ca fait pas comme je veux : 
# exemple :  ./arachnida/00_spider/spider.py  -rrrrllllll 4 url
# usage: spider.py [-h] [-r] [-l [DEPTH]] [-p [PATH]] URL
# spider.py: error: unrecognized arguments: url

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
    # print(args)
    # if not args.r or not args.url:
    #     print("Please provide an URL and the -r flag", file=sys.stderr)
    #     return False