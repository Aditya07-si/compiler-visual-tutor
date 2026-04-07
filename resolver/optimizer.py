import re

def optimize_ir(ir_lines: list) -> tuple:
    """
    Applies basic optimizations on TAC (Three-Address Code).
    - Constant Folding: 2 + 3 -> 5
    - Constant Propagation: t1 = 5; a = t1 -> a = 5
    - Common Subexpression Elimination: t1 = a * b; t2 = a * b -> t2 replaces t1 uses
    - Copy Propagation: x = y; z = x -> z = y
    - Strength Reduction: x * 2 -> x + x
    - Dead Code Elimination: remove unused assignments to temporaries
    
    Returns: (optimized_lines, optimizations_applied)
    """
    optimizations_applied = []
    
    # We will do a few passes until no more changes can be made
    current_lines = list(ir_lines)
    changed = True
    
    # Regexes for parsing TAC
    # Assignment: "x = y"
    # Binary: "x = y op z"
    # Return: "return x" or "return"
    
    binary_op_pattern = re.compile(r'^([a-zA-Z_]\w*)\s*=\s*(.+?)\s*([\+\-\*/<>=!]+)\s*(.+)$')
    assign_pattern = re.compile(r'^([a-zA-Z_]\w*)\s*=\s*(.+)$')
    return_pattern = re.compile(r'^return\s*(.*)$')
    
    max_passes = 10
    pass_num = 0
    
    while changed and pass_num < max_passes:
        changed = False
        pass_num += 1
        
        # 1. Constant Folding & Strength Reduction
        for i, line in enumerate(current_lines):
            match = binary_op_pattern.match(line)
            if match:
                dest, left, op, right = match.groups()
                left = left.strip()
                right = right.strip()
                
                # Check if both are constants
                def is_number(s):
                    try:
                        float(s)
                        return True
                    except ValueError:
                        return False
                        
                if is_number(left) and is_number(right):
                    # Constant Folding
                    try:
                        # eval is safe here since we verified is_number and basic ops
                        if op in ['+', '-', '*', '/']:
                            # Handle division by zero safely
                            if op == '/' and float(right) == 0:
                                continue
                            val = eval(f"{left} {op} {right}")
                            # format nicely
                            if isinstance(val, float) and val.is_integer():
                                val = int(val)
                            new_line = f"{dest} = {val}"
                            current_lines[i] = new_line
                            optimizations_applied.append(f"Constant Folding: {left} {op} {right} -> {val}")
                            changed = True
                            continue
                    except:
                        pass
                
                # Strength Reduction (x * 2 -> x << 1 or x + x)
                # Keep it simple: x * 2 -> x + x
                if op == '*' and (right == '2' or left == '2'):
                    var = left if right == '2' else right
                    new_line = f"{dest} = {var} + {var}"
                    if new_line != line:
                        current_lines[i] = new_line
                        optimizations_applied.append(f"Strength Reduction: {line} -> {new_line}")
                        changed = True
                        continue

        # 2. Constant Propagation & Copy Propagation
        # Find x = <const/var> and replace in subsequent lines
        values = {}
        for i, line in enumerate(current_lines):
            b_match = binary_op_pattern.match(line)
            if b_match:
                dest = b_match.group(1).strip()
                # Clear value if overwritten
                if dest in values:
                    values.pop(dest, None)
                continue
                
            a_match = assign_pattern.match(line)
            if a_match:
                dest, val = a_match.groups()
                dest = dest.strip()
                val = val.strip()
                if " " not in val and not val.startswith("call"): # simple assign
                    values[dest] = val
                    
        # Apply the collected values
        for i, line in enumerate(current_lines):
            # Parse line components and replace
            line_mutated = line
            for var, val in values.items():
                # Avoid replacing the destination of the assignment
                # Use regex to replace whole word boundary
                var_pattern = r'\b' + re.escape(var) + r'\b'
                
                # Split dest and rhs
                if "=" in line_mutated:
                    parts = line_mutated.split("=", 1)
                    dest_str = parts[0]
                    rhs_str = parts[1]
                    
                    new_rhs = re.sub(var_pattern, val, rhs_str)
                    if new_rhs != rhs_str and dest_str.strip() != var:
                        line_mutated = f"{dest_str}={new_rhs}"
                        if val.replace('.','',1).isdigit():
                            optimizations_applied.append(f"Constant Propagation: replaced {var} with {val}")
                        else:
                            optimizations_applied.append(f"Copy Propagation: replaced {var} with {val}")
                        changed = True
                elif line_mutated.startswith("return "):
                    new_ret = re.sub(var_pattern, val, line_mutated)
                    if new_ret != line_mutated:
                        line_mutated = new_ret
                        changed = True
            current_lines[i] = line_mutated

        # 3. Common Subexpression Elimination
        # If t1 = a + b and t2 = a + b, replace t2 uses with t1
        expressions = {}
        for i, line in enumerate(current_lines):
            b_match = binary_op_pattern.match(line)
            if b_match:
                dest, left, op, right = b_match.groups()
                left, right = left.strip(), right.strip()
                expr_key = f"{left} {op} {right}"
                
                # Order independent for commutative ops
                if op in ['+', '*']:
                    # sort alphabetically
                    if left > right:
                        expr_key = f"{right} {op} {left}"
                
                if expr_key in expressions:
                    prev_dest = expressions[expr_key]
                    # We can transform this line into a copy: dest = prev_dest
                    new_line = f"{dest} = {prev_dest}"
                    current_lines[i] = new_line
                    optimizations_applied.append(f"Common Subexpression Elimination: '{expr_key}' replaced with {prev_dest}")
                    changed = True
                else:
                    expressions[expr_key] = dest

        # 4. Dead Code Elimination
        # Remove variables that are assigned but never used, AND are temporaries (t1, t2).
        # We can also remove normal variables if never used, but let's stick to safe bounds.
        uses = set()
        for line in current_lines:
            # find all word identifiers
            # Split line into lhs and rhs if assignment
            if "=" in line:
                lhs, rhs = line.split("=", 1)
                words = re.findall(r'[a-zA-Z_]\w*', rhs)
                uses.update(words)
            elif line.startswith("return "):
                words = re.findall(r'[a-zA-Z_]\w*', line[7:])
                uses.update(words)
                
        to_keep = []
        for line in current_lines:
            if "=" in line:
                dest = line.split("=")[0].strip()
                # If it's a temporary (starts with t and digit) and not used
                if re.match(r'^t\d+$', dest) and dest not in uses:
                    optimizations_applied.append(f"Dead Code Elimination: removed unused temporary {dest}")
                    changed = True
                    continue
            to_keep.append(line)
            
        current_lines = to_keep

    # Remove duplicates from optimizations list but keep order
    seen = set()
    unique_opts = []
    for opt in optimizations_applied:
        # Simplify the message for repetitive stuff
        if opt not in seen:
            seen.add(opt)
            unique_opts.append(opt)
            
    if not unique_opts:
        unique_opts.append("No safe optimizations could be applied.")
        
    return current_lines, unique_opts
