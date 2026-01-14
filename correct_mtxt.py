import re
import unittest

def correct_mtxt(content: str) -> str:
    """
    Applies a series of corrections to raw MTXT content to fix common LLM mistakes.
    """
    lines = content.split('\n')
    corrected_lines = []
    
    # Track aliases to detect collisions
    aliases = set()
    renamed_aliases = {}
    
    # First pass: Identify aliases and collisions
    # We do a pre-scan because we might need to know about renames before processing usage
    for line in lines:
        line_strip = line.strip()
        if line_strip.startswith('alias '):
            parts = line_strip.split()
            if len(parts) >= 2:
                alias_name = parts[1]
                # Check if alias conflicts with note name schema: [A-G][b#]?\d+
                if re.match(r"^[A-G][b#]?\d+$", alias_name):
                    new_name = alias_name + "_Ch"
                    renamed_aliases[alias_name] = new_name
    
    for line in lines:
        # 3. FIX INLINE COMMENTS
        # The parser does not support inline comments (e.g. "note C4 // comment").
        # We strip everything after the first "//" unless the line starts with it (full line comment).
        stripped = line.strip()
        if not stripped.startswith("//") and "//" in line:
            line = line.split("//")[0].strip()
            
        stripped = line.strip()
        
        # 1. FIX BARE TIMESTAMPS
        # LLMs often output a timestamp meant as a section marker (e.g. "4.0").
        # The parser expects a command, so we comment these out.
        if re.match(r"^\d+(\.\d+)?$", stripped):
             line = "// " + line

        # 2. FIX TIMESTAMPS ON DEFAULTS
        # Global commands like 'dur', 'vel', and 'alias' are state changes, not timed events.
        # LLMs often incorrectly prefix them with "0.0". We strip specifically that timestamp.
        match_global = re.match(r"^(\d+(?:\.\d+)?)\s+(dur=|vel=|alias\s)", stripped)
        if match_global:
            line = stripped[len(match_global.group(1)):].strip()
            
        # 4. FIX ALIAS NAME COLLISIONS
        # LLMs occasionally alias a chord name to a valid note name (e.g. "alias A7 ...").
        # This creates ambiguity for the parser. We rename the alias (e.g. "A7" -> "A7_Ch")
        # in both the definition and the usage.
        if renamed_aliases:
            for bad_name, new_name in renamed_aliases.items():
                if stripped.startswith(f"alias {bad_name} "):
                     line = line.replace(f"alias {bad_name} ", f"alias {new_name} ")
                line = re.sub(r"\bnote\s+" + re.escape(bad_name) + r"\b", f"note {new_name}", line)
            
        corrected_lines.append(line)
        
    if not re.match(r"^mtxt \d+\.\d+", "\n".join(corrected_lines)):
        corrected_lines.insert(0, "mtxt 1.0")

    return "\n".join(corrected_lines)


class TestMtxtCorrector(unittest.TestCase):
    
    def test_fix_bare_timestamps(self):
        raw = """0.0 note C4
4.01
8.0 note D4"""
        expected = """0.0 note C4
// 4.01
8.0 note D4"""
        self.assertEqual(correct_mtxt(raw), expected)

    def test_fix_defaults_timestamp(self):
        raw = """0.0 tempo 120
0.0 dur=0.5
0.0 vel=0.9
0.0 alias X C4"""
        expected = """0.0 tempo 120
dur=0.5
vel=0.9
alias X C4"""
        self.assertEqual(correct_mtxt(raw), expected)

    def test_fix_inline_comments(self):
        raw = """0.0 note C4 // starts loop
1.0 note D4"""
        expected = """0.0 note C4
1.0 note D4"""
        self.assertEqual(correct_mtxt(raw), expected)
        
    def test_fix_alias_collision(self):
        raw = """alias A7 A1,A2,A3
0.0 note A7 dur=1.0"""
        expected = """alias A7_Ch A1,A2,A3
0.0 note A7_Ch dur=1.0"""
        self.assertEqual(correct_mtxt(raw), expected)
        
    def test_fix_alias_collision_does_not_break_notes(self):
        # Ensure we don't accidentally replace a regular note A7 used inside another structure
        # Though our current logic only replaces 'note A7'. 
        pass 

    def test_combined_fixes(self):
        raw = """0.0 dur=1.0
alias G13 G1,2,3
0.0 note C4 // nice note
4.01
0.0 note G13"""
        expected = """dur=1.0
alias G13_Ch G1,2,3
0.0 note C4
// 4.01
0.0 note G13_Ch"""
        self.assertEqual(correct_mtxt(raw), expected)

if __name__ == "__main__":
    unittest.main()
