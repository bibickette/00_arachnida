#!/usr/bin/env python3
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

    
# def parse_depth(val):
#     try:
#         return int(val)
#     except ValueError:
#         return None

# ce qui est accepté :
# repetition de la meme lettre uniquement cote a cote : -rrr
# repetition colle de plusieurs lettre differentes : -rrrlllppp
# si apparition dune lettre/repetition dune lettre, elle ne peut plus etre repetée : -r -r

# refusé
# pas de repetition de - : ---r

def is_valid_flag(flag_value : str, char_used : set, iterator : int) :
    previous = None
    for char in flag_value[1:] :
        previous = char
        if char != "r" and char != "l" and char != "p" :
            raise ValueError(f"Error : wrong char : {char}")
        if (char != previous or iterator > 0) and char in char_used : # -rlr => char != previous  | -r -r => iterator > 0
            raise ValueError(f"Flag Error : {flag_value}\nFlag already used: {char}")

        char_used.add(char)
    return char_used, iterator

def flag_checker(argv, char_used: set) :
    iterator = 0
    for arg in argv[1:] :
        if arg.startswith("-") :
            char_used, iterator = is_valid_flag(arg, char_used, iterator)
        iterator +=1
    return char_used

def arg_check() -> (Args | bool) :
    argc = len(sys.argv)
    
    if argc > 7:
        raise ValueError(f"Maximum of 6 arguments")

    if argc < 3 :
        raise ValueError(f"Minimum of 3 arguments")

    args = Args()
    char_used = set() # pour stocker les lettres deja utilisées
    char_used = flag_checker(sys.argv, char_used)
    
    if "r" in char_used :
        args.r = True
    if "l" in char_used :
        args.l = True
    if "p" in char_used :
        args.p = True

    if not args.r :
        raise ValueError(f"Flag -r is needed")

    # need to check : si ya un flag l alors ce qui doit arriver apres est un int ou le flag r ou p, sinon false
    # ne doit pas etre accepter : -lr 4 => refuser ; ok : -rl 4
    # pareil pour p : -pr /data/ => refuser ; ok : -rp /data/
    return args;
