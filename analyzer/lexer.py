import re
from dataclasses import dataclass
from typing import List, Tuple
from utils import find_closest_match

@dataclass
class Token:
    type: str # 'KEYWORD', 'IDENTIFIER', 'NUMBER', 'STRING', 'OPERATOR', 'PUNCTUATION', 'EOF'
    value: str
    line: int
    column: int

C_KEYWORDS = {
    "auto", "break", "case", "char", "const", "continue", "default", "do",
    "double", "else", "enum", "extern", "float", "for", "goto", "if",
    "int", "long", "register", "return", "short", "signed", "sizeof", "static",
    "struct", "switch", "typedef", "union", "unsigned", "void", "volatile", "while"
}

TOKEN_SPECIFICATION = [
    ('COMMENT',         r'//.*'),                         # Single-line comment
    ('MCOMMENT',        r'/\*[\s\S]*?\*/'),               # Multi-line comment
    ('UNCLOSED_MCOMMENT', r'/\*[\s\S]*'),                 # Unclosed multi-line comment
    ('NUMBER',          r'\b\d+(\.\d*)?\b'),              # Integer or decimal number
    ('STRING',          r'"[^"\n]*"'),                    # String literal (single line)
    ('UNCLOSED_STRING', r'"[^"\n]*'),                     # Unclosed string literal on a line
    ('INVALID_ID',      r'\b\d+[a-zA-Z_]\w*\b'),          # Invalid identifier starting with digits
    ('IDENTIFIER',      r'\b[a-zA-Z_]\w*\b'),             # Identifiers
    ('OPERATOR',        r'==|!=|<=|>=|&&|\|\||<<|>>|[+\-*/%=<>&|!^~]'), # Operators
    ('PUNCTUATION',     r'[{}()[\];,.]'),                 # Punctuation
    ('WHITESPACE',      r'[ \t]+'),                       # Skip over spaces and tabs
    ('NEWLINE',         r'\n'),                           # Line endings
    ('STRAY',           r'.'),                            # Any other character
]

def analyze_lexical(source_code: str) -> Tuple[List[Token], List[dict]]:
    """
    Detects lexical errors and generates a sequence of valid tokens.
    We check for C keywords, strict variable (identifier) schemas, and strings.
    """
    tokens = []
    errors = []
    
    tok_regex = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in TOKEN_SPECIFICATION)
    line_num = 1
    line_start = 0
    
    for mo in re.finditer(tok_regex, source_code):
        kind = mo.lastgroup
        value = mo.group()
        column = mo.start() - line_start + 1
        
        if kind == 'NEWLINE':
            line_num += 1
            line_start = mo.end()
        elif kind == 'WHITESPACE':
            pass
        elif kind == 'COMMENT':
            pass
        elif kind == 'MCOMMENT':
            newlines_in_comment = value.count('\n')
            if newlines_in_comment > 0:
                line_num += newlines_in_comment
                line_start = mo.start() + value.rfind('\n') + 1
        elif kind == 'UNCLOSED_MCOMMENT':
            errors.append({
                "type": "Lexical Error",
                "code": "UNCLOSED_COMMENT",
                "message": "Unclosed multi-line comment.",
                "line": line_num,
                "column": column,
                "hint": "Ensure your comment is closed with '*/'.",
                "suggestion": None,
                "auto_corrected": False,
                "recovery_method": "None"
            })
            # Advance lines for whatever was parsed
            newlines = value.count('\n')
            if newlines > 0:
                line_num += newlines
                line_start = mo.start() + value.rfind('\n') + 1
        elif kind == 'IDENTIFIER':
            if value in C_KEYWORDS:
                tokens.append(Token("KEYWORD", value, line_num, column))
            else:
                # Check if it was meant to be a keyword (typo)
                closest_kw = None
                if len(value) >= 4:
                    closest_kw, dist = find_closest_match(value, C_KEYWORDS, max_distance=2)
                
                if closest_kw:
                    errors.append({
                        "type": "Lexical Error",
                        "code": "MISSPELLED_KEYWORD",
                        "message": f"'{value}' looks like a misspelling of keyword '{closest_kw}'.",
                        "line": line_num,
                        "column": column,
                        "hint": f"Did you mean '{closest_kw}'?",
                        "suggestion": closest_kw,
                        "auto_corrected": True,
                        "recovery_method": "None"
                    })
                    # Auto-correct to keyword because confidence is high
                    tokens.append(Token("KEYWORD", closest_kw, line_num, column))
                else:
                    tokens.append(Token("IDENTIFIER", value, line_num, column))
        elif kind == 'INVALID_ID':
            suggested_id = "_" + value
            errors.append({
                "type": "Lexical Error",
                "code": "INVALID_IDENTIFIER",
                "message": f"Invalid identifier '{value}'.",
                "line": line_num,
                "column": column,
                "hint": "Identifiers cannot start with digits in C. Must only contain alphanumeric and underscores.",
                "suggestion": suggested_id,
                "auto_corrected": True,
                "recovery_method": "None"
            })
            # Add to the token stream as the suggested correct ID
            tokens.append(Token("IDENTIFIER", suggested_id, line_num, column))
        elif kind == 'UNCLOSED_STRING':
            errors.append({
                "type": "Lexical Error",
                "code": "UNCLOSED_STRING_LITERAL",
                "message": "Unclosed string literal.",
                "line": line_num,
                "column": column,
                "hint": "Ensure your string closes with a double quote (\").",
                "suggestion": value + '"',
                "auto_corrected": True,
                "recovery_method": "None"
            })
            # Provide it to the token stream as if it were closed, for resilience
            tokens.append(Token("STRING", value + '"', line_num, column))
        elif kind == 'STRAY':
            errors.append({
                "type": "Lexical Error",
                "code": "STRAY_CHARACTER",
                "message": f"Stray '{value}' in program.",
                "line": line_num,
                "column": column,
                "hint": f"The character '{value}' is likely a typo and not valid C syntax.",
                "suggestion": "",
                "auto_corrected": True,
                "recovery_method": "None"
            })
        else:
            # NUMBER, STRING, OPERATOR, PUNCTUATION
            tokens.append(Token(kind, value, line_num, column))
            
    # Add EOF token for parser convenience
    tokens.append(Token("EOF", "", line_num, len(source_code) - line_start + 1))
    
    return tokens, errors
