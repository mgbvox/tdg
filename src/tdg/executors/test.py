import asyncio
import json
import random
import string
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest
from _pytest.config import ExitCode
from pydantic import BaseModel

from tdg import context_managers as cm
from tdg.parsing import is_valid_python


class TestReport(BaseModel):
    nodeid: str
    outcome: str
    longrepr: Optional[str] = None


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


class Report:
    def __init__(self, reports: list[TestReport], exit_code: ExitCode):
        self.failures: list[TestReport] = [r for r in reports if r.outcome != "passed"]
        self.successes: list[TestReport] = [r for r in reports if r.outcome == "passed"]
        self.exit_code: Optional[ExitCode] = exit_code


async def run_pytest_with_json_report(test_file_path: Path):
    # Define the path for the JSON report
    json_report_path = test_file_path.parent / "test_report.json"

    # Command to run pytest in subprocess
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        test_file_path,
        "--json-report",  # Enable JSON reporting
        f"--json-report-file={json_report_path}",  # Specify the JSON report file path
    ]

    # Start the subprocess
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    # Wait for the subprocess to finish
    await process.wait()

    # Read the JSON report
    if json_report_path.exists():
        with open(json_report_path, "r") as file:
            report_data = json.load(file)
            # Extract data from the report
            return Report(
                [TestReport.model_validate(test) for test in report_data["tests"]],
                exit_code=report_data["exitcode"],
            )
    else:
        raise FileNotFoundError(
            f"JSON report not found, expected at {json_report_path}"
        )


class TestExecutor:
    """
    A class for executing test cases and tracking results.
    """

    def __init__(self, script: str, path: Optional[Path] = None):
        if not is_valid_python(script):
            raise ValueError(f"Script was not valid python code:\n\n{script}")
        self.script = script
        self.path = path
        self.tracker = None

        self.exit_code: int | ExitCode = -1

    async def test(self):
        """Invoke the provided test script"""

        with cm.TempDir() as tmpdir:
            if not self.path:
                uuid = "".join(random.choices(string.ascii_letters, k=12))
                tmp_test_file = tmpdir.root / f"test_cases_{uuid}.py"
                tmp_test_file.write_text(self.script)
                self.path = tmp_test_file

            self.tracker = await run_pytest_with_json_report(self.path)

            self.exit_code = self.tracker.exit_code
        return self

    def passed(self) -> bool:
        return self.exit_code == ExitCode.OK

    def n_failures(self) -> int:
        return len(self.tracker.failures)
