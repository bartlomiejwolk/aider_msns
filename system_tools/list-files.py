#!python
import argparse
from pathlib import Path
import sys
import math
from typing import List, Tuple, Union
import datetime

# Constant variables
DEFAULT_MAX_TOKENS = 10000
TOKEN_CHAR_COUNT = 4  # Approx. 1 token per 4 characters


def get_file_list(
    root_dir: Union[str, Path],
    recursive: bool = True,
    max_depth: int = None,
    files_only: bool = False,
    dirs_only: bool = False,
    name_filter: str = None,
    ext_filter: str = None
) -> List[Path]:
    """Get list of files/dirs based on criteria."""
    root = Path(root_dir)
    if not root.exists():
        raise ValueError(f"Directory does not exist: {root_dir}")
    
    if dirs_only and files_only:
        raise ValueError("Cannot specify both --files-only and --dirs-only")

    paths = []
    if recursive:
        if max_depth is None:
            glob_pattern = "**/*"
        else:
            # For max_depth=2 we want "**/*" and "**/*/*" but not deeper
            glob_pattern = ["*"]
            for _ in range(1, max_depth + 1):
                glob_pattern.append(f"{'*/' * _}*")
        
        paths = set()
        if isinstance(glob_pattern, list):
            for pattern in glob_pattern:
                for path in root.glob(pattern):
                    # Skip .git, .aider* and .llm directories and their contents
                    if ('.git' in path.parts or 
                        any(part.startswith('.aider') for part in path.parts) or
                        '.llm' in path.parts):
                        continue
                    if dirs_only and not path.is_dir():
                        continue
                    if files_only and not path.is_file():
                        continue
                        
                    # Apply name filter if specified
                    if name_filter and not path.name.lower().startswith(name_filter.lower()) and name_filter not in path.name.lower():
                        continue
                        
                    # Apply extension filter if specified
                    if ext_filter and path.is_file():
                        if not path.suffix.lower().endswith(f".{ext_filter.lower()}"):
                            continue
                            
                    paths.add(path.relative_to(root))
        else:
            for path in root.glob(glob_pattern):
                # Skip .git and .aider* directories and their contents
                if '.git' in path.parts or any(part.startswith('.aider') for part in path.parts):
                    continue
                if dirs_only and not path.is_dir():
                    continue
                if files_only and not path.is_file():
                    continue
                    
                # Apply name filter if specified
                if name_filter and not path.name.lower().startswith(name_filter.lower()) and name_filter not in path.name.lower():
                    continue
                    
                # Apply extension filter if specified
                if ext_filter and path.is_file():
                    if not path.suffix.lower().endswith(f".{ext_filter.lower()}"):
                        continue
                        
                paths.add(path.relative_to(root))
    else:
        for path in root.iterdir():
            # Skip .git, .aider* and .llm directories
            if path.name == '.git' or path.name.startswith('.aider') or path.name == '.llm':
                continue
            if dirs_only and not path.is_dir():
                continue
            if files_only and not path.is_file():
                continue
            paths.append(path.relative_to(root))
    
    return sorted(paths)

def format_output(
    paths: List[Path],
    max_tokens: int = DEFAULT_MAX_TOKENS,
    root_dir: Union[str, Path] = None,
    files_only: bool = False,
    dirs_only: bool = False
) -> Tuple[str, bool]:
    """Format output respecting token limit using a simple heuristic (approx. 1 token per 4 characters)."""
    output = []
    token_count = 0
    truncated = False
    remaining_count = 0
    
    root = Path(root_dir) if root_dir else None
    for i, path in enumerate(paths):
        line = str(path)
        if root:
            line = str(root / path)
        # Append trailing slash for directories
        if (root / path).is_dir():
            line += "/"
        
        tokens_line = math.ceil((len(line) + 1) / TOKEN_CHAR_COUNT)
        
        if token_count + tokens_line > max_tokens:
            remaining_count = len(paths) - i
            truncated = True
            break
            
        output.append(line)
        token_count += tokens_line
    
    result = "\n".join(output)
    if truncated:
        result += f"\n\n[TRUNCATED] {remaining_count} more {'files/dirs' if not (files_only or dirs_only) else 'files' if files_only else 'dirs'} not shown (max tokens: {max_tokens})"
    
    return result, truncated

def main():
    parser = argparse.ArgumentParser(
        description="List files and directories with various options"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to list (default: current directory)"
    )
    parser.add_argument(
        "--files-only",
        action="store_true",
        help="List only files (exclude directories)"
    )
    parser.add_argument(
        "--dirs-only",
        action="store_true",
        help="List only directories (exclude files)"
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Filter by name (supports wildcards like *.py)"
    )
    parser.add_argument(
        "--ext",
        type=str,
        default=None,
        help="Filter by file extension (e.g. 'py' or 'txt')"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--recursive",
        dest="recursive",
        action="store_true",
        help="Enable recursive directory traversal (default: enabled)"
    )
    group.add_argument(
        "--no-recursive",
        dest="recursive",
        action="store_false",
        help="Disable recursive directory traversal"
    )
    parser.set_defaults(recursive=True)
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum recursion depth (default: unlimited)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help=f"Maximum output size in characters (default: {DEFAULT_MAX_TOKENS})"
    )
    args = parser.parse_args()
    # Reconfigure stdout to use UTF-8 so all Unicode characters print correctly.
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass
    
    try:
        paths = get_file_list(
            args.directory,
            recursive=args.recursive,
            max_depth=args.max_depth,
            files_only=args.files_only,
            dirs_only=args.dirs_only,
            name_filter=args.name,
            ext_filter=args.ext
        )
        
        # Convert paths to safe UTF-8 strings
        safe_paths = [str(p).encode('utf-8', errors='replace').decode('utf-8') for p in paths]
        output, truncated = format_output(
            safe_paths,
            max_tokens=args.max_tokens,
            root_dir=args.directory,
            files_only=args.files_only,
            dirs_only=args.dirs_only
        )
        
        # Save output to .llm.context directory (overwrite existing)
        output_dir = Path.cwd() / ".llm"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "list-files-output.md"
        command_executed = " ".join(sys.argv)
        timestamp = datetime.datetime.now().isoformat()
        header = f"\n\n## List results appended on {timestamp}\n**Command:** {command_executed}\n\n"
        with open(output_file, "a", encoding="utf-8", errors="replace") as f:
            f.write(header + output)
            
        # Also print to stdout for immediate viewing
        print(output)
        print(f"\nOutput saved to: {output_file}")
        
        if truncated:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
