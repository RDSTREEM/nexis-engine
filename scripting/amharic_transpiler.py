"""
amharic_transpiler.py
Updated entry point that uses the full Lark-based pipeline.
Replaces the old regex keyword-substitution stub.

Pipeline:
  .amh source
    → parser.parse()        (Lark LALR → AST)
    → codegen.generate()    (AST → Python source)
    → error_reporter        (friendly bilingual errors)
    → returned to script_runner for sandbox execution
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional

# Try the full pipeline first; fall back to legacy regex if Lark unavailable
try:
    from scripting.amharic.parser       import parse
    from scripting.amharic.codegen      import generate
    from scripting.amharic.error_reporter import (
        from_lark_exception, from_python_exception,
        validate_script_class, AmharicError,
    )
    _FULL_PIPELINE = True
except ImportError:
    _FULL_PIPELINE = False

# ── Stdlib path ──────────────────────────────────────────────────────────────

_STDLIB_PATH = Path(__file__).parent / "amharic" / "stdlib.amh"


def _load_stdlib() -> str:
    if _STDLIB_PATH.exists():
        return _STDLIB_PATH.read_text(encoding="utf-8")
    return ""


# ── Public API ───────────────────────────────────────────────────────────────

class TranspileResult:
    def __init__(self, python_src: str = "", error: str = "",
                 success: bool = False):
        self.python_src = python_src
        self.error      = error
        self.success    = success

    def __bool__(self) -> bool:
        return self.success


def transpile(amharic_source: str, filename: str = "<script>") -> TranspileResult:
    """
    Transpile Amharic source to Python.
    Returns TranspileResult with .python_src and .error.
    """
    if _FULL_PIPELINE:
        return _transpile_full(amharic_source, filename)
    else:
        return _transpile_legacy(amharic_source, filename)


def transpile_file(path: str | Path) -> TranspileResult:
    """Load a .amh file and transpile it."""
    p = Path(path)
    if not p.exists():
        return TranspileResult(error=f"File not found: {p}", success=False)
    src = p.read_text(encoding="utf-8")
    return transpile(src, filename=str(p))


# ── Full pipeline ────────────────────────────────────────────────────────────

def _transpile_full(source: str, filename: str) -> TranspileResult:
    # Prepend stdlib
    stdlib_src = _load_stdlib()
    full_src   = (stdlib_src + "\n\n" + source).strip()

    try:
        ast   = parse(full_src)
        py    = generate(ast)
    except SyntaxError as e:
        return TranspileResult(error=str(e), success=False)
    except Exception as e:
        try:
            err = from_lark_exception(e)
            return TranspileResult(error=err.full_message(), success=False)
        except Exception:
            return TranspileResult(error=f"Transpile error: {e}", success=False)

    # Validate Script class present
    class_err = validate_script_class(py)
    if class_err:
        return TranspileResult(error=class_err.full_message(), success=False)

    # Rename Amharic class name ስክሪፕት → Script for the sandbox
    py = py.replace("class ስክሪፕት", "class Script")

    return TranspileResult(python_src=py, success=True)


# ── Legacy regex fallback (kept for when Lark is not installed) ──────────────

_KEYWORD_MAP = {
    # classes / functions
    "ክፍል":        "class",
    "ተግባር":       "def",
    "ካርታ":        "return",
    # control flow
    "ከሆነ":        "if",
    "ያለዚያ":       "elif",
    "ካልሆነ":       "else",
    "እስካለ":       "while",
    "ለእያንዳንዱ":   "for",
    "ውስጥ":        "in",
    "አቁም":        "break",
    "ቀጥል":        "continue",
    "ምንም_ሳይሆን":   "pass",
    # logical
    "እና":         "and",
    "ወይም":        "or",
    "አይደለም":     "not",
    # literals
    "እውነት":       "True",
    "ሐሰት":        "False",
    "ምንም":        "None",
    # builtins
    "አትም":        "print",
    # exceptions
    "ሞክር":        "try",
    "ያዝ":         "except",
    "በመጨረሻ":     "finally",
    "ከ":          "from",
    "አስገባ":       "import",
    "እንደ":        "as",
    "ከፍ":         "raise",
    "ከጋራ":        "global",
    # script class
    "ስክሪፕት":      "Script",
}


def _transpile_legacy(source: str, filename: str) -> TranspileResult:
    """
    Simple regex-based keyword substitution — used when Lark is not available.
    Not a full parser; only handles keyword replacement.
    """
    import re
    result = source
    for amh, eng in sorted(_KEYWORD_MAP.items(), key=lambda x: -len(x[0])):
        result = re.sub(rf'\b{re.escape(amh)}\b', eng, result)

    if "class Script" not in result:
        return TranspileResult(
            error=(
                "ስክሪፕቱ 'ስክሪፕት' ክፍል (class Script) መያዝ አለበት\n"
                "Script must define a 'Script' class (ስክሪፕት)"
            ),
            success=False,
        )
    return TranspileResult(python_src=result, success=True)


# ── Convenience: get keyword map for editor syntax highlighting ───────────────

def get_amharic_keywords() -> list:
    return list(_KEYWORD_MAP.keys())
