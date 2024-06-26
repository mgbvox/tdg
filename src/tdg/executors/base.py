import ast
import copy

from tdg.parsing import is_valid_python


class Executor:
    def __init__(self, **env):
        # decouple passed in env from external world
        self.env = copy.deepcopy(env)

    def run(self, code: str):
        match is_valid_python(code):
            case True, ast.AST():  # as node (can capture):
                exec(code, self.env)
            case False, SyntaxError() as e:
                raise e
            case _:
                raise NotImplementedError()

    def __getattr__(self, item: str):
        return self.env.get(item)
