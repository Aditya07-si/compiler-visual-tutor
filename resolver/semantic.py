def resolve_semantic(source_code: str, errors: list) -> str:
    """
    Semantic errors are now conditionally auto-fixed!
    - Single Edit-distance matches for UNDECLARED_VARIABLE typos.
    """
    lines = source_code.splitlines()
    fixed_lines = list(lines)

    for err in sorted(errors, key=lambda x: (x.get("line", 1), -x.get("column", 1))):
        code = err.get("code")
        line_no = err.get("line", 1) - 1
        
        if line_no >= len(fixed_lines):
            continue
            
        if err.get("auto_corrected") and err.get("suggestion"):
            val = err["suggestion"]
            col_idx = err.get("column", 1) - 1
            
            line_text = fixed_lines[line_no]
            if code == "UNDECLARED_VARIABLE":
                # Find the word starting at the error column to replace
                import re
                match = re.search(r'\w+', line_text[col_idx:])
                if match:
                    old_len = len(match.group(0))
                    # Safely replace via concatenation
                    prefix = line_text[:col_idx]
                    suffix = line_text[col_idx + old_len:]
                    fixed_lines[line_no] = prefix + val + suffix

    return "\n".join(fixed_lines)
