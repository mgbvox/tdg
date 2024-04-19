from tdg.generator import Generator


def fib_test():
    """
    /gen
    fib:
        - doc: An efficient implementation of the fibbonacci function.
        - args:
            - input: int
        - returns: int
    /end_gen
    """
    assert fib(1) == 1
    assert fib(2) == 1
    assert fib(3) == 2
    assert fib(4) == 3


def factorial_test():
    """
    /gen
    factorial:
        - doc: An efficient implementation of the factorial function, e.g. X!.
        - args:
            - input: int
        - returns: int
    /end_gen
    """
    assert factorial(1) == 1
    assert factorial(2) == 2 * 1
    assert factorial(3) == 3 * 2 * 1


def test_generator():
    gen = Generator(
        factorial_test,
        fib_test,
    )
    gen.generate()
    for result in gen.results:
        assert result
