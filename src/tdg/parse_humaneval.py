import random
import re
import textwrap
from functools import lru_cache
from typing import Optional

import datasets
from pydantic import BaseModel


class HEPItem(BaseModel):
    task_id: str
    prompt: str
    canonical_solution: str
    entry_point: str
    test: str


@lru_cache(None)
def parse_hep() -> list[HEPItem]:
    ds = datasets.load_dataset("evalplus/humanevalplus")
    # only has a test partition for some reason
    # TODO: find out why
    data = []
    for idx, item in enumerate(ds["test"]):
        data.append(HEPItem.model_validate(item))

    return data


def extract_prompt_name_and_doc(item: HEPItem) -> Optional[tuple[str, str]]:
    fn_name = item.entry_point
    doc_pat = re.compile(
        f"def\s+{fn_name}" + r".*['\"]{3}(.*?)['\"]{3}", re.DOTALL + re.MULTILINE
    )
    if doc_match := re.search(doc_pat, item.prompt):
        doc = doc_match.group(1)
        return fn_name, doc


input_pat = re.compile("inputs\s+=(.*?)\n")
results_pat = re.compile("results\s+=(.*?)\n")


def quote_string(s: str) -> str:
    return f'"{s}"'


def convert_tests(hep: HEPItem, max_tests: int = 10) -> Optional[tuple[str, list[str]]]:
    "for i, inp in enumerate(inputs):\n        assertion(candidate(*inp), ref_func(*inp), 0)"

    soln = hep.prompt + hep.canonical_solution
    # figure out if takes *args or explicit positionals
    # definition = find_definition(code=soln, name=hep.entry_point)
    # TODO: return node rather than str, look at node arg sig

    blocks = [soln]

    inp = None
    if input_match := input_pat.search(hep.test):
        inp = input_match.group(1)
    out = None
    if res_match := results_pat.search(hep.test):
        out = res_match.group(1)

    match inp, out:
        case str(), str():
            print("in and out")
            inp = eval(inp.strip())
            out = eval(out.strip())
            cases = random.sample(list(zip(inp, out)), k=min(max_tests, len(inp)))

            for case_num, case in enumerate(cases):
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

        # case None, str():
        #     print("out only")
        # case str(), None:
        #     print("in only")
        # case None, None:
        #     print("No in or out")
        case _:
            # raise NotImplementedError("Should be unreachable")
            return None

    return soln, blocks
