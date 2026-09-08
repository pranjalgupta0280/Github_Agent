import os
import glob
from typing import List, Dict

def inspect_repository(repo_path: str) -> Dict[str, any]:
    """
    Scans repository directory and returns list of source files and file tree.
    """
    abs_path = os.path.abspath(repo_path)
    if not os.path.exists(abs_path):
        return {"file_tree": [], "files": {}}

    file_tree = []
    files_content = {}
    
    # Ignore common build/cache folders
    ignore_dirs = {'.git', '__pycache__', '.pytest_cache', 'venv', '.venv', 'node_modules'}
    
    for root, dirs, files in os.walk(abs_path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if file.endswith(('.py', '.md', '.txt', '.json', '.yaml', '.yml')):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, abs_path)
                file_tree.append(rel_path)
                
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        files_content[rel_path] = f.read()
                except Exception:
                    pass

    return {
        "file_tree": sorted(file_tree),
        "files": files_content
    }

def apply_patch_to_file(repo_path: str, rel_filepath: str, new_content: str) -> bool:
    """
    Writes updated file content directly to target file inside the repository.
    """
    full_path = os.path.join(os.path.abspath(repo_path), rel_filepath)
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    except Exception as e:
        print(f"Error writing patch to {full_path}: {e}")
        return False
