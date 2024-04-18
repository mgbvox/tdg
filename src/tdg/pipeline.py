import uuid
from pathlib import Path
from typing import Callable, Any, Optional

import aiofiles

from tdg import parsing
from tdg.agents import NavAgent, TestAgent, DevAgent
from tdg.agents.base import CodeContext
from tdg.parsing import nl_join
from tdg.executors.test import TestExecutor


class GenerationError(BaseException):
    pass


# TODO: adapt for multiple tests (*tests)
class Pipeline:
    def __init__(
        self, test_fn: Callable[[Any], Any], from_id: str = "", max_iter: int = 5
    ):
        self.code_context = CodeContext(test_fn)
        self._id = from_id if from_id else str(uuid.uuid4())
        self._log_path = Path.home() / ".tdg" / self._id
        self._log_path.mkdir(exist_ok=True, parents=True)

        self.max_iter = max_iter

        self.nav: Optional[NavAgent] = None
        self.test: Optional[TestAgent] = None
        self.dev: Optional[DevAgent] = None

    async def gen(self) -> Optional[str]:
        self.nav = NavAgent(self.code_context)
        nav_response = await self.nav.initial_generation()
        self.test = TestAgent(nav_response=nav_response, code_context=self.code_context)
        test_response = await self.test.initial_generation()
        self.dev = DevAgent(test_response=test_response, code_context=self.code_context)
        dev_response = await self.dev.initial_generation()

        return await self.test_until_passing(
            solution=dev_response.content,
            depth=0,
        )

    async def test_until_passing(self, *, solution: str, depth: int) -> Optional[str]:
        if depth > self.max_iter:
            raise GenerationError(
                f"Max iterations reached without a passing test suite: {self.max_iter}"
            )

        tests = self.test.tests + [self.code_context.test_source]
        imports = self.test.imports

        script = parsing.compile_tests(
            tests=tests,
            imports=imports,
            implementations=[solution],
        )

        script_log_file = self._log_path / f"script_iter_{depth}.py"
        async with aiofiles.open(script_log_file, "w") as f:
            await f.write(script)

        tester = TestExecutor(script=script, path=script_log_file)
        if tester.test().passed():
            return solution
        else:
            # tests failed
            sep = "-----"
            fail_message = nl_join(
                "Your implementation failed the test suite with the following errors:",
                *[nl_join(fail.longrepr, sep) for fail in tester.tracker.failures],
                sep,
                "Please fix your implementation.",
            )

            refined = await self.dev.continue_generation(fail_message)
            return await self.test_until_passing(
                solution=refined.content, depth=depth + 1
            )
