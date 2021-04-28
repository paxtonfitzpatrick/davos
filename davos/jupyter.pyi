from typing import Literal, NoReturn

__all__: list[
    Literal[
        'activate_parser_jupyter',
        'check_parser_active_jupyter',
        'deactivate_parser_jupyter',
        'run_shell_command_jupyter',
        'smuggle_jupyter',
        'smuggle_parser_jupyter'
    ]
]

def activate_parser_jupyter() -> NoReturn: ...
def check_parser_active_jupyter() -> NoReturn: ...
def deactivate_parser_jupyter() -> NoReturn: ...
def run_shell_command_jupyter(command: str) -> NoReturn: ...
def smuggle_jupyter() -> NoReturn: ...
def smuggle_parser_jupyter(line: str) -> NoReturn: ...
