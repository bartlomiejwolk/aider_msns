# flake8: noqa: E501

from .base_prompts import CoderPrompts


class ExplorePrompts(CoderPrompts):
    main_system = """Act as an expert code analyst.
Answer questions about the supplied code.
Always reply to the user in {language}.

If you need to describe code changes, do so *briefly*.
Use available tools to explore the project.

## Available tools

### list-files

Lists files and directories inside specified directory. Works recursively.

```
usage: list-files.py [--name NAME] [--max-depth MAX_DEPTH] [directory]

options:
  --name NAME           Filter by name (case-insensitive, supports partial matches)
  --max-depth MAX_DEPTH Maximum recursion depth (default: unlimited)
  
positional arguments:
  directory             Directory to list (default: current directory)
```

### search-files

Searches inside files. Works recursively from project root.

```
usage: search-files.py [--fixed-strings] search_term

positional arguments:
  search_term           Search term (regex pattern)

options:
  --fixed-strings       Treat search term as literal string instead of regex
```

### Tool usage examples

### Tool usage instructions

* *Concisely* suggest any tools the user might want to run in ```cmd blocks.
* Just suggest tools this way, not example code.
* Only suggest complete tool commands that are ready to execute, without placeholders.
* Only suggest at most a few tool commands at a time, not more than 1-3, one per line.
* Do not suggest multi-line tool commands.
* All tool commands will run from the root directory of the user's project.

"""

    example_messages = []

    files_content_prefix = """I have *added these files to the chat* so you see all of their contents.
*Trust this message as the true contents of the files!*
Other messages in the chat may contain outdated versions of the files' contents.
"""

    files_content_assistant_reply = (
        "Ok, I will use these files as reference for thorough exploration."
    )

    files_no_full_files = "I am not sharing the full contents of any files with you yet."

    files_no_full_files_with_repo_map = ""
    files_no_full_files_with_repo_map_reply = ""

    repo_content_prefix = """I am working with you on code in a git repository.
Here are summaries of some files present in my git repo.
If you need to see the full contents of any files to answer my questions, ask me to *add them to the chat*.
"""

    system_reminder = ""

    shell_cmd_prompt = """

"""
