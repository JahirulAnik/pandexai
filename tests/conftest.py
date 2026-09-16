import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
FIXTURES_DIR = REPO_ROOT / "test_fixtures"

# The scripts use flat imports (`from loaders import ...`), so they must be importable
# as top-level modules. pyproject.toml also sets pythonpath, this is a belt-and-braces
# fallback for running pytest outside the project config.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def fixtures(tmp_path):
    """Copy of test_fixtures/ in a temp dir so scripts can write *_results folders
    without polluting the repo."""
    dest = tmp_path / "fixtures"
    shutil.copytree(FIXTURES_DIR, dest)
    return dest


@pytest.fixture
def python_exe():
    return sys.executable


@pytest.fixture
def scripts_dir():
    return SCRIPTS_DIR
