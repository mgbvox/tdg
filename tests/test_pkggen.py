import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Optional


class TempDir:
    def __init__(self, files: Optional[dict[str, Path]] = None):
        self._source_files = files or {}
        self._temp_files: dict[str, Path] = {}
        self._root: Optional[Path] = None

    def __enter__(self):
        tmp_dir = Path(tempfile.mkdtemp())
        self._root = tmp_dir
        for key, file in self._source_files.items():
            if file.exists():
                file_copy = tmp_dir / file.name
                shutil.copy(file, file_copy)
                self._temp_files[key] = file_copy

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self._root)

    def file(self, key: str) -> Path:
        return self._temp_files[key]


from tests import project_root, test_root
import contextlib

"""
Use cookiecutter templates to generate packages on the fly for tests?

mk_pkg(name:str, src={"main":"# the main file"}, tests={"test_foo":test_foo.read_text()})...
"""




def mk_pkg(name: Optional[str] = None) -> Path:
    name = name or f"my_package_{str(uuid.uuid4()).replace('-', '')}"
    root = test_root / f"pkgs/gen/{name}"


    return root




def test_mk_root():
    pkg = mk_pkg("cool_beans")
    with contextlib.chdir(pkg):
        out = subprocess.run("poetry shell; python -c 'import sys; print(sys.path)'", shell=True)
        print(out.stdout)



def test_shell():

    with shell("zsh") as s:
        out = s.do("echo hi")
        assert out == "hi"

        # can start python session in the shell
        s.do("python")
        s.do("x = 1")
        out = s.do("print(x)")

