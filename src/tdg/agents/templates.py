import abc

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

CODE_GENERATOR = """
IMPORTANT: Your output will be passed directly to a python interpreter.
As such, you should *only* output code; any commentary you provide should
be in the form of # python comments or docstrings.
"""


def nl_join(*args: str) -> str:
    return "\n".join(args)


class Template(BaseModel, abc.ABC):
    @abc.abstractmethod
    def render(self) -> str:
        raise NotImplementedError()


class SystemTemplate(Template):
    role: str
    description: str
    extra_context: list[str] = Field(default_factory=list)

    def render(self):
        extra = nl_join(*self.extra_context)

        return nl_join(
            "You are a Pair Programming agent in a multi-agent environment.",
            f"Your role is '{self.role}.'",
            self.description,
            extra,
        )


class GenerationPrompt(Template):
    targets: list[str] = Field(default_factory=list)
    tests: list[str] = Field(default_factory=list)
    additional_objects: list[str] = Field(default_factory=list)

    command: str = ""

    def render(self):
        target_ctx = ""
        if self.targets:
            sig = "signature" + ("s" if len(self.targets) > 1 else "")
            is_are = "is" if len(self.targets) == 1 else "are"
            target_ctx = nl_join(
                f"The {sig} of the code to generate {is_are}:",
                *self.targets,
            )

        additional_ctx = ""
        if self.additional_objects:
            additional_objects = ", ".join(self.additional_objects)
            additional_ctx = nl_join(
                "The following code objects are not defined in the global or local context and so likely will also need to be generated:",
                additional_objects,
            )

        test_ctx = ""
        if self.tests:
            test_ctx = nl_join(
                "The user has provided the following test(s) for this context:",
                *self.tests,
            )

        combined = nl_join(
            "A user wants to generate some code. This code will need to pass a series of unit tests.",
            target_ctx,
            additional_ctx,
            test_ctx,
            self.command,
        )

        return combined
