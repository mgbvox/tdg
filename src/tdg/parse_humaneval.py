import random
import re
import textwrap
from functools import lru_cache
from typing import Optional, Union, Self

import datasets
from pydantic import BaseModel

from tdg import parsing


class HEPItem(BaseModel):
    task_id: str
    prompt: str
    canonical_solution: str
    entry_point: str
    test: str


class HEPSuite(BaseModel):
    """A HumanEval Benchmark Pytest Suite with Context"""

    fn_name: str
    tests: list[str]
    imports: list[str]
    prompt: str
    solution: str

    def split(self, n: Optional[Union[int, float]] = 10) -> tuple[Self, Self]:
        total_tests = len(self.tests)
        match n:
            case int():
                # use the lower number
                k = min(n, total_tests)
            case float():
                # max_test is a fraction
                k = int(min(total_tests * n, total_tests))
            case _:
                # ignore any modifiers
                k = total_tests

        random.shuffle(self.tests)
        train, test = self.tests[:k], self.tests[k:]
        return self.model_copy(update={"tests": train}), self.model_copy(
            update={"tests": test}
        )

    def compile(self, w_solution: bool = True) -> str:
        """Compile a human eval problem into a runnable test suite."""
        return parsing.compile_tests(
            tests=self.tests,
            implementations=[self.solution] if w_solution else [],
            imports=self.imports,
        )


@lru_cache(None)
def parse_hep() -> list[HEPItem]:
    ds = datasets.load_dataset("evalplus/humanevalplus")
    # only has a test partition for some reason
    # TODO: find out why
    data = []
    for idx, item in enumerate(ds["test"]):
        data.append(HEPItem.model_validate(item))

    return data


input_pat = re.compile("inputs\s+=(.*?)\n")
results_pat = re.compile("results\s+=(.*?)\n")


def quote_string(s: str) -> str:
    return f'"{s}"'


def convert_tests(
    hep: HEPItem,
) -> Optional[HEPSuite]:
    "for i, inp in enumerate(inputs):\n        assertion(candidate(*inp), ref_func(*inp), 0)"

    blocks = []
    solution = hep.prompt + hep.canonical_solution
    imports = parsing.extract_imports(
        parsing.nl_join(
            solution,
            hep.test,
        ),
    )

    inp = None
    if input_match := input_pat.search(hep.test):
        inp = input_match.group(1)
    out = None
    if res_match := results_pat.search(hep.test):
        out = res_match.group(1)

    match inp, out:
        case str(), str():
            inp = eval(inp.strip())
            out = eval(out.strip())

            for case_num, case in enumerate(zip(inp, out)):
                case_inp, case_out = case
                if isinstance(case_inp, str):
                    case_inp = quote_string(case_inp)

                if isinstance(case_out, str):
                    case_out = quote_string(case_out)

                test_block = textwrap.dedent(
                    f"""
                    def test_{hep.entry_point}_case_{case_num}():
                        assert {hep.entry_point}(*{case_inp}) == {case_out}
                    """
                )
                blocks.append(test_block)

        case _:
            return None

    return HEPSuite(
        fn_name=hep.entry_point,
        tests=blocks,
        imports=imports,
        prompt=hep.prompt,
        solution=solution,
    )
