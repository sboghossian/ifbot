"""Locate and import the bot under test.

Works in the real checkout (../ifbot/bot) and in a candidate workspace (../bot). Set IFBOT_BOT_DIR
to point somewhere else. The bot is loaded as a throwaway package so its relative imports work.
"""

import importlib.util
import os
import sys
import uuid
from pathlib import Path

_package = None


def bot_dir():
    env = os.environ.get("IFBOT_BOT_DIR")
    if env:
        return Path(env)
    base = Path(__file__).resolve().parent.parent
    for candidate in (base / "ifbot" / "bot", base / "bot"):
        if (candidate / "__init__.py").is_file():
            return candidate
    raise FileNotFoundError("no bot package found next to the tests")


def load_package():
    global _package
    if _package is None:
        directory = bot_dir()
        name = "_ifbot_under_test_" + uuid.uuid4().hex[:8]
        spec = importlib.util.spec_from_file_location(
            name, str(directory / "__init__.py"), submodule_search_locations=[str(directory)]
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        _package = module
    return _package


def new_bot(seed=0):
    return load_package().Bot(seed=seed)
