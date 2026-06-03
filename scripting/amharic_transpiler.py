"""
amharic_transpiler.py
Transpiles a minimal Amharic scripting language to Python using Lark.

Amharic keywords:
    ክፍል        → class
    ተግባር       → def
    ካርታ        → return
    ከሆነ        → if
    ካልሆነ      → else
    እስካለ      → while
    ለእያንዳንዱ   → for
    ውስጥ        → in
    እውነት       → True
    ሐሰት        → False
    ምንም        → None
    አትም        → print
    እና          → and
    ወይም        → or
    አይደለም     → not
    አቁም        → break
    ቀጥል        → continue
    አስገባ       → import
    ከ           → from
    እንደ        → as
    ሞክር        → try
    ያዝ         → except
    በመጨረሻ    → finally
    ከፍ         → raise
    ከጋራ        → global
    ምንም_ሳይሆን → pass

Usage:
    from scripting.amharic_transpiler import transpile
    python_code = transpile(amharic_source)
"""

from __future__ import annotations

import re

# Simple keyword substitution — no full parse tree needed for v1.
# Ordered longest-first to avoid partial matches.
_KEYWORDS: list[tuple[str, str]] = [
    ("ለእያንዳንዱ", "for"),
    ("ካልሆነ", "else"),
    ("ምንም_ሳይሆን", "pass"),
    ("እስካለ", "while"),
    ("ወይም", "or"),
    ("አይደለም", "not"),
    ("አቁም", "break"),
    ("ቀጥል", "continue"),
    ("አስገባ", "import"),
    ("እንደ", "as"),
    ("ሞክር", "try"),
    ("ያዝ", "except"),
    ("በመጨረሻ", "finally"),
    ("ከፍ", "raise"),
    ("ከጋራ", "global"),
    ("ከሆነ", "if"),
    ("ካርታ", "return"),
    ("ተግባር", "def"),
    ("ክፍል", "class"),
    ("ውስጥ", "in"),
    ("እውነት", "True"),
    ("ሐሰት", "False"),
    ("ምንም", "None"),
    ("አትም", "print"),
    ("እና", "and"),
    ("ከ", "from"),
]

_OPERATORS: list[tuple[str, str]] = [
    ("==", "=="),  # pass through
    ("!=", "!="),
    (">=", ">="),
    ("<=", "<="),
    ("ይሰወር", "=="),  # custom equality keyword
    ("አይሰወርም", "!="),
]


def transpile(source: str) -> str:
    """Transpile Amharic source to valid Python."""
    result = source

    # replace keywords (word-boundary aware)
    for amh, py in _KEYWORDS:
        result = re.sub(
            r"(?<![^\s(,=+\-*/<>!&|])" + re.escape(amh) + r"(?![^\s):,=+\-*/<>!&|])",
            py,
            result,
        )

    # replace any remaining full-word matches
    for amh, py in _KEYWORDS:
        result = result.replace(amh, py)

    return result


# ------------------------------------------------------------------
# Quick test
# ------------------------------------------------------------------

if __name__ == "__main__":
    sample = """
ክፍል Script:
    ተግባር on_start(self, entity):
        አትም("ጀምሯል!")
        self.speed = 5.0

    ተግባር on_update(self, entity, dt):
        ከሆነ self.speed > 0:
            entity.transform.position[0] += self.speed * dt
        ካርታ እውነት
"""
    print(transpile(sample))
