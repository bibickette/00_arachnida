#!/usr/bin/env python3
import sys

class ArgumentParser:
    MAX_DEPTH = 10
    DEFAULT_DEPTH = 5
    DEFAULT_PATH = "./data/"
    RED = "\033[31m"
    RESET = "\033[0m"
    
    def __init__(self) -> None:
        self.recursive = False
        self.depth = None
        self.path = None
        self.url = None


    def print_args(self) -> None:
        print("\n==========\nArguments :\n")
        print(f"depth : {self.depth}\npath : {self.path}\nurl : {self.url}\n==========")


    def parse_depth(self, val: str) -> None:
        try:
            self.depth = int(val)
        except ValueError:
            self.depth = None


    def options_verify(self, char_used : set, value: str, possible_argument: str, iterator: int) -> int:
        if value[len(value) - 1] == "r":
            return iterator

        if possible_argument is None or possible_argument.startswith("-"):
            raise ValueError(f"Missing argument for flag {value}")

        if value[len(value) - 1] == "l":
            if not "r" in char_used:
                raise ValueError(f"Flag -l cannot be used without -r") 
            self.parse_depth(possible_argument)
            iterator += 1

        elif value[len(value) - 1] == "p":
            self.path = possible_argument
            # print(f"verify p argument : {possible_argument}")
            iterator += 1

        return iterator


    def parser_result_verify(self, char_used: set) -> None:
        if "l" in char_used and (self.depth is None):
            raise ValueError(f"Missing depth value for -l flag")
        elif "p" in char_used and (self.path is None):
            raise ValueError(f"Missing path value for -p flag")
        elif self.url is None:
            raise ValueError(f"Missing URL")
        elif self.depth is not None and (self.depth < 0 or self.depth > self.MAX_DEPTH):
            raise ValueError(f"Depth value must be between 0 and {self.MAX_DEPTH}")

        if "r" in char_used:
            self.recursive = True
        if self.depth is None:
            self.depth = self.DEFAULT_DEPTH
        if self.path is None:
            self.path = self.DEFAULT_PATH


    def is_valid_flag(self, flag_value: str, char_used: set) -> set:
        previous = None
        if len(flag_value) == 1:
            raise ValueError(f"Flag Error : {flag_value}\nMissing option")

        previous = flag_value[0]
        for char in flag_value[1:]:
            if char != "r" and char != "l" and char != "p":
                raise ValueError(f"Wrong char : {char}")
            if (char != previous) and char in char_used:
                raise ValueError(
                    f"Flag Error : {flag_value}\nFlag already used: {char}"
                )
            char_used.add(char)
            previous = char

        return char_used


    def validate_flag_arguments(self, argv: list[str]) -> None:
        char_used = set()

        iterator = 0
        while iterator < len(argv):
            arg = argv[iterator]
            if arg.startswith("-"):
                char_used = self.is_valid_flag(arg, char_used)
                if iterator + 1 < len(argv):
                    arg_to_send = argv[iterator + 1]
                else :
                    arg_to_send = None  
                iterator = self.options_verify(char_used,arg, arg_to_send, iterator)
            else:
                self.url = arg
                if iterator + 1 != len(argv):
                    raise ValueError(f"Argument not expected : {arg}")
            iterator += 1

        self.parser_result_verify(char_used)


    def arg_check(self, argv: list[str]) -> "ArgumentParser | None":
        argc = len(argv)
        try:
            if argc > 7:
                raise ValueError(f"Maximum of 6 arguments")
            elif argc < 2:
                raise ValueError(f"Minimum of 2 arguments")
            
            self.validate_flag_arguments(argv[1:])
        except ValueError as e:
            print(f"Usage: spider.py [-r] [-l DEPTH] [-p PATH] URL\n\n{self.RED}Error : {e}{self.RESET}", file=sys.stderr)
            self = None
        
        return self