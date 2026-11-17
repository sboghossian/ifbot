"""The outer loop: make a workspace, let a proposer command edit it, submit it to the gate."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Union

from ..evals.judge import Judge
from ..evals.run import DEFAULT_TIMEOUT
from ..paths import ledger_path, resolve_root
from .gate import GateResult, submit
from .ledger import Ledger
from .workspace import new_workspace

log = logging.getLogger("ifbot.loop")

DEFAULT_PROPOSER_TIMEOUT = 900.0


def run(
    rounds: int,
    proposer_cmd: str,
    root: Optional[Union[str, Path]] = None,
    judge: Optional[Judge] = None,
    timeout: float = DEFAULT_TIMEOUT,
    proposer_timeout: float = DEFAULT_PROPOSER_TIMEOUT,
    keep_workspaces: bool = False,
) -> List[GateResult]:
    """Run `rounds` rounds. The proposer runs with cwd=workspace and IFBOT_WORKSPACE set."""
    root = resolve_root(root)
    results = []  # type: List[GateResult]
    for n in range(1, rounds + 1):
        ws = new_workspace(root, judge=judge)
        log.info("round %d/%d: workspace %s", n, rounds, ws)
        env = dict(os.environ, IFBOT_WORKSPACE=str(ws))
        failure = None
        try:
            proc = subprocess.run(
                proposer_cmd, shell=True, cwd=str(ws), env=env, timeout=proposer_timeout,
                stdin=subprocess.DEVNULL,
            )
            if proc.returncode != 0:
                failure = "proposer exited %d" % proc.returncode
        except subprocess.TimeoutExpired:
            failure = "proposer timed out after %gs" % proposer_timeout
        if failure:
            log.warning("round %d: %s", n, failure)
            Ledger(ledger_path(root)).append(
                {"candidate": "round-%d" % n, "accepted": False, "reason": failure}
            )
            results.append(GateResult("round-%d" % n, False, failure))
        else:
            results.append(submit(ws, root=root, judge=judge, timeout=timeout))
        if not keep_workspaces:
            shutil.rmtree(str(ws), ignore_errors=True)
    return results
