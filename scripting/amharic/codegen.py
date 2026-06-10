"""
codegen.py
AST → Python source code generator for the Amharic scripting language.
Produces clean, properly-indented Python that the existing script_runner
sandbox can execute directly.
"""
from __future__ import annotations
from typing import List

from scripting.amharic.ast_nodes import *


class CodeGen:
    def __init__(self, indent_size: int = 4):
        self._indent_size = indent_size
        self._level       = 0
        self._lines: List[str] = []

    # ── Public ───────────────────────────────────────────────────────────────

    def generate(self, module: Module) -> str:
        self._lines = []
        self._level = 0
        for stmt in module.body:
            self._stmt(stmt)
        return "\n".join(self._lines)

    # ── Indent helpers ────────────────────────────────────────────────────────

    def _indent(self) -> str:
        return " " * (self._indent_size * self._level)

    def _emit(self, line: str) -> None:
        self._lines.append(self._indent() + line)

    def _emit_raw(self, line: str) -> None:
        self._lines.append(line)

    # ── Statements ────────────────────────────────────────────────────────────

    def _stmt(self, node: ASTNode) -> None:
        dispatch = {
            Module:          self._module,
            ClassDef:        self._class_def,
            FuncDef:         self._func_def,
            IfStmt:          self._if_stmt,
            WhileStmt:       self._while_stmt,
            ForStmt:         self._for_stmt,
            ReturnStmt:      self._return_stmt,
            BreakStmt:       lambda n: self._emit("break"),
            ContinueStmt:    lambda n: self._emit("continue"),
            PassStmt:        lambda n: self._emit("pass"),
            RaiseStmt:       self._raise_stmt,
            GlobalStmt:      self._global_stmt,
            TryStmt:         self._try_stmt,
            ImportStmt:      self._import_stmt,
            FromImportStmt:  self._from_import_stmt,
            AssignStmt:      self._assign_stmt,
            AugAssignStmt:   self._aug_assign_stmt,
            ExprStmt:        self._expr_stmt,
        }
        fn = dispatch.get(type(node))
        if fn:
            fn(node)

    def _suite(self, body: List[ASTNode]) -> None:
        self._level += 1
        if not body:
            self._emit("pass")
        else:
            for stmt in body:
                self._stmt(stmt)
        self._level -= 1

    def _module(self, n: Module) -> None:
        for stmt in n.body:
            self._stmt(stmt)

    def _class_def(self, n: ClassDef) -> None:
        bases = ", ".join(self._expr(b) for b in n.bases) if n.bases else ""
        header = f"class {n.name}({bases}):" if bases else f"class {n.name}:"
        self._emit(header)
        self._suite(n.body)

    def _func_def(self, n: FuncDef) -> None:
        params = []
        for p in n.params:
            if p.default:
                params.append(f"{p.name}={self._expr(p.default)}")
            else:
                params.append(p.name)
        self._emit(f"def {n.name}({', '.join(params)}):")
        self._suite(n.body)

    def _if_stmt(self, n: IfStmt) -> None:
        self._emit(f"if {self._expr(n.test)}:")
        self._suite(n.body)
        for elif_test, elif_body in n.elifs:
            self._emit(f"elif {self._expr(elif_test)}:")
            self._suite(elif_body)
        if n.orelse:
            self._emit("else:")
            self._suite(n.orelse)

    def _while_stmt(self, n: WhileStmt) -> None:
        self._emit(f"while {self._expr(n.test)}:")
        self._suite(n.body)

    def _for_stmt(self, n: ForStmt) -> None:
        self._emit(f"for {n.target} in {self._expr(n.iter)}:")
        self._suite(n.body)

    def _return_stmt(self, n: ReturnStmt) -> None:
        if n.value:
            self._emit(f"return {self._expr(n.value)}")
        else:
            self._emit("return")

    def _raise_stmt(self, n: RaiseStmt) -> None:
        if n.exc:
            self._emit(f"raise {self._expr(n.exc)}")
        else:
            self._emit("raise")

    def _global_stmt(self, n: GlobalStmt) -> None:
        self._emit(f"global {', '.join(n.names)}")

    def _try_stmt(self, n: TryStmt) -> None:
        self._emit("try:")
        self._suite(n.body)
        for h in n.handlers:
            if h.exc_type and h.name:
                self._emit(f"except {self._expr(h.exc_type)} as {h.name}:")
            elif h.exc_type:
                self._emit(f"except {self._expr(h.exc_type)}:")
            else:
                self._emit("except:")
            self._suite(h.body)
        if n.finally_:
            self._emit("finally:")
            self._suite(n.finally_)

    def _import_stmt(self, n: ImportStmt) -> None:
        if n.alias:
            self._emit(f"import {n.module} as {n.alias}")
        else:
            self._emit(f"import {n.module}")

    def _from_import_stmt(self, n: FromImportStmt) -> None:
        if n.alias:
            self._emit(f"from {n.module} import {n.name} as {n.alias}")
        else:
            self._emit(f"from {n.module} import {n.name}")

    def _assign_stmt(self, n: AssignStmt) -> None:
        self._emit(f"{self._expr(n.target)} = {self._expr(n.value)}")

    def _aug_assign_stmt(self, n: AugAssignStmt) -> None:
        self._emit(f"{self._expr(n.target)} {n.op} {self._expr(n.value)}")

    def _expr_stmt(self, n: ExprStmt) -> None:
        self._emit(self._expr(n.expr))

    # ── Expressions ───────────────────────────────────────────────────────────

    def _expr(self, node: ASTNode) -> str:
        dispatch = {
            Name:         lambda n: n.id,
            Num:          lambda n: repr(n.value),
            Str:          lambda n: repr(n.value),
            BoolLiteral:  lambda n: "True" if n.value else "False",
            NoneLiteral:  lambda n: "None",
            BinOp:        self._binop,
            UnaryOp:      self._unaryop,
            BoolOp:       self._boolop,
            Compare:      self._compare,
            Call:         self._call,
            Subscript:    self._subscript,
            Attribute:    self._attribute,
            ListExpr:     self._list_expr,
            DictExpr:     self._dict_expr,
            PrintCall:    self._print_call,
            AssignStmt:   lambda n: f"{self._expr(n.target)} = {self._expr(n.value)}",
        }
        fn = dispatch.get(type(node))
        if fn:
            return fn(node)
        return repr(node)

    def _binop(self, n: BinOp) -> str:
        return f"({self._expr(n.left)} {n.op} {self._expr(n.right)})"

    def _unaryop(self, n: UnaryOp) -> str:
        if n.op == "not":
            return f"(not {self._expr(n.operand)})"
        return f"({n.op}{self._expr(n.operand)})"

    def _boolop(self, n: BoolOp) -> str:
        sep = f" {n.op} "
        return "(" + sep.join(self._expr(v) for v in n.values) + ")"

    def _compare(self, n: Compare) -> str:
        parts = [self._expr(n.left)]
        for op, comp in zip(n.ops, n.comps):
            parts.append(op)
            parts.append(self._expr(comp))
        return "(" + " ".join(parts) + ")"

    def _call(self, n: Call) -> str:
        args = ", ".join(self._expr(a) for a in n.args)
        return f"{self._expr(n.func)}({args})"

    def _subscript(self, n: Subscript) -> str:
        return f"{self._expr(n.value)}[{self._expr(n.index)}]"

    def _attribute(self, n: Attribute) -> str:
        return f"{self._expr(n.value)}.{n.attr}"

    def _list_expr(self, n: ListExpr) -> str:
        return "[" + ", ".join(self._expr(e) for e in n.elts) + "]"

    def _dict_expr(self, n: DictExpr) -> str:
        pairs = ", ".join(
            f"{self._expr(k)}: {self._expr(v)}"
            for k, v in zip(n.keys, n.values)
        )
        return "{" + pairs + "}"

    def _print_call(self, n: PrintCall) -> str:
        args = ", ".join(self._expr(a) for a in n.args)
        return f"print({args})"


def generate(module: Module) -> str:
    """Convert a Module AST to a Python source string."""
    return CodeGen().generate(module)
