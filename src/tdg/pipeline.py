import uuid
from pathlib import Path
from typing import Callable, Any, Optional, Type

import aiofiles

from tdg import parsing
from tdg.agents import NavAgent, TestAgent, DevAgent
from tdg.agents.base import CodeContext, Agent
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

        self.best_solution_failures: int = 9999999
        self.best_solution: str = ""

    def __repr__(self):
        return f"Pipeline({self._id})"

    async def create_agent(self, cls: Type[Agent], **kwargs) -> Agent:
        agent = cls(**kwargs)
        agent.pipeline_id = self._id
        await agent.load_state()
        return agent

    async def gen(self, no_test: bool = False) -> tuple[str, Optional[str]]:
        print(f"Starting pipeline for context {self.code_context.signatures}")
        self.nav = await self.create_agent(NavAgent, code_context=self.code_context)
        nav_response = await self.nav.generate(self.nav.user_prompt())

        self.test = await self.create_agent(
            TestAgent, nav_response=nav_response, code_context=self.code_context
        )
        test_response = await self.test.generate(self.test.user_prompt())

        self.dev = await self.create_agent(
            DevAgent, test_response=test_response, code_context=self.code_context
        )
        dev_response = await self.dev.generate(self.dev.user_prompt())

        if no_test:
            return self._id, None

        return self._id, await self.test_until_passing(
            solution=dev_response.content,
            depth=0,
        )

    async def test_until_passing(self, *, solution: str, depth: int) -> Optional[str]:
        print(f"TEST ITER: {depth + 1}")
        if depth > self.max_iter:
            # give up, and return the best solution that we have.
            return self.best_solution
        try:
            tests = self.test.tests + self.code_context.test_sources
            imports = self.test.imports

            script = parsing.compile_tests(
                tests=tests,
                imports=imports,
                implementations=[solution],
            )

            uuid_small = str(uuid.uuid4()).replace("-", "")[:8]

            script_log_file = self._log_path / f"script_iter_{depth}_{uuid_small}.py"
            async with aiofiles.open(script_log_file, "w") as f:
                await f.write(script)

            tester = TestExecutor(script=script, path=script_log_file)
            await tester.test()
            if (n_fail := tester.n_failures()) < self.best_solution_failures:
                self.best_solution = solution
                self.best_solution_failures = n_fail
                print(
                    f"{self}: Best Solution has {self.best_solution_failures} failures"
                )

            if n_fail == 0:
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

                refined = await self.dev.generate(fail_message)
                return await self.test_until_passing(
                    solution=refined.content, depth=depth + 1
                )
        except BaseException:
            # something is broken, don't ruin the other pipelines
            return self.best_solution
