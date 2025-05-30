#!python
import argparse
import subprocess
import sys
import os
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
    fixed_strings: bool = False
) -> str:
    """Run ripgrep search with basic parameters."""
    search_dir = Path(directory)
    if not search_dir.exists():
        raise ValueError(f"Directory does not exist: {directory}")

    cmd = ["rg.exe", "--color=never", "--no-heading", "--with-filename", "--line-number"]


    # Apply hardcoded ignore globs (these should override the whitelists)
    default_ignores = [
        "!**/.*",                     # Ignore all hidden files and directories
    ]
    for ignore_glob in default_ignores:
        cmd.extend(["--glob", ignore_glob])
        

    if fixed_strings:
        cmd.append("--fixed-strings")
    cmd.append(search_term)
    

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
    max_tokens: int = DEFAULT_MAX_TOKENS
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
        result += f"\n\n[TRUNCATED] {remaining_count} more matches not shown (max tokens: {max_tokens})"
    
    return result, truncated

def main():
    parser = argparse.ArgumentParser(
        usage="search-files [--directory DIRECTORY] [--fixed-strings] [--max-tokens MAX_TOKENS] search_term",
        description="Search files using ripgrep",
        add_help=False
    )
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                        help='Show this help message and exit')
    parser.add_argument(
        "--directory",
        default=".",
        help="Directory to search (default: current directory)"
    )
    parser.add_argument(
        "search_term",
        help="Search term (regex pattern)\nUse --fixed-strings for exact matches"
    )
    parser.add_argument(
        "--fixed-strings",
        action="store_true",
        help="Treat search term as literal string instead of regex"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help=f"Maximum output size in tokens (default: {DEFAULT_MAX_TOKENS} ~40KB)"
    )
    
    args = parser.parse_args()
    # Reconfigure stdout to use UTF-8 and safely print Unicode characters.
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass
    
    try:
        search_term = args.search_term
        output = run_ripgrep_search(
            search_term,
            args.directory,
            args.fixed_strings
        )
        
        if output is None:
            print("No results found", file=sys.stderr)
            sys.exit(1)
            
        # Ensure output is properly encoded before formatting
        safe_output = output.encode('utf-8', errors='replace').decode('utf-8')
        # Format the complete output without token limits, capturing all results like the list-files script does
        formatted_output, truncated = format_output(safe_output, args.max_tokens)
        
        full_output, _ = format_output(safe_output, max_tokens=10**9)
        output_dir = Path.cwd() / ".llm"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "search-files-output.txt"
        cmd = os.path.basename(sys.argv[0])
        if len(sys.argv) > 1:
            command_executed = f"{cmd} " + " ".join(sys.argv[1:])
        else:
            command_executed = cmd
        # Generate timestamp and header for output file, ensuring the format matches that of list-files
        timestamp = datetime.datetime.now().isoformat()
        header = f"SEARCH | {timestamp} | {command_executed}\n\n"
        with open(output_file, "a", encoding="utf-8", errors="replace") as f:
            f.write(header + full_output + "\n\n")
            
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
