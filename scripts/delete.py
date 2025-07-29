# filename: scripts/clean_pycache.py

import os
import shutil
import sys

def delete_pycache(root_dir):
    """
    Recursively finds and deletes all __pycache__ directories.
    """
    deleted_count = 0
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if '__pycache__' in dirnames:
            pycache_path = os.path.join(dirpath, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                print(f"Deleted: {pycache_path}")
                deleted_count += 1
            except OSError as e:
                print(f"Error deleting {pycache_path}: {e}")
    if deleted_count == 0:
        print(f"No __pycache__ directories found in {root_dir}.")
    else:
        print(f"Successfully deleted {deleted_count} __pycache__ directories.")

if __name__ == "__main__":
    # Get the root directory of the project (assuming script is run from project root)
    # or adjust this path as needed.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    print(f"Searching for __pycache__ in: {project_root}")
    delete_pycache(project_root)
    print("\n__pycache__ cleanup complete.")