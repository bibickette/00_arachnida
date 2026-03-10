#!/usr/bin/env python3
import sys
from src.arg_checker import arg_check

def main() -> int:
    try:
        args = arg_check()
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1

    print(f"\nlist of {args}\n")
    print("program exit successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main()) #  raise SystemExit(main()) ; cest un equivalent pour return un code retour dans python