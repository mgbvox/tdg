import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional


class TempDir:
    def __init__(self, *, root: Optional[Path] = None):
        self._temp_files: dict[str, Path] = {}
        self._orig_root = root
        self.root: Optional[Path] = None

    def __enter__(self):
        tmp_dir = Path(tempfile.mkdtemp())
        self.root = tmp_dir

        if self._orig_root:
            shutil.copytree(self._orig_root, self.root, dirs_exist_ok=True)
            for parent, dirs, files in os.walk(self._orig_root):
                for file in files:
                    file = Path(parent) / Path(file)
                    if "pyc" not in file.suffix:
                        rel_file = self.root / file.relative_to(self._orig_root)
                        self._temp_files[file.stem] = rel_file
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self.root)
        assert not self.root.exists(), FileExistsError(
            f"self.root was not removed: {self.root}"
        )

    def __getitem__(self, key: str) -> Path:
        return self._temp_files.get(key.split(".")[0])
