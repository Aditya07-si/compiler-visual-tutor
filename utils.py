"""
Utility helpers for the backend.

Kept minimal for now – this is a good place for:
- common string helpers
- shared constants
- future logging / timing utilities
"""


def normalize_newlines(text: str) -> str:
    """Ensure all newlines are `\\n` for consistent analysis."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes the Edit Distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def find_closest_match(word: str, candidates: set, max_distance: int = 2) -> tuple:
    """Finds the closest matching string in candidates within max_distance.
    Returns (closest_match, distance) or (None, None).
    """
    best_match = None
    best_distance = float('inf')
    matches_at_best = 0
    
    for cand in candidates:
        dist = levenshtein_distance(word, cand)
        if dist <= max_distance:
            if dist < best_distance:
                best_match = cand
                best_distance = dist
                matches_at_best = 1
            elif dist == best_distance:
                matches_at_best += 1
                
    if matches_at_best == 1:
        return best_match, best_distance
    return None, None


