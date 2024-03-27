from typing import Union, TypeVar

import pexpect


def print_shell(inp: bytes):
    for line in inp.decode("utf-8").splitlines():
        print(line)


T = TypeVar("T")


def ensure_list(item: Union[T, list[T]]) -> list[T]:
    if not isinstance(item, list):
        item = [item]
    return item


def do_py_cmd(
    cmd,
    shell: pexpect.spawn,
    level: int = 0,
    indent: str = "    ",
    prompt: str = ">>>",
):
    tab = indent * level
    expect = lambda: shell.expect([">>>", "\.\.\."])

    if isinstance(cmd, dict):
        # nested, e.g. for loop
        # format:
        # {outer : [inner, commands]}
        # e.g:
        # {"for i in range(10)" : ["print(i)", "print(i**2)"]}
        assert len(cmd) == 1, ValueError("Only a single for loop dict allowed!")
        loop_start, contents = list(cmd.items())[0]
        if not loop_start[-1] == ":":
            loop_start += ":"

        print(f"{prompt} {loop_start}")
        shell.sendline(loop_start)
        expect()

        contents = ensure_list(contents)
        # recursively kick off inputting subcommands
        do_py_cmd(cmd=contents, shell=shell, level=level + 1, prompt="...")

        # execute the loop
        shell.sendline()
        expect()

    elif isinstance(cmd, list):
        # we're sending contents of a for loop:
        for subcmd in cmd:
            # tab them in and execute one by one
            do_py_cmd(cmd=f"{tab}{subcmd}", shell=shell, prompt=prompt)

    else:
        shell.sendline(cmd)
        expect()

    print_shell(shell.before)


def do_py(*cmds):
    s = pexpect.spawn("bash")
    prompt = ">>>"
    s.sendline("python")
    s.expect(prompt)
    print_shell(s.before)
    for c in cmds:
        do_py_cmd(c, shell=s)

    s.close(force=True)


if __name__ == "__main__":
    do_py(
        "import sys",
        {"for p in sys.path": "print(p)"},
        {"for i in range(10)": ["i += 1", "print(i)", "print(i**2)"]},
    )
