"""Command line entry point: chat, eval, and the evolve subcommands."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Optional, TextIO

from . import __version__
from .evals.dataset import DatasetError, load_rows
from .evals.judge import CommandJudge, Judge, OverlapJudge
from .evals.run import DEFAULT_TIMEOUT, evaluate, load_package
from .paths import bot_dir, data_path, ledger_path, resolve_root

BANNER = """\
  .-----------------------------.
  |  if(bot)   v%s          |
  |  a tiny rules-only chatbot  |
  '-----------------------------'
  /reset starts over, /exit leaves.
""" % __version__


def _say(bot, text: str, verbose: bool, out: TextIO, err: TextIO, label: str = "") -> None:
    start = time.perf_counter()
    reply = bot.respond(text)
    ms = (time.perf_counter() - start) * 1000
    out.write(label + reply.text + "\n")
    if verbose:
        err.write("  [%s, confidence %.2f, %.1f ms]\n" % (reply.module, reply.confidence, ms))


def _chat(args: argparse.Namespace, root: Path) -> int:
    Bot = load_package(bot_dir(root)).Bot
    bot = Bot(seed=args.seed)
    if args.prompt is not None:
        _say(bot, args.prompt, args.verbose, sys.stdout, sys.stderr)
        return 0
    if not sys.stdin.isatty():
        for line in sys.stdin:
            _say(bot, line.rstrip("\n"), args.verbose, sys.stdout, sys.stderr)
        return 0
    sys.stdout.write(BANNER)
    while True:
        try:
            line = input("you> ")
        except (EOFError, KeyboardInterrupt):
            sys.stdout.write("\n")
            return 0
        command = line.strip().lower()
        if command in ("/exit", "/quit"):
            return 0
        if command == "/reset":
            bot.reset()
            sys.stdout.write("(conversation reset)\n")
            continue
        _say(bot, line, args.verbose, sys.stdout, sys.stdout, label="bot> ")


def _make_judge(args: argparse.Namespace) -> Judge:
    if args.judge == "command":
        if not args.judge_cmd:
            raise SystemExit("--judge command needs --judge-cmd")
        return CommandJudge(args.judge_cmd, timeout=args.judge_timeout)
    return OverlapJudge(args.threshold)


def _judge_name(judge: Judge) -> str:
    return getattr(judge, "name", type(judge).__name__)


def _eval(args: argparse.Namespace, root: Path) -> int:
    rows = load_rows(data_path(root, args.split))
    judge = _make_judge(args)
    report = evaluate(bot_dir(root), rows, judge)
    if args.json:
        out = dict(report, split=args.split, judge=_judge_name(judge))
        sys.stdout.write(json.dumps(out, indent=2) + "\n")
        return 0
    w = sys.stdout.write
    w("split: %s (%d rows)   judge: %s\n" % (args.split, report["total"], _judge_name(judge)))
    w("win rate: %d/%d = %.3f\n" % (report["wins"], report["total"], report["win_rate"]))
    w("by category:\n")
    for cat, stats in sorted(report["by_category"].items()):
        w("  %-10s %d/%d  %.3f\n" % (cat, stats["wins"], stats["total"], stats["win_rate"]))
    if args.failures:
        w("losses:\n")
        for f in report["failures"]:
            w("  %s [%s] %s\n    bot: %s\n" % (f["id"], f["module"], f["instruction"], f["reply"]))
    return 0


def _evolve(args: argparse.Namespace, root: Path) -> int:
    from .evolve import gate, loop, workspace
    from .evolve.ledger import Ledger, format_table

    cmd = args.evolve_command
    if cmd == "new":
        sys.stdout.write(str(workspace.new_workspace(root)) + "\n")
        return 0
    if cmd == "submit":
        result = gate.submit(args.dir, root=root, judge=_make_judge(args), timeout=args.timeout)
        sys.stdout.write(_result_line(result) + "\n")
        return 0 if result.accepted else 1
    if cmd == "run":
        results = loop.run(
            args.rounds, args.proposer_cmd, root=root, judge=_make_judge(args), timeout=args.timeout,
            proposer_timeout=args.proposer_timeout, keep_workspaces=args.keep,
        )
        for r in results:
            sys.stdout.write(_result_line(r) + "\n")
        kept = sum(1 for r in results if r.accepted)
        sys.stdout.write("%d of %d rounds kept\n" % (kept, len(results)))
        return 0
    if cmd == "log":
        rows = Ledger(ledger_path(root)).rows()
        sys.stdout.write((format_table(rows) if rows else "ledger is empty") + "\n")
        return 0
    return 2


def _result_line(r) -> str:
    rate = "n/a" if r.heldout_win_rate is None else "%.3f" % r.heldout_win_rate
    return "%s %s heldout=%s: %s" % ("ACCEPTED" if r.accepted else "REJECTED", r.candidate, rate, r.reason)


def _add_judge_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--judge", choices=("overlap", "command"), default="overlap")
    p.add_argument("--judge-cmd", help="shell command for --judge command (JSON on stdin, WIN or LOSS on stdout)")
    p.add_argument("--judge-timeout", type=float, default=60.0, help="seconds per judge call")
    p.add_argument("--threshold", type=float, default=0.35, help="overlap judge F1 threshold")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ifbot", description="A tiny rules-only chatbot and its evolution harness.")
    p.add_argument("-p", "--prompt", help="answer one message and exit")
    p.add_argument("-s", "--seed", type=int, default=0, help="random seed for reply variety")
    p.add_argument("-v", "--verbose", action="store_true", help="show the winning module and timing")
    p.add_argument("--root", help="project root (default: this checkout)")
    sub = p.add_subparsers(dest="command")

    ev = sub.add_parser("eval", help="score the current bot on a split")
    ev.add_argument("--split", choices=("dev", "heldout"), default="dev")
    ev.add_argument("--json", action="store_true")
    ev.add_argument("--failures", action="store_true", help="list the rows the bot lost")
    _add_judge_args(ev)

    evo = sub.add_parser("evolve", help="grow the bot by hill-climbing")
    es = evo.add_subparsers(dest="evolve_command", required=True)
    es.add_parser("new", help="create a candidate workspace and print its path")
    sm = es.add_parser("submit", help="run the gate on a candidate workspace")
    sm.add_argument("dir")
    sm.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="seconds per subprocess")
    _add_judge_args(sm)
    rn = es.add_parser("run", help="run rounds of propose then submit")
    rn.add_argument("--rounds", type=int, default=1)
    rn.add_argument("--proposer-cmd", required=True, help="shell command run inside each workspace")
    rn.add_argument("--proposer-timeout", type=float, default=900.0)
    rn.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="seconds per gate subprocess")
    rn.add_argument("--keep", action="store_true", help="keep workspaces after each round")
    _add_judge_args(rn)
    es.add_parser("log", help="print the ledger")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    level = logging.DEBUG if args.verbose else logging.INFO if args.command == "evolve" else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s", stream=sys.stderr)
    root = resolve_root(args.root)
    try:
        if args.command == "eval":
            return _eval(args, root)
        if args.command == "evolve":
            return _evolve(args, root)
        return _chat(args, root)
    except DatasetError as exc:
        sys.stderr.write("dataset error: %s\n" % exc)
        return 2
    except BrokenPipeError:
        return 0
