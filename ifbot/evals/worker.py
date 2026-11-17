"""Standalone worker: load a bot package from a directory and answer a list of instructions.

Run as a script in its own interpreter so candidate code never enters the harness process:

    python -I worker.py <bot_dir>      (JSON [{"id", "instruction"}, ...] on stdin)

Prints JSON [{"id", "text", "module"}, ...] on stdout. Each instruction gets a fresh Bot.
This file must stay free of imports from ifbot.
"""

import importlib.util
import json
import sys
import uuid
from pathlib import Path


def load_package(bot_dir):
    name = "_ifbot_candidate_" + uuid.uuid4().hex[:8]
    init = Path(bot_dir) / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        name, str(init), submodule_search_locations=[str(Path(bot_dir))]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: worker.py <bot_dir>\n")
        return 2
    rows = json.loads(sys.stdin.read())
    real_stdout = sys.stdout
    sys.stdout = sys.stderr  # stray prints from the bot must not corrupt the JSON
    package = load_package(argv[1])
    results = []
    for row in rows:
        bot = package.Bot(seed=0)
        try:
            reply = bot.respond(row["instruction"])
            text, module = str(reply.text)[:2000], str(reply.module)
        except Exception as exc:  # a crashing bot loses the row, it does not stop the run
            text, module = "", "error:" + type(exc).__name__
        results.append({"id": row["id"], "text": text, "module": module})
    real_stdout.write(json.dumps(results))
    real_stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
