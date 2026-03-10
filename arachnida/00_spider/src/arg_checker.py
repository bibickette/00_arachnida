#!/usr/bin/env python3
import sys
from dataclasses import dataclass # permet des creer des classes

@dataclass
class Args:
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
    if len(flag_value) == 1 :
        raise ValueError(f"Flag Error : {flag_value}\nMissing option")

    for char in flag_value[1:] :
        previous = char
        if char != "r" and char != "l" and char != "p" :
            raise ValueError(f"Error : wrong char : {char}")
        if (char != previous or iterator > 0) and char in char_used : # -rlr => char != previous  | -r -r => iterator > 0
            raise ValueError(f"Flag Error : {flag_value}\nFlag already used: {char}")

        char_used.add(char)
    return char_used, iterator

def options_parse(args : Args, char_used : set) -> (Args) :
    if "r" in char_used :
        args.r = True
    if "l" in char_used :
        args.l = True
    if "p" in char_used :
        args.p = True
    return args

def options_verify(args : Args, value : str) -> (Args) :
    if args.l == True and value[len(value) - 1] == "l":
        print("verify l argument")
        # verifier si largument dapres est un flag : ne rien faire, sinon : doit etre un int ou une str ( si -rl 4 url ; -rl url)
    if args.p == True and value[len(value) - 1] == "p":
        print("verify p argument")
        # verifier si largument dapres est un flag : ne rien faire, sinon : doit etre une str
        
    return args

def flag_letter_repetition_checker(args : Args, argv, char_used: set) -> (tuple[Args, set]) :
    iterator = 0
    for arg in argv[1:] :
        if arg.startswith("-") :
            char_used, iterator = is_valid_flag(arg, char_used, iterator)
        args = options_parse(args, char_used)
        args = options_verify(args, arg)
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


    # need to check : si ya un flag l alors ce qui doit arriver apres est un int ou le flag r ou p, sinon false
    # ne doit pas etre accepter : -lr 4 => refuser ; ok : -rl 4
    # pareil pour p : -pr /data/ => refuser ; ok : -rp /data/
    return args;
