"""
ast_serializer.py
-----------------
Converts the internal Python AST objects produced by analyzer/syntax.py
into a clean, JSON-serializable dictionary that matches the spec:

  Input Code → Lexer → Parser → AST (this output) → TAC Generator → Optimizer
"""

from typing import Optional
from analyzer.syntax import (
    ASTNode, Program, Block, VarDecl,
    Assignment, BinaryExpr, Literal, Identifier, ReturnStatement,
    Expression,
)


def ast_to_json(node: ASTNode) -> Optional[dict]:
    """
    Recursively convert an ASTNode into a JSON-serializable dict.
    Returns None if node is None.
    """
    if node is None:
        return None

    # ── Program ────────────────────────────────────────────────────────────
    if isinstance(node, Program):
        return {
            "type": "Program",
            "body": [ast_to_json(s) for s in node.statements if s is not None],
        }

    # ── Block ──────────────────────────────────────────────────────────────
    if isinstance(node, Block):
        return {
            "type": "Block",
            "body": [ast_to_json(s) for s in node.statements if s is not None],
        }

    # ── Variable Declaration ───────────────────────────────────────────────
    if isinstance(node, VarDecl):
        result = {
            "type": "VarDeclaration",
            "varType": node.type_name,
            "name": node.var_name,
            "line": node.line,
        }
        if getattr(node, "init_expr", None) is not None:
            # Always wrap the initializer in an explicit AssignmentExpression
            # so the tree shows: VarDecl → AssignmentExpr(=) → <expression>
            result["init"] = {
                "type": "AssignmentExpression",
                "operator": "=",
                "left": {"type": "Identifier", "name": node.var_name},
                "right": ast_to_json(node.init_expr),
            }
        return result

    # ── Assignment Expression ──────────────────────────────────────────────
    if isinstance(node, Assignment):
        return {
            "type": "AssignmentExpression",
            "operator": "=",
            "left": {"type": "Identifier", "name": node.var_name},
            "right": ast_to_json(node.expr),
            "line": node.line,
        }

    # ── Binary Expression ─────────────────────────────────────────────────
    if isinstance(node, BinaryExpr):
        return {
            "type": "BinaryExpression",
            "operator": node.op,
            "left": ast_to_json(node.left),
            "right": ast_to_json(node.right),
        }

    # ── Literal ────────────────────────────────────────────────────────────
    if isinstance(node, Literal):
        return {
            "type": "Literal",
            "value": str(node.value),
            "dataType": node.type_str,
        }

    # ── Identifier ─────────────────────────────────────────────────────────
    if isinstance(node, Identifier):
        # Detect function calls (name ends with "()")
        name = node.name
        if name.endswith("()"):
            return {
                "type": "CallExpression",
                "callee": name[:-2],
            }
        return {
            "type": "Identifier",
            "name": name,
        }

    # ── Return Statement ────────────────────────────────────────────────────
    if isinstance(node, ReturnStatement):
        result = {"type": "ReturnStatement"}
        if getattr(node, "expr", None) is not None:
            result["argument"] = ast_to_json(node.expr)
        return result

    # Fallback: unknown node type – stringify class name
    return {"type": type(node).__name__}
