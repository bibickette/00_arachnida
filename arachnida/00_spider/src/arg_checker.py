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

def flag_letter_checker(flag_value : str, compare : str, iterator : int, flag_setted : bool) : 
    if iterator == None or iterator >= len(flag_value) : # marque la fin du parcours pouriterator >= len et verifie si on est pas a la fin du parcours pour la lettre suivante
        return None, flag_setted
    if iterator == False : # si une erreur a été detecté dans une itération précédente
        return False, flag_setted
    if flag_value[iterator] == compare :
            if  flag_setted == True :
                print(f"{RED}Flag Error : {flag_value}{RESET}", file=sys.stderr)
                print(f"{RED}Flag is already used : {flag_value[iterator]}{RESET}", file=sys.stderr)
                return False, flag_setted
            flag_setted = True
            while(iterator < len(flag_value) and flag_value[iterator] == compare) : # sauter les repetitions
                iterator += 1
    elif flag_value[iterator] != "r" and flag_value[iterator] != "l" and flag_value[iterator] != "p" :
        print(f"{RED}Error : wrong char : {flag_value[iterator]}{RESET}", file=sys.stderr)
        return False, flag_setted
    return iterator, flag_setted

def is_valid_flag(flag_value : str, r_used, l_used, p_used) :
    i = 1  # car le char 0 est un -
    value_len = len(flag_value)

    while(i < value_len) :
        previous_i = i
        i, r_used = flag_letter_checker(flag_value, 'r',  i, r_used)
        i, l_used = flag_letter_checker(flag_value, 'l',  i, l_used)
        i, p_used = flag_letter_checker(flag_value, 'p',  i, p_used)
        if not i or i == False :
            break
        if(previous_i == i) : # si i n'a car la lettre qui suit est lappel precedent
            i += 1
    
    if i == False : # si ya eu un probleme alors je quitte
        return False, False, False, False
    
    return True, r_used, l_used, p_used


def flag_checker(argv, i : int, r_used : bool, l_used : bool, p_used : bool) :
    if i >= len(argv):
        return True, r_used, l_used, p_used
    arg = sys.argv[i]
    # detecteur de flag
    if arg.startswith("-") and i + 1 == len(argv) : # si le flag est le dernier argument alors c'est une erreur
        print(f"Usage: spider.py -r [-l DEPTH] [-p PATH] URL\n", file=sys.stderr)
        print(f"{RED}Missing URL{RESET}", file=sys.stderr)
        return False, False, False, False
    elif arg.startswith("-") :
            ret, r_used, l_used, p_used = is_valid_flag(arg, r_used, l_used, p_used)
            if not ret :
                return False, False, False, False
    ret, r_used, l_used, p_used = flag_checker(argv, i+1, r_used, l_used, p_used)
    return ret, r_used, l_used, p_used

def arg_check():
    argc = len(sys.argv)
    
    if argc > 7:
        print("Usage: spider.py -r [-l DEPTH] [-p PATH] URL\n", file=sys.stderr)
        print(f"{RED}Maximum of 6 arguments{RESET}", file=sys.stderr)
        return False

    if argc < 3 :
        print("Usage: spider.py -r [-l DEPTH] [-p PATH] URL\n", file=sys.stderr)
        print(f"{RED}Minimum of 3 arguments{RESET}", file=sys.stderr)
        return False
    args = Args()
    i = 1
    # check que les flags avec -
    ret, args.r, args.l, args.p = flag_checker(sys.argv, i, args.r, args.l, args.p);
    if ret == False :
        print("End false of program")
        print(f"r {args.r} l {args.l} p {args.p}")
        return False

    if not args.r :
        print("Usage: spider.py -r [-l DEPTH] [-p PATH] URL\n", file=sys.stderr)
        print(f"{RED}Flag -r is needed{RESET}", file=sys.stderr)
        return False
    
    # need to check : si ya un flag l alors ce qui doit arriver apres est un int ou le flag r ou p, sinon false
    # ne doit pas etre accepter : -lr 4 => refuser ; ok : -rl 4
    return args;
