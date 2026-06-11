"""
amharic_transpiler.py
Full Amharic scripting — ALL identifiers, API names, and lifecycle methods
are in Amharic. English keywords also accepted for compatibility.

Key Amharic → Python mappings:
  ራስ           → self
  ነፍስ          → entity
  ሲጀምር         → on_start
  ሲዘምን         → on_update
  ሲቆም          → on_stop
  ሲገቡ          → on_input
  ሲጋጩ         → on_collision_enter
  ሲለያዩ        → on_collision_exit
  ቦታ           → transform
  ቦታ_ቁ        → position
  ሽክርክሪ       → rotation
  ልኬት         → scale
  ግቤት          → Input
  ጊዜ           → Time
  ክስተቶች       → Events
  ትዕይንቶች      → SceneManager
"""

from __future__ import annotations
import re

# ── Language keywords (longest first to avoid partial substitution) ──────────
_KEYWORDS: list[tuple[str, str]] = [
    ("ለእያንዳንዱ", "for"),
    ("ምንም_ሳይሆን", "pass"),
    ("ያለዚያም", "elif"),
    ("ካልሆነ", "else"),
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
    ("ያለዚያ", "elif"),
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

# ── Identifier / API mapping ──────────────────────────────────────────────────
_IDENTIFIERS: list[tuple[str, str]] = [
    # self
    ("ራስ", "self"),
    # entity lifecycle
    ("ሲጀምር", "on_start"),
    ("ሲዘምን", "on_update"),
    ("ሲቆም", "on_stop"),
    ("ሲገቡ", "on_input"),
    ("ሲጋጩ", "on_collision_enter"),
    ("ሲለያዩ", "on_collision_exit"),
    # entity / scene references
    ("ነፍስ", "entity"),
    ("ትዕይንት", "scene"),
    # transform
    ("ቦታ", "transform"),
    ("ቦታ_ቁ", "position"),
    ("ሽክርክሪ", "rotation"),
    ("ልኬት", "scale"),
    # engine singletons
    ("ግቤት", "Input"),
    ("ጊዜ", "Time"),
    ("ክስተቶች", "Events"),
    ("ትዕይንቶች", "SceneManager"),
    ("ቅድመ_ቅርጾች", "Prefabs"),
    ("ዕቃዎች", "Assets"),
    # Input methods
    ("ቁልፍ_ተጫነ", "get_key"),
    ("ቁልፍ_ወረደ", "get_key_down"),
    ("ቁልፍ_ተለቀቀ", "get_key_up"),
    ("አጥ_ቁልፍ", "get_axis"),
    ("አይጥ_ቦታ", "get_mouse_position"),
    ("አይጥ_ጠቅ", "get_mouse_button"),
    ("ሸብልሎ", "get_scroll"),
    # Time fields
    ("ዴልታ_ጊዜ", "delta_time"),
    ("ጠቅላላ_ጊዜ", "elapsed"),
    ("ፍሬም_ቁጥር", "frame_count"),
    ("ፍሬም_ፍጥነት", "fps"),
    # Events
    ("ምልክት_ላክ", "emit"),
    ("ምልክት_ስማ", "on"),
    ("ምልክት_ዘጋ", "off"),
    # Audio
    ("ተጫወት", "play"),
    ("አቁም_ድምፅ", "stop"),
    ("አቁም_ሁሉ", "pause"),
    # Physics / RB
    ("ፍጥነት", "velocity"),
    ("ኃይል_ጨምር", "apply_force"),
    ("ምት_ጨምር", "apply_impulse"),
    ("መሬት_ላይ", "grounded"),
    # Component helpers
    ("ክፍል_አምጣ", "get_component"),
    ("ክፍል_ጨምር", "add_component"),
    ("ክፍል_አለ", "has_component"),
    # Scene helpers
    ("ትዕይንት_ጫን", "load"),
    ("ነፍስ_ፍጠር", "create_entity"),
    ("ነፍስ_አግኝ", "get_entity"),
    ("ነፍስ_ጨምር", "add_entity"),
    # common attrs
    ("ስም", "name"),
    ("ነቅቷል", "enabled"),
    ("መለያ", "tags"),
    ("ልጆች", "children"),
    ("ወላጅ", "parent"),
    # builtins
    ("ፍጹም", "abs"),
    ("ርዝማኔ", "len"),
    ("ክልል", "range"),
    ("ዝርዝር", "list"),
    ("መዝገብ", "dict"),
    ("ቁጥር_ፍ", "float"),
    ("ቁጥር_ሙ", "int"),
    ("ፅሑፍ", "str"),
]

# ── Script class name ──────────────────────────────────────────────────────────
_CLASS_MAP: list[tuple[str, str]] = [
    ("ስክሪፕት", "Script"),
]


def transpile(source: str) -> str:
    """Transpile Amharic source to valid Python."""
    result = source

    # 1. Language keywords (word-boundary aware)
    for amh, py in _KEYWORDS:
        result = re.sub(r"(?<!\w)" + re.escape(amh) + r"(?!\w)", py, result)

    # 2. Identifiers (longest first to avoid partial matches)
    for amh, py in sorted(_IDENTIFIERS, key=lambda x: -len(x[0])):
        result = re.sub(r"(?<!\w)" + re.escape(amh) + r"(?!\w)", py, result)

    # 3. Script class name
    for amh, py in _CLASS_MAP:
        result = re.sub(r"(?<!\w)" + re.escape(amh) + r"(?!\w)", py, result)

    return result


def get_amharic_keywords() -> list:
    """Return all Amharic tokens for syntax highlighting."""
    tokens = [k for k, _ in _KEYWORDS]
    tokens += [k for k, _ in _IDENTIFIERS]
    tokens += [k for k, _ in _CLASS_MAP]
    return tokens
