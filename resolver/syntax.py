def resolve_syntax(source_code: str, errors: list) -> tuple:
    """
    Fixes syntax errors via Statement Mode Recovery:
    - Analyzes each string line independently for missing semicolons.
    - Appends missing closing braces/parentheses from Panic Mode errors at EOF.
    
    Returns: (fixed_code, updated_errors)
    """
    lines = source_code.splitlines()
    fixed_lines = lines.copy()

    # Track structural errors from Panic Mode
    missing_braces = 0
    missing_parens = 0

    # 1. Panic Mode Recovery (Braces / Parens)
    for err in errors:
        code = err.get("code")
        if err.get("recovery_method") == "Panic Mode":
            if code == "MISSING_CLOSING_BRACE":
                missing_braces += 1
                err["auto_corrected"] = True
            elif code == "MISSING_CLOSING_PARENTHESIS" or code == "MISSING_PARENTHESIS":
                missing_parens += 1
                err["auto_corrected"] = True

    # 2. Strict Statement Mode Recovery (Semicolons)
    # The user rule states we must scan EACH line independently.
    # We will generate MISSING_SEMICOLON errors in this pass, rather than relying
    # on the parsed AST errors (which stop working well when parsing fails entirely).
    
    # Filter out old MISSING_SEMICOLON errors from the parser since we are replacing them
    updated_errors = [e for e in errors if e.get("code") != "MISSING_SEMICOLON"]

    for i, line in enumerate(fixed_lines):
        stripped = line.strip()
        
        # Rule 3:
        # Is not empty
        # Does not end with { or }
        # Does not already end with ;
        if not stripped:
            continue
            
        if stripped.endswith("{") or stripped.endswith("}") or stripped.endswith(";"):
            continue
            
        # Is a valid statement (e.g., assignment, function call, return) or variable decl
        # We'll use a heuristic to check if it looks like a statement
        is_statement = False
        
        # Check for keywords that start statements or declarations
        first_word = stripped.split()[0] if stripped else ""
        statement_starters = {"int", "float", "char", "double", "long", "short", "void", "return", "break", "continue", "goto"}
        
        if first_word in statement_starters:
            is_statement = True
        elif "=" in stripped and "==" not in stripped: # rudimentary assignment check
            is_statement = True
        elif stripped.endswith(")") and "(" in stripped: # rudimentary function call check (e.g. printf("Hello"))
            # But wait, `if (x > 5)` also ends with ')', so we must exclude control structures
            if first_word not in {"if", "for", "while"}:
                is_statement = True
        elif stripped.replace("_", "").isalnum(): # checking things like x++ (not perfect but OK) or just variables
            is_statement = True
            
        # Also exclude lines that are part of multi-line comments or macros (simplified here)
        if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*"):
            is_statement = False
            
        if is_statement:
            # Report the error
            updated_errors.append({
                "type": "Syntax Error",
                "code": "MISSING_SEMICOLON",
                "message": "Expected ';' at the end of statement.",
                "line": i + 1,
                "column": len(line) + 1,
                "hint": "Add a semicolon (;).",
                "suggestion": ";",
                "auto_corrected": True,
                "recovery_method": "Statement Mode"
            })
            # Fix it
            fixed_lines[i] = fixed_lines[i] + ";"

    # Append missing closers (Panic Mode)
    if missing_parens > 0:
        fixed_lines.append(")" * missing_parens)
    if missing_braces > 0:
        for _ in range(missing_braces):
            fixed_lines.append("}")

    return "\n".join(fixed_lines), updated_errors
