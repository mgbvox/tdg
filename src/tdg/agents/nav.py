from tdg.agents import templates
from tdg.agents.base import Agent, CodeContext, Message
from tdg.parsing import nl_join


class NavAgent(Agent):
    def __init__(self, code_context: CodeContext):
        self.code_context = code_context
        super().__init__()

    def system_prompt(self) -> str:
        return templates.SystemTemplate(
            role="Navigator",
            description=nl_join(
                "Navigators look at the context and reason on a high level about what needs to be done to solve a given problem.",
                "You should NOT actually solve the problem - rather, you should provide maximally relevant context such that the",
                "Developer and Test Designer agents can perform their jobs optimally.",
            ),
            extra_context=[templates.PERFORMANCE_CRITICAL, templates.AVOID_PITFALLS],
        ).render()

    def user_prompt(self) -> str:
        """
        Generate a navigator analysis prompt N_pre = G_nav(p,T) from the prompt and human derived tests.

        Returns:
            Prompt N_pre.
        """

        return templates.GenerationPrompt(
            targets=self.code_context.signatures,
            additional_objects=self.code_context.undefined,
            tests=[self.code_context.test_source],
            command=nl_join(
                "Please reason in detail about what the user will need to do to solve the problem.",
                "Think in particular about any gotchas and edge cases that might be encountered.",
            ),
        ).render()

    async def ensure_output_valid(self, message: Message):
        return message
