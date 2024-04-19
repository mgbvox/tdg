"""
A synchronous generator that wraps many asynchronous pipelines.
"""

import asyncio

from tdg.pipeline import Pipeline


class Generator:
    def __init__(self, *tests, from_id: str = ""):
        self.tests = tests
        self.pipelines = [Pipeline(test, from_id=from_id) for test in tests]
        self.results = []

    async def _generate_all_pipelines(self):
        self.results.extend(
            await asyncio.gather(*[pipe.gen() for pipe in self.pipelines])
        )

    def generate(self):
        asyncio.run(self._generate_all_pipelines())
