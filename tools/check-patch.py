import sys, re

def check_patch(filename):
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    hunk_regex = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')
    i = 0
    errors = 0
    while i < len(lines):
        line = lines[i]
        m = hunk_regex.match(line)
        if m:
            hunk_idx = i + 1
            old_start = int(m.group(1))
            old_count = int(m.group(2)) if m.group(2) is not None else 1
            new_start = int(m.group(3))
            new_count = int(m.group(4)) if m.group(4) is not None else 1
            
            i += 1
            actual_old = 0
            actual_new = 0
            while i < len(lines):
                hl = lines[i]
                if hl.startswith('diff --git') or hunk_regex.match(hl):
                    break
                if hl.startswith('\\ No newline'):
                    i += 1
                    continue
                if hl.startswith('-'):
                    actual_old += 1
                elif hl.startswith('+'):
                    actual_new += 1
                elif hl.startswith(' ') or hl == '\n':
                    actual_old += 1
                    actual_new += 1
                else:
                    # Malformed line or patch footer
                    break
                i += 1
            
            if actual_old != old_count or actual_new != new_count:
                print(f"Mismatch at line {hunk_idx}: header says -{old_start},{old_count} +{new_start},{new_count}, but found old={actual_old}, new={actual_new}")
                errors += 1
        else:
            i += 1
    
    if errors == 0:
        print(f"{filename}: ALL HUNKS VALID!")
    else:
        print(f"{filename}: {errors} ERRORS FOUND!")
    return errors

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'xnu/patches/0900-en0-Apple80211-for-wifid-over-the-Topaz.patch'
    sys.exit(check_patch(path))
