"""
parser.py
Converts a Lark parse tree into NEXIS AST nodes.
Falls back to regex-transpiler if Lark is not installed.
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Any

try:
    from lark import Lark, Token, Tree
    _LARK_OK = True
except ImportError:
    _LARK_OK = False

from scripting.amharic.ast_nodes import *

_GRAMMAR_PATH = Path(__file__).parent / "grammar.lark"


def _get_parser():
    if not _LARK_OK:
        return None
    if not _GRAMMAR_PATH.exists():
        return None
    try:
        return Lark(
            _GRAMMAR_PATH.read_text(encoding="utf-8"),
            parser="lalr",
            propagate_positions=True,
        )
    except Exception as e:
        print(f"[Amharic] Grammar load failed: {e}")
        return None


_PARSER = None   # lazy-init


def get_parser():
    global _PARSER
    if _PARSER is None:
        _PARSER = _get_parser()
    return _PARSER


# ── Tree → AST ───────────────────────────────────────────────────────────────

def _line(tree_or_tok) -> int:
    try:
        if hasattr(tree_or_tok, "meta"):
            return tree_or_tok.meta.line or 0
        if hasattr(tree_or_tok, "line"):
            return tree_or_tok.line or 0
    except Exception:
        pass
    return 0


class _Builder:
    """Walks the Lark Tree and produces AST nodes."""

    def build(self, tree) -> Module:
        stmts = [self._stmt(child) for child in tree.children
                 if not (isinstance(child, Token) and child.type == "NEWLINE")]
        stmts = [s for s in stmts if s is not None]
        return Module(body=stmts)

    # ── Dispatcher ───────────────────────────────────────────────────────────

    def _stmt(self, node) -> Optional[ASTNode]:
        if isinstance(node, Token):
            return None
        handlers = {
            "class_def":       self._class_def,
            "func_def":        self._func_def,
            "if_stmt":         self._if_stmt,
            "while_stmt":      self._while_stmt,
            "for_stmt":        self._for_stmt,
            "return_stmt":     self._return_stmt,
            "break_stmt":      lambda n: BreakStmt(line=_line(n)),
            "continue_stmt":   lambda n: ContinueStmt(line=_line(n)),
            "pass_stmt":       lambda n: PassStmt(line=_line(n)),
            "raise_stmt":      self._raise_stmt,
            "global_stmt":     self._global_stmt,
            "try_stmt":        self._try_stmt,
            "import_stmt":     self._import_stmt,
            "from_import_stmt":self._from_import_stmt,
            "assign_stmt":     self._assign_stmt,
            "aug_assign_stmt": self._aug_assign_stmt,
            "expr_stmt":       self._expr_stmt,
        }
        fn = handlers.get(node.data)
        if fn:
            return fn(node)
        return None

    def _stmts(self, suite_node) -> List[ASTNode]:
        result = []
        for child in suite_node.children:
            if isinstance(child, Token):
                continue
            if child.data == "suite":
                result.extend(self._stmts(child))
            else:
                s = self._stmt(child)
                if s:
                    result.append(s)
        return result

    # ── Statement builders ────────────────────────────────────────────────────

    def _class_def(self, n) -> ClassDef:
        name  = str(n.children[0])
        bases = []
        body  = []
        for ch in n.children[1:]:
            if isinstance(ch, Token):
                continue
            if ch.data == "arglist":
                bases = [self._expr(e) for e in ch.children if not isinstance(e, Token)]
            elif ch.data == "suite":
                body = self._stmts(ch)
        return ClassDef(name=name, bases=bases, body=body, line=_line(n))

    def _func_def(self, n) -> FuncDef:
        name   = str(n.children[0])
        params = []
        body   = []
        for ch in n.children[1:]:
            if isinstance(ch, Token):
                continue
            if ch.data == "params":
                params = [Param(name=str(p.children[0]),
                                default=self._expr(p.children[1]) if len(p.children)>1 else None)
                          for p in ch.children if not isinstance(p, Token)]
            elif ch.data == "suite":
                body = self._stmts(ch)
        return FuncDef(name=name, params=params, body=body, line=_line(n))

    def _if_stmt(self, n) -> IfStmt:
        children = [c for c in n.children if not isinstance(c, Token)]
        test  = self._expr(children[0])
        body  = self._stmts(children[1])
        elifs = []
        orelse = []
        i = 2
        while i < len(children):
            ch = n.children[i*2] if False else None   # placeholder
            break
        # Simplified: collect alternating test/suite pairs for elif, last suite = else
        raw = list(n.children)
        # tokens: IF, expr, ":", suite, (ELIF expr ":" suite)*, (ELSE ":" suite)?
        idx = 0
        # skip IF token
        idx += 1
        test_node  = self._expr(raw[idx]); idx += 1
        idx += 1  # ":"
        body_suite = self._stmts(raw[idx]); idx += 1
        elifs_ = []
        orelse_ = []
        while idx < len(raw):
            tok = raw[idx]
            if isinstance(tok, Token) and tok.type == "ELIF":
                idx += 1
                et = self._expr(raw[idx]); idx += 1
                idx += 1  # ":"
                es = self._stmts(raw[idx]); idx += 1
                elifs_.append((et, es))
            elif isinstance(tok, Token) and tok.type == "ELSE":
                idx += 1
                idx += 1  # ":"
                orelse_ = self._stmts(raw[idx]); idx += 1
            else:
                break
        return IfStmt(test=test_node, body=body_suite, elifs=elifs_, orelse=orelse_, line=_line(n))

    def _while_stmt(self, n) -> WhileStmt:
        raw = list(n.children)
        test = self._expr(raw[1])
        body = self._stmts(raw[3])
        return WhileStmt(test=test, body=body, line=_line(n))

    def _for_stmt(self, n) -> ForStmt:
        raw  = list(n.children)
        target = str(raw[1])
        iter_  = self._expr(raw[3])
        body   = self._stmts(raw[5])
        return ForStmt(target=target, iter=iter_, body=body, line=_line(n))

    def _return_stmt(self, n) -> ReturnStmt:
        kids = [c for c in n.children if not isinstance(c, Token)]
        val  = self._expr(kids[0]) if kids else None
        return ReturnStmt(value=val, line=_line(n))

    def _raise_stmt(self, n) -> RaiseStmt:
        kids = [c for c in n.children if not isinstance(c, Token)]
        exc  = self._expr(kids[0]) if kids else None
        return RaiseStmt(exc=exc, line=_line(n))

    def _global_stmt(self, n) -> GlobalStmt:
        names = [str(c) for c in n.children if isinstance(c, Token) and c.type == "NAME"]
        return GlobalStmt(names=names, line=_line(n))

    def _try_stmt(self, n) -> TryStmt:
        # try ":" suite except_clause+ [finally ":" suite]
        raw = list(n.children)
        body     = self._stmts(raw[2])
        handlers = []
        finally_ = []
        i = 3
        while i < len(raw):
            ch = raw[i]
            if isinstance(ch, Tree) and ch.data == "except_clause":
                cr = list(ch.children)
                exc_type = self._expr(cr[1]) if len(cr) > 1 and not isinstance(cr[1], Token) else None
                alias    = str(cr[3]) if len(cr) > 3 else None
                bsuite   = self._stmts(cr[-1])
                handlers.append(ExceptHandler(exc_type=exc_type, name=alias, body=bsuite))
            elif isinstance(ch, Token) and ch.type == "FINALLY":
                finally_ = self._stmts(raw[i+2])
            i += 1
        return TryStmt(body=body, handlers=handlers, finally_=finally_, line=_line(n))

    def _import_stmt(self, n) -> ImportStmt:
        raw   = list(n.children)
        mod   = ".".join(str(t) for t in raw[1].children if isinstance(t, Token))
        alias = str(raw[3]) if len(raw) > 3 else None
        return ImportStmt(module=mod, alias=alias, line=_line(n))

    def _from_import_stmt(self, n) -> FromImportStmt:
        raw   = list(n.children)
        mod   = ".".join(str(t) for t in raw[1].children if isinstance(t, Token))
        name  = str(raw[3])
        alias = str(raw[5]) if len(raw) > 5 else None
        return FromImportStmt(module=mod, name=name, alias=alias, line=_line(n))

    def _assign_stmt(self, n) -> AssignStmt:
        target = self._expr(n.children[0])
        value  = self._expr(n.children[2])
        return AssignStmt(target=target, value=value, line=_line(n))

    def _aug_assign_stmt(self, n) -> AugAssignStmt:
        target = self._expr(n.children[0])
        op     = str(n.children[1])
        value  = self._expr(n.children[2])
        return AugAssignStmt(target=target, op=op, value=value, line=_line(n))

    def _expr_stmt(self, n) -> ExprStmt:
        return ExprStmt(expr=self._expr(n.children[0]), line=_line(n))

    # ── Expression builder ────────────────────────────────────────────────────

    def _expr(self, node) -> ASTNode:
        if isinstance(node, Token):
            t = node.type
            if t == "NAME":   return Name(id=str(node),  line=_line(node))
            if t == "NUMBER": return Num(value=_parse_num(str(node)), line=_line(node))
            if t == "STRING": return Str(value=str(node)[1:-1], line=_line(node))
            if t == "TRUE":   return BoolLiteral(value=True,  line=_line(node))
            if t == "FALSE":  return BoolLiteral(value=False, line=_line(node))
            if t == "NONE":   return NoneLiteral(line=_line(node))
            return Name(id=str(node), line=_line(node))

        data = node.data
        if data == "paren":
            return self._expr(node.children[0])
        if data == "name":
            return Name(id=str(node.children[0]), line=_line(node))
        if data == "number":
            return Num(value=_parse_num(str(node.children[0])), line=_line(node))
        if data == "string":
            s = "".join(str(c)[1:-1] for c in node.children)
            return Str(value=s, line=_line(node))
        if data == "true":    return BoolLiteral(value=True,  line=_line(node))
        if data == "false":   return BoolLiteral(value=False, line=_line(node))
        if data == "none":    return NoneLiteral(line=_line(node))
        if data == "list_expr":
            elts = [self._expr(c) for c in node.children if not isinstance(c, Token)]
            return ListExpr(elts=elts, line=_line(node))
        if data == "dict_expr":
            keys = []; vals = []
            kids = [c for c in node.children if not isinstance(c, Token)]
            for i in range(0, len(kids), 2):
                keys.append(self._expr(kids[i]))
                if i+1 < len(kids):
                    vals.append(self._expr(kids[i+1]))
            return DictExpr(keys=keys, values=vals, line=_line(node))
        if data == "print_call":
            args = [self._expr(c) for c in node.children if not isinstance(c, Token)]
            return PrintCall(args=args, line=_line(node))
        if data == "call":
            # trailer: func already resolved by atom_expr
            return None   # handled in atom_expr chain below
        if data in ("or_expr", "and_expr"):
            kids = [c for c in node.children if not isinstance(c, Token)]
            op   = "or" if data == "or_expr" else "and"
            vals = [self._expr(k) for k in kids]
            return BoolOp(op=op, values=vals, line=_line(node))
        if data == "not_expr":
            return UnaryOp(op="not", operand=self._expr(node.children[1]), line=_line(node))
        if data == "comparison":
            kids = list(node.children)
            left = self._expr(kids[0])
            ops  = [str(kids[i]) for i in range(1, len(kids), 2)]
            cps  = [self._expr(kids[i]) for i in range(2, len(kids), 2)]
            return Compare(left=left, ops=ops, comps=cps, line=_line(node))
        if data in ("arith", "term"):
            kids = list(node.children)
            result = self._expr(kids[0])
            i = 1
            while i < len(kids) - 1:
                op    = str(kids[i])
                right = self._expr(kids[i+1])
                result = BinOp(left=result, op=op, right=right, line=_line(node))
                i += 2
            return result
        if data == "factor":
            if len(node.children) == 2:
                return UnaryOp(op=str(node.children[0]),
                               operand=self._expr(node.children[1]), line=_line(node))
            return self._expr(node.children[0])
        if data == "power":
            base = self._expr(node.children[0])
            if len(node.children) > 1:
                exp = self._expr(node.children[2])
                return BinOp(left=base, op="**", right=exp, line=_line(node))
            return base
        if data == "atom_expr":
            result = self._expr(node.children[0])
            for trailer in node.children[1:]:
                if isinstance(trailer, Token):
                    continue
                if trailer.data == "call":
                    args = [self._expr(c) for c in trailer.children
                            if not isinstance(c, Token)]
                    result = Call(func=result, args=args, line=_line(trailer))
                elif trailer.data == "subscript":
                    idx = self._expr(trailer.children[0])
                    result = Subscript(value=result, index=idx, line=_line(trailer))
                elif trailer.data == "attr":
                    attr = str(trailer.children[0])
                    result = Attribute(value=result, attr=attr, line=_line(trailer))
            return result
        if data == "lvalue":
            return self._expr(node.children[0])
        # fallback
        return Name(id=str(node), line=_line(node))


def _parse_num(s: str) -> Any:
    try:
        return int(s)
    except ValueError:
        return float(s)


# ── Public API ────────────────────────────────────────────────────────────────

def parse(source: str) -> Module:
    """Parse Amharic source → Module AST. Raises SyntaxError on failure."""
    p = get_parser()
    if p is None:
        raise ImportError("Lark not available — install with: pip install lark")
    try:
        tree = p.parse(source)
    except Exception as e:
        raise SyntaxError(f"Amharic parse error: {e}") from e
    return _Builder().build(tree)
