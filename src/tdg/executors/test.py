import random
import string
from typing import Optional

import pytest
from _pytest.config import ExitCode
from pydantic import BaseModel

from tdg import context_managers as cm
from tdg.parsing import is_valid_python


class TestReport(BaseModel):
    nodeid: str
    outcome: str
    longrepr: str


class PytestReportPlugin:
    def __init__(self):
        self.failures: list[TestReport] = []
        self.successes: list[TestReport] = []
        self.exit_code: Optional[ExitCode] = None

    def pytest_runtest_logreport(self, report):
        report_info = {
            "nodeid": report.nodeid,
            "outcome": report.outcome,
            "longrepr": str(report.longrepr),
        }
        parsed = TestReport.model_validate(report_info)
        if report.failed:
            self.failures.append(parsed)
        else:
            self.successes.append(parsed)

    def pytest_sessionfinish(self):
        # Here, you could further process the reports or print them.
        pass


class TestExecutor:
    """
    A class for executing test cases and tracking results.
    """

    def __init__(self, script: str):
        if not is_valid_python(script):
            raise ValueError(f"Script was not valid python code:\n\n{script}")
        self.script = script
        self.tracker = PytestReportPlugin()

        self.exit_code: int | ExitCode = -1

    def test(self):
        """Invoke the provided test script"""

        with cm.TempDir() as tmpdir:
            uuid = "".join(random.choices(string.ascii_letters, k=12))
            tmp_test_file = tmpdir.root / f"test_cases_{uuid}.py"
            tmp_test_file.write_text(self.script)

            out = pytest.main(
                [str(tmp_test_file), "-vvv"],
                plugins=[self.tracker],
            )
            self.exit_code = out

    def passed(self) -> bool:
        return self.exit_code == ExitCode.OK
