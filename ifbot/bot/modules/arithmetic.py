"""Simple sums, evaluated by walking a whitelisted syntax tree. Never calls eval()."""

from __future__ import annotations

import ast
import operator
import re
from typing import TYPE_CHECKING, Optional, Union

from ..arbiter import Proposal

if TYPE_CHECKING:  # pragma: no cover
    from ..engine import Context

Number = Union[int, float]

_MAX_LEN = 100
_MAX_EXPONENT = 64
_MAX_RESULT = 10 ** 30

_BIN = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}

_WORD_OPS = [
    (re.compile(r"\bto the power of\b"), " ** "),
    (re.compile(r"\bmultiplied by\b"), " * "),
    (re.compile(r"\bdivided by\b"), " / "),
    (re.compile(r"\bmodulo\b|\bmod\b"), " % "),
    (re.compile(r"\bover\b"), " / "),
    (re.compile(r"\bplus\b"), " + "),
    (re.compile(r"\bminus\b"), " - "),
    (re.compile(r"\btimes\b"), " * "),
    (re.compile(r"(?<=\d)\s*x\s*(?=\d)"), " * "),
]
_FILLER = re.compile(
    r"\b(what|is|calculate|compute|solve|how|much|equals|equal|evaluate|tell|me|the|result|answer|please)\b"
)


class TooBig(Exception):
    """Raised for sums we refuse to do (too big)."""


def _eval(node: ast.AST) -> Number:
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_eval(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and (abs(right) > _MAX_EXPONENT or abs(left) > 10 ** 6):
            raise TooBig("too big")
        result = _BIN[type(node.op)](left, right)
        if isinstance(result, complex) or abs(result) > _MAX_RESULT:
            raise TooBig("too big")
        return result
    raise ValueError("unsupported syntax")


def _format(value: Number) -> str:
    if isinstance(value, float):
        if value.is_integer() and abs(value) < 1e15:
            return str(int(value))
        return "%.10g" % value
    return str(value)


def _extract(text: str) -> Optional[str]:
    """Return the bare expression if the whole message is a sum, else None."""
    s = text.replace("×", "*").replace("÷", "/").replace("^", " ** ")
    s = s.replace("%", " percent ")
    s = re.sub(r"(?<=\d),(?=\d{3}\b)", "", s)
    for pattern, repl in _WORD_OPS:
        s = pattern.sub(repl, s)
    s = _FILLER.sub(" ", s)
    s = re.sub(r"[?=!]", " ", s).strip().rstrip(".,").strip()
    if not s or not re.search(r"\d", s) or not re.fullmatch(r"[\d+\-*/().\s]+", s):
        return None
    if not re.search(r"[+\-*/]", s):
        return None
    return re.sub(r"\s+", " ", s)[:_MAX_LEN * 2]


def propose(ctx: "Context") -> Optional[Proposal]:
    expr = _extract(ctx.text)
    if expr is None:
        return None
    if len(expr) > _MAX_LEN:
        return Proposal("That sum is too long for me.", 0.6)
    try:
        tree = ast.parse(expr, mode="eval")
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        return Proposal("I couldn't read that as a sum. Try something like 12 * 7.", 0.6)
    if not isinstance(tree.body, (ast.BinOp,)):
        return None  # a bare signed number is not a question
    try:
        value = _eval(tree)
    except ZeroDivisionError:
        return Proposal("I can't divide by zero.", 0.95)
    except TooBig:
        return Proposal("That number is too big for me.", 0.6)
    except (ValueError, OverflowError, RecursionError):
        return Proposal("I couldn't read that as a sum. Try something like 12 * 7.", 0.6)
    return Proposal("%s = %s" % (expr, _format(value)), 0.95)
