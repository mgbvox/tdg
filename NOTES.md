# TODOs, Notes, Musings, and Assorted Shindiggery


## TODO
* Map canonical solution/test examples into pytest module
* Implement pytest executor module
* Include example base tests with code generation prompt
* Navigator can perform RAG for algorithm look up, search, etc.
* Perhaps navigator also tackles pseudocode generation? AB test this.


## Later / Ideas
Let each generator role know about the other roles, and allow e.g role A to
query role B, C, etc.

Provide a query budget and let each generator know how many queries are
remaining. Instruct to minimize queries where possible, but to
prioritize correctness and ask for clarifications where needed.

We can think of multi agent generation as a directed graph, or flowchart,
the sequencing of which *can probably be learned.* Graph neural networks / reinforcement learning?

This optimal flow is probably different for a given question, and we probably
don’t want to be manually implementing a single flow for all questions.

Why limit the underlying language models to a single system?
Different model types are probably better for different constraints,
e.g. time and use cases/context. This query -> language model routing problem
can also probably be learned.

When a given role receives context, some of this is probably redundant or
even counterproductive for the specific role's intent. What if we added a
context filtering step that took as input bulk context and role information
and output a shorter, more distilled context, optimized for a given role?
