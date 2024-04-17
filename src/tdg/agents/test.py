from openai.types.chat import ChatCompletion

from tdg import parsing
from tdg.agents import Agent, NavAgentPre, templates
from tdg.agents.base import CodeAgent
from tdg.agents.templates import nl_join


class TestAgent(CodeAgent):
    def __init__(self, nav_pre: NavAgentPre):
        super().__init__()
        self.nav_response = nav_pre.gen_response
        self.context = nav_pre.context

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
                    self.nav_response,
                ),
                templates.CODE_GENERATOR,
            ],
        ).render()

    def user_prompt(self) -> str:
        return templates.GenerationPrompt(
            targets=self.context.signatures,
            additional_objects=self.context.undefined,
            tests=[self.context.test_source],
            command=nl_join(
                "Please write a pytest-compatible test suite that compliments the test(s) provided by the user.",
                "Please note that you should *not* actually implement the system under test - that will be handled",
                "by the Developer role agent.",
                "Just write the tests for the system.",
            ),
        ).render()
