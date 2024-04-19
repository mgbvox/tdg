from openai.types.chat import ChatCompletion

from tdg import parsing
from tdg.agents import Agent, NavAgent, templates
from tdg.agents.base import CodeAgent, CodeContext, Message
from tdg.extract import TestFinder
from tdg.parsing import nl_join


class TestAgent(CodeAgent):
    def __init__(self, nav_response: Message, code_context: CodeContext):
        self.code_context = code_context
        self.nav_response = nav_response

        self.tests: list[str] = []

        super().__init__()

    def system_prompt(self) -> str:
        prompt = templates.SystemTemplate(
            role="Test Designer",
            description=nl_join(
                "Test Designers focus on writing comprehensive pytest tests to satisfy the constraints",
                "of the prompt presented by the user, and the analysis provided by the Navigator role.",
                "You should be sure to include edge cases and potential gotchas in your tests.",
                "You should follow the principles of Test-Driven Design, wherein tests are written first",
                "to define the desired scope and behavior of production code.",
            ),
            extra_context=[
                templates.PERFORMANCE_CRITICAL,
                templates.AVOID_PITFALLS,
                nl_join(
                    "The reasoning provided by the Navigator role is the following - please take this into account",
                    "when generating your response.",
                    "Navigator Reasoning:",
                    self.nav_response.content,
                ),
                templates.CODE_GENERATOR,
            ],
        ).render()

        return prompt

    def user_prompt(self) -> str:
        return templates.GenerationPrompt(
            targets=self.code_context.signatures,
            additional_objects=self.code_context.undefined,
            tests=self.code_context.test_sources,
            command=nl_join(
                "Please write a pytest-compatible test suite that compliments the test(s) provided by the user.",
                "Please note that you should *not* actually implement the system under test - that will be handled",
                "by the Developer role agent.",
                "Just write the tests for the system.",
            ),
        ).render()

    async def ensure_valid_code(self, choice: Message) -> Message:
        initial = await super().ensure_valid_code(choice)
        # we do not allow fixtures for generated tests!
        finder = TestFinder().visit_code(initial.content)
        self.tests = list(finder.tests.values())
        if not finder.test_args:
            return initial
        else:
            # remove the affected tests if they're ony a subset
            if len(finder.test_args) < len(finder.tests):
                tests = finder.tests.copy()
                for name in finder.test_args:
                    tests.pop(name)
                self.tests = list(tests.values())
                new_code = parsing.compile_tests(tests=tests, imports=self.imports)
                initial.content = new_code
                return initial
            # otherwise the whole suite is affected; regenerate
            else:
                return await self.generate(
                    nl_join(
                        "Your generated pytest suite contained fixtures, which we do not allow!",
                        "Please regenerate your tests so they are fixture-free.",
                    )
                )
