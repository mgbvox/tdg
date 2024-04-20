"""
A synchronous generator that wraps many asynchronous pipelines.
"""

import asyncio
import uuid
from pathlib import Path
from typing import Callable, Union

from tdg.parse_humaneval import HEPSuite
from tdg.pipeline import Pipeline


class Generator:
    def __init__(self, *tests: Union[Callable, HEPSuite], from_id: str = ""):
        self.tests = tests
        self._id: str = str(uuid.uuid4())

        self.pipelines: list[Pipeline] = []

        for test in tests:
            match test:
                case HEPSuite():
                    pipe_id = test.fn_name
                case _:
                    pipe_id = str(test)

            pipe = Pipeline(test, from_id=pipe_id)
            self.pipelines.append(pipe)

        self.results: list[tuple[str, str]] = []

    async def _generate_all_pipelines(self):
        self.results.extend(
            await asyncio.gather(
                *[pipe.gen() for pipe in self.pipelines], return_exceptions=True
            )
        )

    def generate(self):
        asyncio.run(self._generate_all_pipelines())

    def save(self, path: Path):
        path.mkdir(exist_ok=True, parents=True)
        for id_, result in self.results:
            result_path = path / f"{id_}.py"
            result_path.write_text(str(result))
