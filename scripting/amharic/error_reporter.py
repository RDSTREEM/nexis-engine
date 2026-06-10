"""
error_reporter.py
Produces friendly error messages in both Amharic and English
for parse errors, transpilation errors, and runtime errors.
"""
from __future__ import annotations
import re
from typing import Optional


# ── Amharic error message templates ─────────────────────────────────────────

_MSGS = {
    "syntax_error": (
        "የሰዋሰው ስህተት",
        "Syntax error"
    ),
    "unexpected_token": (
        "ያልተጠበቀ ቃል: '{token}'",
        "Unexpected token: '{token}'"
    ),
    "unexpected_eof": (
        "ፋይሉ ሳይጠናቀቅ ቆሟል",
        "Unexpected end of file"
    ),
    "undefined_name": (
        "'{name}' አልተገለጸም",
        "'{name}' is not defined"
    ),
    "type_error": (
        "የዓይነት ስህተት: {detail}",
        "Type error: {detail}"
    ),
    "indent_error": (
        "የእርከን ስህተት",
        "Indentation error"
    ),
    "missing_script_class": (
        "ስክሪፕቱ 'ስክሪፕት' ክፍል (class Script) መያዝ አለበት",
        "Script must define a 'Script' class (ስክሪፕት)"
    ),
    "missing_method": (
        "'{method}' ዘዴ አልተገኘም",
        "Method '{method}' not found"
    ),
    "runtime_error": (
        "የሩጫ ጊዜ ስህተት: {detail}",
        "Runtime error: {detail}"
    ),
    "import_error": (
        "ሞጁሉ '{module}' አልተገኘም",
        "Module '{module}' not found"
    ),
    "lark_unavailable": (
        "Lark ቤተ-ፍርድ አልተጫነም። pip install lark ያሂዱ",
        "Lark library not installed. Run: pip install lark"
    ),
}


class AmharicError(Exception):
    """Carries both Amharic and English error messages."""

    def __init__(self, key: str, line: int = 0, **kwargs):
        amh_tmpl, eng_tmpl = _MSGS.get(key, (key, key))
        self.amharic = amh_tmpl.format(**kwargs)
        self.english = eng_tmpl.format(**kwargs)
        self.line    = line
        super().__init__(self.full_message())

    def full_message(self) -> str:
        loc = f" (መስመር {self.line} / line {self.line})" if self.line else ""
        return f"{self.amharic}{loc}\n{self.english}{loc}"


# ── Lark exception → AmharicError ────────────────────────────────────────────

def from_lark_exception(exc) -> AmharicError:
    """Convert a Lark ParseError / UnexpectedToken into an AmharicError."""
    msg  = str(exc)
    line = 0

    # Extract line number from lark message
    m = re.search(r"line (\d+)", msg, re.IGNORECASE)
    if m:
        line = int(m.group(1))

    if "UnexpectedEOF" in type(exc).__name__ or "end of input" in msg.lower():
        return AmharicError("unexpected_eof", line=line)

    tok_m = re.search(r"Token\('(\w+)',\s*'([^']+)'\)", msg)
    if tok_m:
        token = tok_m.group(2)
        return AmharicError("unexpected_token", line=line, token=token)

    return AmharicError("syntax_error", line=line)


def from_python_exception(exc, source_lines: Optional[list] = None) -> str:
    """
    Convert a Python exception that occurred in transpiled code back to a
    user-friendly bilingual message, attempting to map to original .amh lines.
    """
    typ  = type(exc).__name__
    msg  = str(exc)
    line = 0

    # Extract line from traceback if available
    import traceback
    tb = traceback.extract_tb(exc.__traceback__)
    if tb:
        line = tb[-1].lineno

    if isinstance(exc, SyntaxError):
        err = AmharicError("syntax_error", line=exc.lineno or 0)
    elif isinstance(exc, NameError):
        m = re.search(r"name '(.+)' is not defined", msg)
        name = m.group(1) if m else msg
        err = AmharicError("undefined_name", line=line, name=name)
    elif isinstance(exc, TypeError):
        err = AmharicError("type_error", line=line, detail=msg)
    elif isinstance(exc, ImportError):
        m = re.search(r"No module named '(.+)'", msg)
        mod = m.group(1) if m else msg
        err = AmharicError("import_error", line=line, module=mod)
    elif isinstance(exc, IndentationError):
        err = AmharicError("indent_error", line=exc.lineno or 0)
    else:
        err = AmharicError("runtime_error", line=line, detail=f"{typ}: {msg}")

    # Annotate with source context
    context = ""
    if source_lines and 0 < line <= len(source_lines):
        context = f"\n  ▶  {source_lines[line-1].rstrip()}"

    return err.full_message() + context


def validate_script_class(python_src: str) -> Optional[AmharicError]:
    """
    Quick static check: does the transpiled source define a Script class?
    Returns an AmharicError if not, None if OK.
    """
    if "class Script" not in python_src and "class ስክሪፕት" not in python_src:
        return AmharicError("missing_script_class")
    return None
