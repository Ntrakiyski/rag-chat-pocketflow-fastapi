import os

def combine_codebase_to_markdown(output_filename="combined_codebase.md"):
    project_root = os.path.dirname(os.path.abspath(__file__))
    output_filepath = os.path.join(project_root, output_filename)

    # Define the files and directories to include based on the new structure
    # and the screenshot provided.
    # Categorize for better organization in the output markdown.

    # Files that are primarily documentation or configuration at the root/docs level
    # or specific non-python files from other folders that should be included.
    doc_and_root_config_files = [
        "docs/design.md",
        "docs/api_docs.md",
        "README.md",
        "requirements.txt",
        ".windsurfrules",
        ".clinerules",
        ".cursorrules",
        ".gitignore",
        ".goosehints",
        "run.bat",
        "Dockerfile",       # Added based on request
        "docker-compose.yml", # Added based on request
        "scripts/api_tests.http", # Added for specific non-python file in scripts
        # delete_redis_index.py is removed as it's not in the screenshot and scripts/delete.py covers it.
    ]

    # Directories that contain Python code, which will be walked recursively
    python_code_dirs = [
        "app",
        "nodes",
        "scripts",  # Added based on screenshot to include delete.py and other python scripts
        "utils"
    ]

    # Helper to determine code block language for markdown formatting
    def get_code_block_type(filepath):
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".py":
            return "python"
        elif ext == ".md":
            return "markdown"
        elif ext == ".txt":
            return "text"
        elif ext == ".bat":
            return "batch"
        elif ext == ".yml" or ext == ".yaml": # For docker-compose.yml
            return "yaml"
        elif os.path.basename(filepath).lower() == "dockerfile": # For Dockerfile (no extension)
            return "dockerfile"
        elif ext == ".http": # For api_tests.http
            return "http"
        # For files without common extensions or specific rules (e.g., dotfiles)
        elif os.path.basename(filepath) in [".windsurfrules", ".clinerules", ".cursorrules", ".gitignore", ".goosehints"]:
            return "text"
        return "" # Default to no specific language if unknown

    with open(output_filepath, "w", encoding="utf-8") as outfile:
        outfile.write("# Combined Project Codebase\n\n")
        outfile.write("This document contains the consolidated code from key project files and directories.\n\n")

        # Process Documentation and Root Configuration Files
        outfile.write("## Documentation and Root Configuration\n\n")
        for filename in doc_and_root_config_files:
            filepath = os.path.join(project_root, filename)
            # Ensure we don't include the output file itself
            # os.path.abspath is used for robust comparison of paths
            if os.path.exists(filepath) and os.path.abspath(filepath) != os.path.abspath(output_filepath):
                outfile.write(f"---\n### File: `{filename}`\n---\n\n")
                code_type = get_code_block_type(filename)
                outfile.write(f"```{code_type}\n")
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        outfile.write(f.read())
                except Exception as e:
                    outfile.write(f"# Error reading file {filename}: {e}\n")
                outfile.write("\n```\n\n")
            else:
                # Only report if not the output file and it truly doesn't exist
                if os.path.abspath(filepath) != os.path.abspath(output_filepath):
                    outfile.write(f"---\n### File: `{filename}` (Not Found or Excluded)\n---\n\n")


        # Process Python Application Directories (app, nodes, scripts, utils)
        # These directories will be walked recursively to find Python files.
        for dirname in python_code_dirs:
            dir_path = os.path.join(project_root, dirname)
            if os.path.isdir(dir_path):
                outfile.write(f"## Directory: `{dirname}`\n\n")
                # os.walk traverses directories recursively
                for root, dirs, files in os.walk(dir_path):
                    # IMPORTANT: Modify dirs in-place to skip specific folders
                    # such as __pycache__, venv, temp_uploads which are not source code.
                    dirs[:] = [d for d in dirs if d not in ['__pycache__', 'venv', 'temp_uploads']]
                    
                    # Sort files for consistent output order
                    files.sort()
                    for file in files:
                        # Only include .py files in this recursive walk section.
                        # Other file types like .http from 'scripts' are handled explicitly
                        # in the doc_and_root_config_files list.
                        if file.endswith(".py"): 
                            filepath = os.path.join(root, file)
                            relative_filepath = os.path.relpath(filepath, project_root)
                            outfile.write(f"---\n### File: `{relative_filepath}`\n---\n\n")
                            
                            # All Python files get 'python' highlight
                            outfile.write("```python\n")
                            try:
                                with open(filepath, "r", encoding="utf-8") as f:
                                    outfile.write(f.read())
                            except Exception as e:
                                outfile.write(f"# Error reading file {relative_filepath}: {e}\n")
                            outfile.write("\n```\n\n")
            else:
                outfile.write(f"## Directory: `{dirname}` (Not Found)\n\n")

    print(f"Codebase combined into {output_filepath}")

if __name__ == "__main__":
    combine_codebase_to_markdown()