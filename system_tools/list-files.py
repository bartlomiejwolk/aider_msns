#!python
import argparse
from pathlib import Path
import sys
import os
import math
import fnmatch
from typing import List, Tuple, Union
import datetime

# Constant variables
DEFAULT_MAX_TOKENS = 10000
TOKEN_CHAR_COUNT = 4  # Approx. 1 token per 4 characters


def get_file_list(
    root_dir: Union[str, Path],
    recursive: bool = True,
    max_depth: int = None,
    name_filter: str = None
) -> List[Path]:
    """Get list of files/dirs based on criteria."""
    root = Path(root_dir)
    if not root.exists():
        raise ValueError(f"Directory does not exist: {root_dir}")
    

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
                    # Skip hidden files and directories
                    if any(part.startswith('.') for part in path.parts):
                        continue
                        
                    # Apply name filter if specified using wildcard and partial matching
                    if name_filter:
                        full_name = path.name.lower()
                        name_without_ext = path.stem.lower()
                        filter_lower = name_filter.lower()
                        if ("*" in name_filter or "?" in name_filter):
                            if not (fnmatch.fnmatch(full_name, filter_lower) or fnmatch.fnmatch(name_without_ext, filter_lower)):
                                continue
                        else:
                            if filter_lower not in full_name and filter_lower not in name_without_ext:
                                continue
                        
                            
                    paths.add(path.relative_to(root))
        else:
            for path in root.glob(glob_pattern):
                # Skip hidden files and directories
                if any(part.startswith('.') for part in path.parts):
                    continue
                    
                # Apply name filter if specified
                if name_filter and not path.name.lower().startswith(name_filter.lower()) and name_filter not in path.name.lower():
                    continue
                    
                        
                paths.add(path.relative_to(root))
    else:
        for path in root.iterdir():
            # Skip hidden files and directories
            if any(part.startswith('.') for part in path.parts):
                continue
            if name_filter:
                full_name = path.name.lower()
                name_without_ext = path.stem.lower()
                filter_lower = name_filter.lower()
                if ("*" in name_filter or "?" in name_filter):
                    if not (fnmatch.fnmatch(full_name, filter_lower) or fnmatch.fnmatch(name_without_ext, filter_lower)):
                        continue
                else:
                    if filter_lower not in full_name and filter_lower not in name_without_ext:
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
        usage="list-files [--directory DIRECTORY] [--name NAME] [--max-depth MAX_DEPTH] [--max-tokens MAX_TOKENS]",
        description="List files and directories (listing is recursive by default)",
        add_help=False
    )
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                        help='Show this help message and exit')
    parser.add_argument(
        "--directory",
        type=str,
        default=".",
        help="Directory to list (default: current working directory)"
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Filter by name (supports wildcards like *.py)"
    )
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
            max_depth=args.max_depth,
            name_filter=args.name
        )
        
        # Convert paths to safe UTF-8 strings
        safe_paths = [str(p).encode('utf-8', errors='replace').decode('utf-8') for p in paths]
        output, truncated = format_output(
            safe_paths,
            max_tokens=args.max_tokens,
            root_dir=args.directory
        )
        full_output, _ = format_output(safe_paths, max_tokens=10**9, root_dir=args.directory)
        
        # Save output to .llm directory (overwrite existing)
        output_dir = Path.cwd() / ".llm"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "list-files-output.txt"
        timestamp = datetime.datetime.now().isoformat()
        cmd = os.path.basename(sys.argv[0])
        if len(sys.argv) > 1:
            command_executed = f"{cmd} " + " ".join(sys.argv[1:])
        else:
            command_executed = cmd
        header = f"{timestamp}\nSEARCH_COMMAND: {command_executed}\n\n"
        with open(output_file, "a", encoding="utf-8", errors="replace") as f:
            f.write(header + full_output + "\n\n")
            
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
