from abc import ABC, abstractmethod
from enum import Enum, auto


class Role(Enum):
    Navigator = auto()
    Programmer = auto()
    Test_Designer = auto()


"""

agents explored by AgentCoder:
"gpt-3.5-turbo"
"palm-2-codechat-bison"
"claude-instant-1"
"gpt-4-1106-preview"
"gpt-4"

maybe Roles want to be full classes? dspy signatures?

for generation, Navigator maybe wants to be RAG
to lookup context for given algos, etc


test gen should be conditioned to include edge cases
and large / small cases
Populate TDD code with generated tests on pass

Though it may be tempting to just generate assert lines
e.g. assert case 1 \n assert case 2,
if we want to insert test cases back into the original
source they need to be pytest cases.

Perhaps generate three tests by default -
def test_{fn_name}_base_cases
def test_{fn_name}_edge_cases
def test_{fn_name}_large_and_small_cases


Instructions for codegen from AgentCoder:
**Instructions**:
1. **Understand and Clarify**:
Make sure you understand the task. If necessary, write down what the function should do.
2. **Algorithm/Method Selection**:
Decide on the most efficient way to compare the numbers in the list to find if any two are within the threshold.
3. **Pseudocode Creation**:
Write down the steps you will follow in pseudocode. This should outline how you will iterate through the list and compare the numbers.
4. **Code Generation**:
Translate your pseudocode into executable Python code. Remember to test your function with the provided examples and any additional cases you think are relevant.

"""


class Generator(ABC):
    def __init__(self, role: Role):
        self.role = role

    @abstractmethod
    def generate(self):
        raise NotImplementedError()


def test_gen():
    openai_gen = OpenAIGen(role=...)


def test_foo():

    codegen = OpenAIGen()
    tester = TextExecutor()
