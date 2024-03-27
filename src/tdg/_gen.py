import ast
import importlib
import inspect
import sys
from pathlib import Path
from typing import Callable, Optional

import openai
from pydantic import BaseModel

from tdg.config import Settings

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


def do_generation_openai(
    fn_name: str,
    test: Callable,
) -> str:

    client = openai.Client(api_key=_conf.OPENAI_API_KEY.get_secret_value())
    system_prompt = _system_template.format(context=DEFAULT_CONTEXT)

    test_source = inspect.getsource(test)

    user_prompt = _user_template.format(
        test=test_source,
        fn_name=fn_name,
    )
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

    failures: list[tuple[str, AssertionError]] = []
    for choice in out.choices:
        code = clean_openai_code(choice.message.content)
        if is_valid_python(code) and f"def {fn_name}" in code:

            # remove old implementations of `fn_name`
            if fn_name in locals():
                del locals()[fn_name]
            # populate namespace with code
            exec(code)
            fn = locals()[fn_name]
            try:
                test(fn)
                return code
            except AssertionError as e:
                failures.append((code, e))
                continue


class GenHistory(BaseModel):
    code: str
    test: str
    prompt: str


class gen:
    def __init__(self, module: str, gen_root: Optional[Path] = None):

        self.gen_root = gen_root or Path.cwd().joinpath("src", "gen")
        if not self.gen_root.exists():
            self.gen_root.mkdir(exist_ok=True, parents=True)

        # add the generated code root to sys.path
        if str(self.gen_root) not in sys.path:
            sys.path.append(str(self.gen_root))

        self.module = module
        self.cwd = Path.cwd()
        self.module_path = self.gen_root.joinpath(*module.split(".")).with_suffix(".py")

        self._gen_history: list[GenHistory] = []

    def __call__(self, test: Callable):
        if not self.module_path.exists():
            self.module_path.parent.mkdir(exist_ok=True, parents=True)
            self.module_path.touch()

        try:
            code = importlib.import_module(self.module)
            print(code)
        except ImportError:

            sig = inspect.signature(test)
            to_generate = list(sig.parameters)[0]

            source = inspect.getsource(test)

            gen = do_generation_dspy(fn_name=to_generate, test=source)
            self._gen_history.append(gen)

            raise NotImplementedError("TODO!")
