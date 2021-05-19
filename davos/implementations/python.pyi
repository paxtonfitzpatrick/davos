from typing import Optional
from davos.implementations import ParserFunc, SmuggleFunc

# TODO: add __all__

def _activate_helper(smuggle_func: SmuggleFunc, parser_func: ParserFunc) -> None: ...
def _check_conda_avail_helper() -> Optional[str]: ...
def _deactivate_helper(smuggle_func: SmuggleFunc, parser_func: ParserFunc) -> None: ...
def _run_shell_command_helper(command: str) -> None: ...