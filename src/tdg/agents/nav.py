import importlib
import inspect
import textwrap
from types import FunctionType
from typing import Optional

from openai.types.chat import ChatCompletion

from tdg.agents import templates
from tdg.agents.base import Agent
from tdg.agents.templates import nl_join
from tdg.extractors.str2str import UndefinedFinder
from tdg.parsing import find_gen_signatures


class HumanProvidedContext:
    def __init__(self, test: FunctionType):
        test_module = importlib.import_module(test.__module__)
        test_globals = vars(test_module)
        prior_frame = inspect.currentframe().f_back
        test_locals = prior_frame.f_locals

        self.test_source = inspect.getsource(test)
        self.test_source = self.test_source.replace(test.__doc__, "")

        undefined = (
            UndefinedFinder(test_globals, test_locals).visit_code(test).undefined
        )
        signatures = find_gen_signatures(test.__doc__)

        self.fn_names = list(signatures.keys())
        self.signatures = []
        self.undefined = []

        for idx, undefined in enumerate(undefined):
            if sig := signatures.get(undefined):
                self.signatures.append(
                    nl_join(
                        f"{idx}. Signature for function '{undefined}':",
                        textwrap.indent(sig, "\t"),
                        "----------",
                    )
                )
            else:
                self.undefined.append(undefined)


class NavAgentPre(Agent):
    def __init__(self, test: FunctionType):
        super().__init__()

        self.test = test
        self.context = HumanProvidedContext(test)

        self.gen_response: Optional[str] = None

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
            targets=self.context.signatures,
            additional_objects=self.context.undefined,
            tests=[self.context.test_source],
            command=nl_join(
                "Please reason in detail about what the user will need to do to solve the problem.",
                "Think in particular about any gotchas and edge cases that might be encountered.",
            ),
        ).render()

    async def gen(self) -> str:
        result: ChatCompletion = await self._do_generation(
            system_prompt=self.system_prompt(),
            user_prompt=self.user_prompt(),
        )
        self.gen_response = result.choices[0].message.content
        return self.gen_response
