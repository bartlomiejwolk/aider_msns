#!python
import argparse
import subprocess
import sys
from pathlib import Path
import math
from typing import List, Tuple
import datetime

# Constant variables
DEFAULT_MAX_TOKENS = 10000  # Limits output to ~10,000 tokens (~40KB text)
TOKEN_CHAR_COUNT = 4  # Approx. 1 token per 4 characters

def run_ripgrep_search(
    search_term: str,
    directory: str = ".",
    files_only: bool = False,
    max_results: int = None,
    ext: str = None,
    fixed_strings: bool = False,
    files_mode: bool = False,  # Changed from use_glob
    globs: List[str] = None    # New parameter
) -> str:
    """Run ripgrep search with basic parameters."""
    search_dir = Path(directory)
    if not search_dir.exists():
        raise ValueError(f"Directory does not exist: {directory}")

    cmd = ["rg.exe", "--color=never", "--no-heading", "--with-filename", "--line-number",
           "--glob", "!**/.llm/**", "--glob", "!**/.git/**", "--glob", "!**/.aider*/**"]

    if files_mode:
        cmd.append("--files")
        
    if globs:
        for g in globs:
            cmd.extend(["--glob", g])

    # Handle normal search mode
    if not files_mode:
        if files_only:
            cmd.append("--files-with-matches")
        if fixed_strings:
            cmd.append("--fixed-strings")
        cmd.append(search_term)

    # Handle extension filters and additional globs
    if ext:
        for extension in ext.split(','):
            cmd.extend(["--glob", f"*.{extension.strip()}"])
    if max_results:
        cmd.extend(["--max-count", str(max_results)])

    cmd.append(str(search_dir))
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            return ""
        raise RuntimeError(f"ripgrep search failed: {e.stderr}")

def format_output(
    output: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    files_only: bool = False
) -> Tuple[str, bool]:
    """Format output respecting token limit."""
    if output is None:
        return "", False
        
    lines = output.splitlines()
    formatted = []
    token_count = 0
    truncated = False
    remaining_count = 0
    
    for i, line in enumerate(lines):
        tokens_line = math.ceil((len(line) + 1) / TOKEN_CHAR_COUNT)
        
        if token_count + tokens_line > max_tokens:
            remaining_count = len(lines) - i
            truncated = True
            break
            
        formatted.append(line)
        token_count += tokens_line
    
    result = "\n".join(formatted)
    if truncated:
        result += f"\n\n[TRUNCATED] {remaining_count} more {'matches' if not files_only else 'files'} not shown (max tokens: {max_tokens})"
    
    return result, truncated

def main():
    parser = argparse.ArgumentParser(
        description="Search files using ripgrep (supports both regex and file patterns)",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Examples:
  # Regex search for Python class definitions
  %(prog)s 'class\\s+\\w+' src
  
  # Literal string search with fixed-strings
  %(prog)s 'GetComponentName(' --fixed-strings
  
  # File pattern search for *.cpp files
  %(prog)s --files --glob '*.cpp' src
  
  # Combined extension filter and regex search
  %(prog)s 'TODO: ' --ext py,js
"""
    )
    parser.add_argument(
        "search_term",
        nargs="?",
        default=None,
        help="Search term (regex pattern)\nUse --fixed-strings for exact matches"
    )
    parser.add_argument(
        "--fixed-strings",
        action="store_true",
        help="Treat search term as literal string instead of regex"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to search (default: current directory)"
    )
    parser.add_argument(
        "--files-only",
        action="store_true",
        help="Only show files containing matches, not the matches themselves"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help=f"Maximum output size in tokens (default: {DEFAULT_MAX_TOKENS} ~40KB)"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        help="Maximum number of matches to return per file (uses rg --max-count)"
    )
    parser.add_argument(
        "--ext",
        type=str,
        default=None,
        help="Filter by file extensions (comma-separated, e.g. 'py,txt')"
    )
    parser.add_argument(
        "--files",
        action="store_true",
        help="List files instead of searching content"
    )
    parser.add_argument(
        "--glob",
        type=str,
        action="append",
        help="File pattern to include/exclude (can be used multiple times)"
    )
    
    args = parser.parse_args()
    # Reconfigure stdout to use UTF-8 and safely print Unicode characters.
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass
    
    try:
        # Handle missing search term when using --glob
        search_term = args.search_term if args.search_term else "."
        output = run_ripgrep_search(
            search_term,
            args.directory,
            args.files_only,
            args.max_results,
            args.ext,
            args.fixed_strings,
            args.files,
            args.glob
        )
        
        if output is None:
            print("No results found", file=sys.stderr)
            sys.exit(1)
            
        # Ensure output is properly encoded before formatting
        safe_output = output.encode('utf-8', errors='replace').decode('utf-8')
        formatted_output, truncated = format_output(safe_output, args.max_tokens, args.files_only)
        
        # Save output to .llm.context directory (overwrite existing)
        output_dir = Path.cwd() / ".llm"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "search-files-output.md"
        command_executed = " ".join(sys.argv)
        timestamp = datetime.datetime.now().isoformat()
        header = f"\n\n## Search results appended on {timestamp}\n**Command:** {command_executed}\n\n"
        with open(output_file, "a", encoding="utf-8", errors="replace") as f:
            f.write(header + formatted_output)
            
        # Print to stdout only if there is output
        if formatted_output.strip():
            print(formatted_output)
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
