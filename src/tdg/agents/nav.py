import importlib
import inspect
import textwrap
from typing import Callable

from tdg.agents import templates
from tdg.agents.base import Agent
from tdg.extractors.str2str import UndefinedFinder
from tdg.parsing import find_gen_signatures


class NavAgent(Agent):
    @classmethod
    def system_prompt(cls) -> str:
        return templates.SystemTemplate(
            role="Navigator",
            description=textwrap.dedent(
                """
                Navigators look at the context and reason on a high level about what needs to be done to solve a given problem.
                You should NOT actually solve the problem - rather, you should provide maximally relevant context such that the
                Developer and Test Designer agents can perform their jobs optimally.
                """
            ),
            extra_context=[templates.PERFORMANCE_CRITICAL, templates.AVOID_PITFALLS],
        ).render()

    def __init__(self, test: Callable):
        super().__init__()

        self.test = test
        test_module = importlib.import_module(test.__module__)
        test_globals = vars(test_module)
        prior_frame = inspect.currentframe().f_back
        test_locals = prior_frame.f_locals

        self.prompt = ""
        self.test_source = inspect.getsource(test)
        self.test_source = self.test_source.replace(test.__doc__, "")
        self.undefined = (
            UndefinedFinder(test_globals, test_locals).visit_code(test).undefined
        )
        self.signatures = find_gen_signatures(test.__doc__)

    def _gen_prompt_first_pass(self) -> str:
        """
        Generate a navigator analysis prompt N_pre = G_nav(p,T) from the prompt and human derived tests.

        Returns:
            Prompt N_pre.
        """
        code_to_generate_chunk = []
        additional_objects = []

        for idx, undefined in enumerate(self.undefined):
            if sig := self.signatures.get(undefined):
                indented_sig = textwrap.indent(sig, "\t\t\t")
                code_to_generate_chunk.append(
                    f"\t{idx}. Function name: {undefined}\n\t\tWith signature:\n{indented_sig}"
                )
            else:
                additional_objects.append(undefined)

        return templates.GenerationPrompt(
            prompt=self.prompt,
            targets=code_to_generate_chunk,
            additional_objects=additional_objects,
            tests=[self.test_source],
            command=(
                "Please reason in detail about what the user will need to do to solve the problem. "
                "Think in particular about any gotchas and edge cases that might be encountered."
            ),
        ).render()
