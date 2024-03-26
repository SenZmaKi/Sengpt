import sys

from .utils import APP_NAME_LOWER, DESCRIPTION, VERSION


class ArgParser:
    def __init__(self, args: list[str]) -> None:
        self.args, self.non_args = ArgParser.parse_args(args)

    @staticmethod
    def parse_args(args: list[str]) -> tuple[list[str], list[str]]:
        non_args: list[str] = []
        extracted_args: list[str] = []
        for a in args:
            if a.startswith("-"):
                extracted_args.append(a)
                continue
            non_args.append(a)
        return extracted_args, non_args

    @staticmethod
    def version_info() -> str:
        return f"{APP_NAME_LOWER} {VERSION}"

    @staticmethod
    def help_info() -> str:
        return f"""
{DESCRIPTION}

Usage: sengpt [prompt] [options]

-h, --help                    Show help message and exit                                                
-v, --version                 Show the version information                                              
-cf, --config_file            Show the config file's contents and location                              
-st, --session_token          Set session token                                                         
                                                                                                        
-ng, --no_glow                Disable pretty printing with Glow,                                        
                              this can be set to be the default behaviour in the config file                
                                                                                                        
-c,  --copy                   Copy the prompt response to the clipboard,                                
                              this can be set to be the default behaviour in the config file                
                                                                                                        
-p,  --paste                  Append the most recently copied clipboard text to the sent prompt         
-rc, --recent_conversation    Use the most recently saved conversation as context                       
-pp, --preconfigured_prompt   Append a preconfigured prompt to the sent prompt,                         
                              replace "preconfigured_prompt" with the prompt's name                     
                              as it appears in the config file                                          
                                                                                                        
-q, query                     Use query mode i.e., print ChatGPT's response and exit,                   
                              this flag is only necessary if "default_mode" in config file is interactive 
                                                                                                        
-s, --save                    By default conversations in query mode are deleted on exit,               
                              this saves the conversation instead,                                      
                              this can be set to be the default behaviour in the config file                
                                                                                                        
-i, --interactive             Use interactive mode i.e., back and forth interaction with ChatGPT,       
                              this flag is only necessary if "default_mode" in the config file is query   
                                                                                                        
-d, --delete                  By default conversations in interactive mode are saved on exit,           
                              this deletes then exits the interactive mode session,                     
                              this can be set to be the default behaviour in the config file                
"""

    @staticmethod
    def short_and_long(name: str) -> tuple[str, str]:
        long = f"--{name}"
        chars: list[str] = []
        for prev_char, char in zip(name, name[1:]):
            if prev_char == "_":
                chars.append(char)
        short = f'-{name[0]}{"".join(chars)}'
        return short, long

    @staticmethod
    def abstract_is_set(flag_name: str, args: list[str]) -> bool:
        short, long = ArgParser.short_and_long(flag_name)
        return short in args or long in args

    def is_set(self, flag_name: str) -> bool:
        return ArgParser.abstract_is_set(flag_name, self.args)


SYS_ARGS = ArgParser(sys.argv[1:])

