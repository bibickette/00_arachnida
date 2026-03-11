#!/usr/bin/env python3
import sys

# ce qui est accepté :
# repetition de la meme lettre uniquement cote a cote : -rrr
# repetition colle de plusieurs lettre differentes : -rrrlllppp
# si apparition dune lettre/repetition dune lettre, elle ne peut plus etre repetée : -r -r

# refusé
# pas de repetition de - : ---r
class Args:
    # depth: int | None = None
    # path: str | None = None
    # url: str | None = None
    def __init__(self) -> None:
        self.depth = None
        self.path = None
        self.url = None

    
def parse_depth(val):
    try:
        return int(val)
    except ValueError:
        return None

def options_verify(args : Args, value : str, char_used : set, possible_argument : str, iterator : int) -> (Args) :
    if value[len(value) - 1] == "r":
        return args, iterator
    
    if possible_argument is None:
        raise ValueError(f"Missing argument for flag {value}")
        
    if value[len(value) - 1] == "l":
        args.depth = parse_depth(possible_argument)
        iterator += 1

    elif value[len(value) - 1] == "p":
        args.path = possible_argument
        # print(f"verify p argument : {possible_argument}")
        iterator += 1
        
    return args, iterator

def is_valid_flag(flag_value : str, char_used : set) :
    previous = None
    if len(flag_value) == 1 :
        raise ValueError(f"Flag Error : {flag_value}\nMissing option")

    previous = flag_value[0]
    for char in flag_value[1:] :
        if char != "r" and char != "l" and char != "p" :
            raise ValueError(f"Error : wrong char : {char}")
        if (char != previous) and char in char_used : 
            raise ValueError(f"Flag Error : {flag_value}\nFlag already used: {char}")
        char_used.add(char)
        previous = char
        
    return char_used

def validate_flag_arguments(args : Args, argv, char_used: set) -> (tuple[Args, set]) :
    iterator = 1
    while iterator < len(argv) :
        arg = argv[iterator]
        if arg.startswith("-") :
            char_used = is_valid_flag(arg, char_used)
            if iterator + 1 < len(argv) :
                arg_to_send = argv[iterator + 1] 
            else :
                arg_to_send = None
            args, iterator = options_verify(args, arg, char_used, arg_to_send, iterator)
        else :
            args.url = arg
            if iterator + 1 != len(argv) :
                raise ValueError(f"Argument not expected : {arg}")
        iterator +=1
    
    return args, char_used

def arg_check(argv) -> (Args | bool) :
    MAX_DEPTH = 10
    argc = len(argv)
    
    if argc > 7:
        raise ValueError(f"Maximum of 6 arguments")
    elif argc < 3 :
        raise ValueError(f"Minimum of 3 arguments")
    
    # pour stocker les lettres deja utilisées
    char_used = set() 
    args = Args()
    args, char_used = validate_flag_arguments(args, sys.argv, char_used)
    
    if not "r" in char_used :
        raise ValueError(f"Flag -r is needed")
    elif "l" in char_used and (args.depth is None) :
        raise ValueError(f"Missing depth value for -l flag")
    elif "p" in char_used and (args.path is None) :
        raise ValueError(f"Missing path value for -p flag")
    elif args.url is None :
        raise ValueError(f"Missing URL")
    elif args.depth is not None and (args.depth < 0 or args.depth > MAX_DEPTH) :
        raise ValueError(f"Depth value must be between 0 and 10")

    if args.depth is None :
        args.depth = 5
    if args.path is None :
        args.path = "./data/"

    return args;

