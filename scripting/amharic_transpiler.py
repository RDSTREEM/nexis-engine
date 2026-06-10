"""
amharic_transpiler.py
Full Amharic scripting — EVERYTHING is in Amharic.
This includes: self → ራስ, entity → ነፍስ, on_start → ሲጀምር, etc.
Also handles engine API remapping: Input → ግቤት, Time → ጊዜ, etc.
"""

from __future__ import annotations
import re

# ── Core language keywords ─────────────────────────────────────────────────
_KEYWORDS = [
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
    ("ያለዚያ", "elif"),  # alias
    ("ከ", "from"),
]

# ── self / entity / lifecycle method names ────────────────────────────────
_IDENTIFIER_MAP = {
    # self
    "ራስ": "self",
    # lifecycle
    "ሲጀምር": "on_start",
    "ሲዘምን": "on_update",
    "ሲቆም": "on_stop",
    "ሲገቡ": "on_input",
    "ሲጋጩ": "on_collision_enter",
    "ሲለያዩ": "on_collision_exit",
    # entity access
    "ነፍስ": "entity",
    # transform
    "ቦታ": "transform",
    "ቦታ_ቁ": "position",
    "ሽክርክሪ": "rotation",
    "ልኬት": "scale",
    # engine APIs (class names — always capitalized in Python)
    "ግቤት": "Input",
    "ጊዜ": "Time",
    "ክስተቶች": "Events",
    "ትዕይንቶች": "SceneManager",
    "ቅድመ_ቅርጾች": "Prefabs",
    "ዕቃዎች": "Assets",
    # Input methods
    "ቁልፍ_ተጫነ": "get_key",
    "ቁልፍ_ወረደ": "get_key_down",
    "ቁልፍ_ተለቀቀ": "get_key_up",
    "አጥ_ቁልፍ": "get_axis",
    "አይጥ_ቦታ": "get_mouse_position",
    "አይጥ_ጠቅ": "get_mouse_button",
    "ሸብልሎ": "get_scroll",
    # Time fields
    "ዴልታ_ጊዜ": "delta_time",
    "ጠቅላላ_ጊዜ": "elapsed",
    "ፍሬም_ቁጥር": "frame_count",
    "ፍሬም_ፍጥነት": "fps",
    # Events
    "ምልክት_ላክ": "emit",
    "ምልክት_ስማ": "on",
    "ምልክት_ዘጋ": "off",
    # Audio
    "ተጫወት": "play",
    "አቁም_ድምፅ": "stop",
    "አቁም_ሁሉ": "pause",
    # Physics
    "ፍጥነት": "velocity",
    "ኃይል_ጨምር": "apply_force",
    "ምት_ጨምር": "apply_impulse",
    "መሬት_ላይ": "grounded",
    # Math
    "ፍጹም": "abs",
    "ካርስ": "sqrt",
    "ሳይን": "sin",
    "ኮሳይን": "cos",
    "ታንጀንት": "tan",
    "ጣሪያ": "max",
    "ወለል": "min",
    "ርዝማኔ": "len",
    "ክልል": "range",
    # Component getters (common pattern)
    "ክፍል_አምጣ": "get_component",
    "ክፍል_ጨምር": "add_component",
    "ክፍል_አለ": "has_component",
    # Scene
    "ትዕይንት_ጫን": "load",
    "ትዕይንት_ፍጠር": "create_entity",
    "ነፍስ_አግኝ": "get_entity",
    "ነፍስ_ጨምር": "add_entity",
    # common attributes
    "ስም": "name",
    "ነቅቷል": "enabled",
    "መለያ": "tags",
    "ልጆች": "children",
    "ወላጅ": "parent",
}

# ── Script class name ─────────────────────────────────────────────────────
_CLASS_NAME_MAP = {
    "ስክሪፕት": "Script",
}


def transpile(source: str) -> str:
    """Transpile full Amharic source to valid Python."""
    result = source

    # 1. Replace language keywords (word-boundary aware)
    for amh, py in _KEYWORDS:
        result = re.sub(r"(?<!\w)" + re.escape(amh) + r"(?!\w)", py, result)

    # 2. Replace identifiers (also word-boundary aware)
    for amh, py in sorted(_IDENTIFIER_MAP.items(), key=lambda x: -len(x[0])):
        result = re.sub(r"(?<!\w)" + re.escape(amh) + r"(?!\w)", py, result)

    # 3. Replace script class name
    for amh, py in _CLASS_NAME_MAP.items():
        result = re.sub(r"(?<!\w)" + re.escape(amh) + r"(?!\w)", py, result)

    return result


def get_amharic_keywords() -> list:
    """Return all Amharic keyword tokens for syntax highlighting."""
    kws = [k for k, _ in _KEYWORDS]
    kws += list(_IDENTIFIER_MAP.keys())
    kws += list(_CLASS_NAME_MAP.keys())
    return kws
