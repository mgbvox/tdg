import subprocess
from pathlib import Path

from _pytest.config import ExitCode

from tdg import context_managers as cm

import pytest


def test_plugin():
    with cm.TempDir(root=Path(__file__).parent) as td:
        before = td["test_before"]
        before_content_pre = before.read_text()

        # open in charm
        subprocess.run(["charm", str(before)])
        out = pytest.main([str(before)])
        assert out is ExitCode.OK

        before_content_post = before.read_text()
        after = td["test_after"]
        after_content = after.read_text()

        assert after_content != before_content_pre
        assert before_content_post == after_content
