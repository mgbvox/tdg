from pathlib import Path
from typing import Iterable, TypeVar

import datasets

from tdg import parse_humaneval


import itertools

from tdg.generator import Generator
from tdg.parse_humaneval import HEPItem

T = TypeVar("T")


def chunked_iterable(iterable: T, chunk_size) -> Iterable[T]:
    """Yield successive chunk_size chunks from iterable."""
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, chunk_size))
        if not chunk:
            break
        yield chunk


CHUNK = 50


def main():
    data = datasets.load_dataset("evalplus/humanevalplus")

    dataset = [HEPItem.model_validate(item) for item in data["test"]]
    print("data is ", len(dataset), "long; will take ", len(dataset) // CHUNK, "iters")

    hep_suites = (parse_humaneval.convert_tests(hep) for hep in dataset)
    without_failures = (h for h in hep_suites if h)
    batches = chunked_iterable(without_failures, chunk_size=CHUNK)

    for it, batch in enumerate(batches):
        # keep track of originals for evaluation
        originals = []
        # randomly select 10 tests for prompting
        inputs = []
        for item in batch:
            originals.append(item.copy())
            item, _ = item.split(10)
            inputs.append(item)

        # do the pipeline
        gen = Generator(inputs[0])
        # gen = Generator(*inputs)
        gen.generate()
        return

        gen.save(Path(__file__).parent / "results")


if __name__ == "__main__":
    main()
