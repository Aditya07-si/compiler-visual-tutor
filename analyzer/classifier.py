from analyzer.lexer import analyze_lexical
from analyzer.syntax import analyze_syntax
from analyzer.semantic import analyze_semantics
from resolver.syntax import resolve_syntax
from resolver.lexical import resolve_lexical
from resolver.ast_serializer import ast_to_json

def analyze_code(source_code: str):
    """
    Central compiler-like controller.
    Runs lexical → syntax → semantic analysis,
    selects resolution routines, and returns results.
    """

    tokens, lexical_errors = analyze_lexical(source_code)
    ast, syntax_errors = analyze_syntax(tokens)
    semantic_errors = analyze_semantics(ast)

    all_errors = lexical_errors + syntax_errors + semantic_errors

    fixed_code = source_code
    explanation = "Code looks good! No critical errors detected."

    # Sort errors by line for logical reading
    all_errors.sort(key=lambda x: (x.get("line", 0), x.get("column", 0)))

    # Apply fixes in reverse order (semantics -> syntax -> lexical) 
    # Actually, lexical fixes (unclosed strings) first, then syntax fixes (semicolons/braces)
    # Semantic errors usually cannot be auto-fixed safely without more context
    if lexical_errors:
        fixed_code = resolve_lexical(fixed_code, lexical_errors)
    
    if syntax_errors or source_code: # Always run syntax resolution to catch missing semicolons
        fixed_code, new_syntax_errors = resolve_syntax(fixed_code, syntax_errors)
        # Update the main errors list with the newly discovered and fixed missing semicolons
        # We replace the old syntax errors with the new ones from the resolver.
        # But wait, we need to keep the panic mode errors that the resolver kept.
        # So we just reconstruct the all_errors list.
        all_errors = lexical_errors + new_syntax_errors + semantic_errors
        # And make sure syntax_errors references the new list for explanation generation
        syntax_errors = new_syntax_errors

    # Re-sort errors
    all_errors.sort(key=lambda x: (x.get("line", 0), x.get("column", 0)))

    # Generate a readable explanation based on what we found
    msgs = []
    
    warnings = [e for e in all_errors if e.get("severity") == "warning"]
    criticals = [e for e in all_errors if e.get("severity") != "warning"]

    if criticals:
        msgs.append(f"Detected {len(criticals)} error(s).")
    if warnings:
        msgs.append(f"Detected {len(warnings)} warning(s).")

    if lexical_errors:
        if any(e.get("code") == "UNCLOSED_STRING_LITERAL" for e in lexical_errors):
            msgs.append("An unclosed string was closed automatically.")
        if any(e.get("code") == "INVALID_IDENTIFIER" for e in lexical_errors):
            msgs.append("Variable names starting with numbers are not allowed.")

    if syntax_errors:
        if any(e.get("code") == "MISSING_SEMICOLON" for e in syntax_errors):
            msgs.append("Missing semicolons were automatically inserted.")
        if any("BRACE" in e.get("code", "") or "PARENTHESIS" in e.get("code", "") for e in syntax_errors):
            msgs.append("Mismatched braces or parentheses were detected. Attempted to auto-close blocks at the end of the file.")

    if semantic_errors:
        if any(e.get("code") == "UNDECLARED_VARIABLE" for e in semantic_errors):
            msgs.append("You have used variables that were not declared.")
        if any(e.get("code") == "TYPE_MISMATCH" for e in semantic_errors):
            msgs.append("Detected assigning variables to incompatible types (e.g. string to int).")
            
    if msgs:
        explanation = " ".join(msgs)
    
    if fixed_code == source_code and not criticals:
        fixed_code = "" # No fixes applied

    intermediate_code = []
    optimized_code = []
    optimizations_applied = []

    # Block IR Generation only for unrecoverable Lexical or Syntax errors
    blocking_errors = [
        e for e in all_errors 
        if e.get("type") in ["Lexical Error", "Syntax Error"] and not e.get("auto_corrected")
    ]

    # ── Pipeline: AST → TAC → Optimizer ───────────────────────────────────
    # Always attempt AST serialization (partial AST is valid even with semantic errors).
    # TAC + optimizer are only run when no blocking parse errors remain.
    ast_json = None
    ast_error = None

    if ast:
        try:
            ast_json = ast_to_json(ast)
        except Exception as e:
            ast_error = str(e)

    # ── Build DAG from ast_json (always try, even with semantic errors) ─────
    dag_json = None
    if ast_json:
        try:
            from resolver.dag_generator import build_dag
            dag_json = build_dag(ast_json)
        except Exception:
            dag_json = None

    if not blocking_errors and ast:
        from resolver.ir_generator import generate_ir
        from resolver.optimizer import optimize_ir
        
        intermediate_code = generate_ir(ast)
        optimized_code, optimizations_applied = optimize_ir(intermediate_code)

    return {
        "errors": all_errors,
        "fixed_code": fixed_code,
        "explanation": explanation,
        "intermediate_code": intermediate_code,
        "optimized_code": optimized_code,
        "optimizations_applied": optimizations_applied,
        "ast_json": ast_json,
        "ast_error": ast_error,
        "dag_json": dag_json,
    }

