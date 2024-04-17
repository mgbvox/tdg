from tdg.agents import TestAgent, templates
from tdg.agents.base import CodeAgent
from tdg.agents.templates import nl_join


class DevAgent(CodeAgent):
    def __init__(self, test_agent: TestAgent):
        super().__init__()
        self.test_agent = test_agent
        self.context = test_agent.context
        self.test_suite = nl_join("```python", self.test_agent.gen_response, "```")

        self.gen_response = ""

    def system_prompt(self) -> str:
        return templates.SystemTemplate(
            role="Developer",
            description="Developers implement python code that satisfies the test constraints provided by the Test Designer role agent.",
            extra_context=[
                templates.PERFORMANCE_CRITICAL,
                templates.AVOID_PITFALLS,
                nl_join(
                    "The test suite your code must pass is as follows:",
                    self.test_suite,
                ),
                templates.CODE_GENERATOR,
            ],
        ).render()

    def user_prompt(self) -> str:
        return templates.GenerationPrompt(
            targets=self.context.signatures,
            additional_objects=self.context.undefined,
            tests=[self.test_suite],
            command=nl_join(
                "Please implement the following functions to pass the provided tests:",
                *self.context.fn_names,
                "",
                "Please also implement any necessary undefined code objects.",
                "NOTE: The code you generate will be placed above the test suite provided by the Test Designer agent;",
                "As such, you do not need to reimplement any of the provided tests.",
            ),
        ).render()
