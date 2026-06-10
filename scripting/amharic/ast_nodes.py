"""
ast_nodes.py
AST node dataclasses for the Amharic scripting language.
One node per grammar construct — mirrors the grammar.lark tree.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Optional


# ── Base ────────────────────────────────────────────────────────────────────

@dataclass
class ASTNode:
    line: int = 0


# ── Module ──────────────────────────────────────────────────────────────────

@dataclass
class Module(ASTNode):
    body: List[ASTNode] = field(default_factory=list)


# ── Statements ───────────────────────────────────────────────────────────────

@dataclass
class ClassDef(ASTNode):
    name:    str
    bases:   List[ASTNode]
    body:    List[ASTNode]


@dataclass
class FuncDef(ASTNode):
    name:    str
    params:  List["Param"]
    body:    List[ASTNode]


@dataclass
class Param(ASTNode):
    name:    str
    default: Optional[ASTNode] = None


@dataclass
class IfStmt(ASTNode):
    test:     ASTNode
    body:     List[ASTNode]
    elifs:    List[tuple]        # [(test, body), ...]
    orelse:   List[ASTNode]


@dataclass
class WhileStmt(ASTNode):
    test:  ASTNode
    body:  List[ASTNode]


@dataclass
class ForStmt(ASTNode):
    target: str
    iter:   ASTNode
    body:   List[ASTNode]


@dataclass
class ReturnStmt(ASTNode):
    value: Optional[ASTNode] = None


@dataclass
class BreakStmt(ASTNode):
    pass


@dataclass
class ContinueStmt(ASTNode):
    pass


@dataclass
class PassStmt(ASTNode):
    pass


@dataclass
class RaiseStmt(ASTNode):
    exc: Optional[ASTNode] = None


@dataclass
class GlobalStmt(ASTNode):
    names: List[str] = field(default_factory=list)


@dataclass
class TryStmt(ASTNode):
    body:     List[ASTNode]
    handlers: List["ExceptHandler"]
    finally_: List[ASTNode]


@dataclass
class ExceptHandler(ASTNode):
    exc_type: Optional[ASTNode]
    name:     Optional[str]
    body:     List[ASTNode]


@dataclass
class ImportStmt(ASTNode):
    module: str
    alias:  Optional[str] = None


@dataclass
class FromImportStmt(ASTNode):
    module: str
    name:   str
    alias:  Optional[str] = None


@dataclass
class AssignStmt(ASTNode):
    target: ASTNode
    value:  ASTNode


@dataclass
class AugAssignStmt(ASTNode):
    target: ASTNode
    op:     str
    value:  ASTNode


@dataclass
class ExprStmt(ASTNode):
    expr: ASTNode


# ── Expressions ──────────────────────────────────────────────────────────────

@dataclass
class BinOp(ASTNode):
    left:  ASTNode
    op:    str
    right: ASTNode


@dataclass
class UnaryOp(ASTNode):
    op:    str
    operand: ASTNode


@dataclass
class BoolOp(ASTNode):
    op:     str           # "and" / "or"
    values: List[ASTNode]


@dataclass
class Compare(ASTNode):
    left:  ASTNode
    ops:   List[str]
    comps: List[ASTNode]


@dataclass
class Call(ASTNode):
    func: ASTNode
    args: List[ASTNode]


@dataclass
class Subscript(ASTNode):
    value: ASTNode
    index: ASTNode


@dataclass
class Attribute(ASTNode):
    value: ASTNode
    attr:  str


@dataclass
class Name(ASTNode):
    id: str


@dataclass
class Num(ASTNode):
    value: Any


@dataclass
class Str(ASTNode):
    value: str


@dataclass
class BoolLiteral(ASTNode):
    value: bool


@dataclass
class NoneLiteral(ASTNode):
    pass


@dataclass
class ListExpr(ASTNode):
    elts: List[ASTNode]


@dataclass
class DictExpr(ASTNode):
    keys:   List[ASTNode]
    values: List[ASTNode]


@dataclass
class PrintCall(ASTNode):
    args: List[ASTNode]
