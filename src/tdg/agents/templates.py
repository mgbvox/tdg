import abc
import re
import textwrap

from pydantic import BaseModel, Field

PERFORMANCE_CRITICAL = """
    Please also note that you are running in a performance-critical environment; your generated responses should be:
        * short
        * concise
        * to the point
        * high level
        * optimally useful
"""

AVOID_PITFALLS = """
    You should avoid:
        * extraneous context
        * obvious information that does not need to be clarified
        * meta-commentary on the problem
"""


class Template(BaseModel, abc.ABC):
    @abc.abstractmethod
    def render(self) -> str:
        raise NotImplementedError()


class SystemTemplate(Template):
    role: str
    description: str
    extra_context: list[str] = Field(default_factory=list)

    def render(self):
        extra = "\n".join(
            [textwrap.dedent(item) for item in self.extra_context]
        ).strip()

        return textwrap.dedent(
            f"""
            You are a Pair Programming agent in a multi-agent environment.

            Your role is "{self.role}."

            {self.description}

            {extra}
            """
        )


class GenerationPrompt(Template):
    prompt: str
    targets: list[str] = Field(default_factory=list)
    tests: list[str] = Field(default_factory=list)
    additional_objects: list[str] = Field(default_factory=list)

    command: str = ""

    def render(self):
        target_ctx = ""
        if self.targets:
            targets = "\n".join(self.targets)
            target_ctx = textwrap.dedent(
                f"""
                The signature(s) of the code to generate is/are:
                {targets}
                """
            )

        additional_ctx = ""
        if self.additional_objects:
            additional_objects = ", ".join(self.additional_objects)
            additional_ctx = textwrap.dedent(
                f"""The following code objects are not defined in the global
                or local context and so likely will also need to be generated:
                {additional_objects}
                """
            )

        test_ctx = ""
        if self.tests:
            test_source = "\n".join(self.tests)
            test_ctx = textwrap.dedent(
                f"""
                The user has provided the following test(s) for this context:
                {test_source}
                """
            )

        combined = textwrap.dedent(
            f"""
            A user wants to generate some code. This code will need to pass a series of unit tests.

            The code that needs to be generated must satisfy the following prompt:
            {self.prompt}

            {target_ctx}

            {additional_ctx}

            {test_ctx}

            {self.command}
            """
        )
        clean = re.sub(r"\n{2+}", "\n", combined)
        return clean
