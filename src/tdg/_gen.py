import ast
import inspect
import os
import uuid
from enum import Enum, auto
from pathlib import Path
from typing import Callable, Optional

import openai
import pytest
from _pytest.config import ExitCode
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice
from pydantic import BaseModel

from tdg import context_managers as cm
import tdg.extractors
from tdg.config import Settings

from cs224u_utils.cache import disk_cache

_conf = Settings.from_dotenv()
DEFAULT_CONTEXT = "No Codebase Yet - generate from scratch."
_system_template = """
You are a Python code completion LLM. Your task is to generate functions that pass specified tests.
Your code should be fully statically typed, conform to the syle of the parent codebase (if known), and have 100% coverage.
Add docstrings always (Google docstring syntax) and inline comments where helpful.

Restrictions:
* You should ONLY output valid python code - your response will be parsed and used directly in a python codebase.
* You should not wrap your code in markdown or other metaformatting; please output pure python code. 
    Invalid output:
    ```python
    def my_function():
        ...
    ```
    
    Valid output:
    def my_function():
        ...

Here is the code base as it stands:
{context}
"""


_user_template = """
Please implement a function that passes the following test(s).
Your implementation should be called {fn_name}, e.g. `def {fn_name}(...):`
If a function in the codebase exists that would be useful here, feel free to use it.
Be as efficient as possible, and do not repeat yourself.

{test}
"""


def is_valid_python(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def clean_openai_code(code: str) -> str:
    code = code.strip().splitlines()
    if "```py" in code[0]:
        code = code[1:]
    if "```" in code[-1]:
        code = code[:-1]
    return "\n".join(code)


def eval_init():
    os.environ["PROC_ID"] = str(uuid.uuid4())


@disk_cache
def _mk_completion(system_prompt: str, user_prompt: str) -> list[Choice]:
    client = openai.Client(api_key=_conf.OPENAI_API_KEY.get_secret_value())
    out = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        model=_conf.LLM_MODEL,
    )
    return out.choices


def do_generation_openai(
    fn_name: str,
    test: Callable,
) -> str:

    system_prompt = _system_template.format(context=DEFAULT_CONTEXT)

    test_source = tdg.extractors.strip_decorator(test)

    user_prompt = _user_template.format(
        test=test_source,
        fn_name=fn_name,
    )

    choices = _mk_completion(system_prompt=system_prompt, user_prompt=user_prompt)

    failures: list[tuple[str, AssertionError]] = []

    for choice in choices:
        code = clean_openai_code(choice.message.content)
        if is_valid_python(code) and f"def {fn_name}" in code:
            # in a temporary directory, run a sub-pytest session on the generated code
            with cm.TempDir() as tmpdir:
                tmp_test_file = tmpdir.root / f"test_{fn_name}.py"
                tmp_test_file.write_text(code + "\n\n" + test_source)
                out = pytest.main([str(tmp_test_file)])
                if out is ExitCode.OK:
                    return code
                else:
                    failures.append(())


class GenHistory(BaseModel):
    code: str
    test: str
    prompt: str


class Mode(Enum):
    GEN = auto()
    EVAL = auto()


class gen:
    def __init__(self, fn_name: Optional[str] = None):
        self.fn_name = fn_name
        self._gen_history: list[GenHistory] = []

    def __call__(self, test: Callable):
        if os.getenv("TDG_MODE") == Mode.EVAL:
            return test
        else:
            gen = do_generation_openai(fn_name=self.fn_name, test=test)
            to_modify = Path(inspect.getfile(test))
            src_lines = to_modify.read_text().splitlines()
            fn_start_line = inspect.getsourcelines(test)[1]

            # account for @tdg.gen decorator
            fn_start_line -= 1

            preceding = "\n".join(src_lines[:fn_start_line])
            injection = "\n" + gen + "\n"
            succeding = "\n".join(src_lines[fn_start_line:])

            new_content = preceding + injection + succeding

            to_modify.write_text(new_content)

