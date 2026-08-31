import os
import fnmatch

EXCLUDE = ["__pycache__", ".pytest_cache", "*.pyc"]

def print_tree(directory, f, prefix=""):
    try:
        entries = sorted(os.listdir(directory))
    except Exception:
        return
        
    entries = [e for e in entries if not any(fnmatch.fnmatch(e, p) for p in EXCLUDE)]
        
    for i, entry in enumerate(entries):
        path = os.path.join(directory, entry)
        is_last = (i == len(entries) - 1)
        connector = "\\-- " if is_last else "|-- "
        
        f.write(f"{prefix}{connector}{entry}\n")
        
        if os.path.isdir(path):
            new_prefix = prefix + ("    " if is_last else "|   ")
            print_tree(path, f, new_prefix)

with open("structure.txt", "w", encoding="utf-8") as f:
    f.write("backend/\n")
    print_tree("d:/Projects/agent-virtual-office/backend", f)
