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
RED = "\033[31m"
RESET = "\033[0m"

def flag_letter_checker(flag_value : str, compare : str, iterator : int, flag_setted : bool) -> (tuple[int | None, bool]) : 
    if iterator == None or iterator >= len(flag_value) : # marque la fin du parcours pouriterator >= len et verifie si on est pas a la fin du parcours pour la lettre suivante
        return None, flag_setted
    
    if flag_value[iterator] == compare :
            if  flag_setted == True :
                raise ValueError(f"{RED}Flag Error : {flag_value}\nFlag is already used : {flag_value[iterator]}{RESET}")
            flag_setted = True
            while(iterator < len(flag_value) and flag_value[iterator] == compare) : # sauter les repetitions
                iterator += 1
    
    return iterator, flag_setted

def is_valid_flag(flag_value : str, r_used, l_used, p_used) -> (tuple[bool, bool, bool]) :
    i = 1  # car le char 0 est un -
    value_len = len(flag_value)

    while(i < value_len) :
        previous_i = i
        if flag_value[i] != "r" and flag_value[i] != "l" and flag_value[i] != "p" :
            raise ValueError(f"{RED}Error : wrong char : {flag_value[i]}{RESET}")
        i, r_used = flag_letter_checker(flag_value, 'r',  i, r_used)
        i, l_used = flag_letter_checker(flag_value, 'l',  i, l_used)
        i, p_used = flag_letter_checker(flag_value, 'p',  i, p_used)
        if not i :
            break
        if(previous_i == i) : # si i n'a car la lettre qui suit est lappel precedent
            i += 1
    
    return r_used, l_used, p_used


def flag_checker(argv, i : int, r_used : bool, l_used : bool, p_used : bool) -> (tuple[bool, bool, bool]) :
    if i >= len(argv):
        return r_used, l_used, p_used
    arg = sys.argv[i]
    # detecteur de flag
    if arg.startswith("-") :
        if i + 1 == len(argv) : # si le flag est le dernier argument alors c'est une erreur
            raise ValueError(f"Usage: spider.py -r [-l DEPTH] [-p PATH] URL\n{RED}Missing URL{RESET}")
        r_used, l_used, p_used = is_valid_flag(arg, r_used, l_used, p_used)
    
    r_used, l_used, p_used = flag_checker(argv, i+1, r_used, l_used, p_used)
    return r_used, l_used, p_used

def arg_check() -> (Args | bool) :
    argc = len(sys.argv)
    
    if argc > 7:
        raise ValueError(f"Usage: spider.py -r [-l DEPTH] [-p PATH] URL\n{RED}Maximum of 6 arguments{RESET}")

    if argc < 3 :
        raise ValueError(f"Usage: spider.py -r [-l DEPTH] [-p PATH] URL\n{RED}Minimum of 3 arguments{RESET}")

    args = Args()
    i = 1
    # check que les flags avec -
    args.r, args.l, args.p = flag_checker(sys.argv, i, args.r, args.l, args.p);

    if not args.r :
        raise ValueError(f"Usage: spider.py -r [-l DEPTH] [-p PATH] URL\n{RED}Flag -r is needed{RESET}")

    # need to check : si ya un flag l alors ce qui doit arriver apres est un int ou le flag r ou p, sinon false
    # ne doit pas etre accepter : -lr 4 => refuser ; ok : -rl 4
    # pareil pour p : -pr /data/ => refuser ; ok : -rp /data/
    return args;
