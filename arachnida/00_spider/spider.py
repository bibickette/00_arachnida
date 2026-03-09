#!/usr/bin/env python3
import sys


def arg_check(argv) -> bool:
    argc = len(argv)
    if argc > 6 : # if ||
        print("Too many arguments", file=sys.stderr)
        return False
    elif argc < 2 :
        print("Not enough arguments", file=sys.stderr)
        return False
    
    print(f"list of {argv}")
    return True

def main(argv) -> int:
    if not arg_check(argv) : # if (!)
        return 1
    
    print("program exit successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv)) #  raise SystemExit(main()) ; cest un equivalent pour return un code retour dans python