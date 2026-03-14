#!/usr/bin/env python3
import sys

def main() -> int:
    RED = "\033[31m"
    RESET = "\033[0m"
    print(f"{RED}This is a placeholder for the scorpion script.{RESET}")

    return 0

if __name__ == "__main__":
    sys.exit(main()) #  raise SystemExit(main()) ; cest un equivalent pour return un code retour dans python