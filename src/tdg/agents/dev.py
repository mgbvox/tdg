from tdg import parsing
from tdg.agents import templates
from tdg.agents.base import CodeAgent, CodeContext, Message
from tdg.parsing import nl_join


class DevAgent(CodeAgent):
    def __init__(self, test_response: Message, code_context: CodeContext) -> None:
        super().__init__()
        self.code_context = code_context
        self.test_suite = nl_join("```python", test_response.content, "```")

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
            targets=self.code_context.signatures,
            additional_objects=self.code_context.undefined,
            tests=[self.test_suite],
            command=nl_join(
                "Please implement the following functions to pass the provided tests:",
                *self.code_context.fn_names,
                "",
                "Please also implement any necessary undefined code objects.",
                "NOTE: The code you generate will be placed above the test suite provided by the Test Designer agent;",
                "As such, you do not need to reimplement any of the provided tests.",
            ),
        ).render()

    async def continue_generation(self, message: str) -> Message:
        response = await super().continue_generation(message)
        response.content = parsing.clean_openai_code_or_error(response.content)
        return response
