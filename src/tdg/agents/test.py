from openai.types.chat import ChatCompletion

from tdg import parsing
from tdg.agents import Agent, NavAgent, templates
from tdg.agents.base import CodeAgent, CodeContext, Message
from tdg.parsing import nl_join


class TestAgent(CodeAgent):
    def __init__(self, nav_response: Message, code_context: CodeContext):
        super().__init__()

        self.code_context = code_context
        self.nav_response = nav_response

        self.tests: list[str] = []
        self.imports: list[str] = []

    def system_prompt(self) -> str:
        return templates.SystemTemplate(
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

    def user_prompt(self) -> str:
        return templates.GenerationPrompt(
            targets=self.code_context.signatures,
            additional_objects=self.code_context.undefined,
            tests=[self.code_context.test_source],
            command=nl_join(
                "Please write a pytest-compatible test suite that compliments the test(s) provided by the user.",
                "Please note that you should *not* actually implement the system under test - that will be handled",
                "by the Developer role agent.",
                "Just write the tests for the system.",
            ),
        ).render()

    async def initial_generation(self) -> Message:
        response = await super().initial_generation()
        self.tests = parsing.extract_tests(response.content)
        self.imports = parsing.extract_and_filter_imports(response.content)
        tests_compiled = parsing.compile_tests(tests=self.tests, imports=self.imports)
        response.content = tests_compiled
        return response
