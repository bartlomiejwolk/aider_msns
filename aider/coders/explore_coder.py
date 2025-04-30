#!/usr/bin/env python

from aider.coders.base_coder import Coder
from .explore_prompts import ExplorePrompts
import re

class ExploreCoder(Coder):
    edit_format = "explore"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gpt_prompts = ExplorePrompts()

    def get_edits(self):
        content = self.partial_response_content

        # might raise ValueError for malformed ORIG/UPD blocks
        edits = list(
            find_original_update_blocks(
                content,
                self.fence,
                self.get_inchat_relative_files(),
            )
        )

        self.shell_commands += [edit[1] for edit in edits if edit[0] is None]
        edits = [edit for edit in edits if edit[0] is not None]

        return edits

DEFAULT_FENCE = ("`" * 3, "`" * 3)

def find_original_update_blocks(content, fence=DEFAULT_FENCE, valid_fnames=None):
    lines = content.splitlines(keepends=True)
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for shell code blocks
        shell_starts = [
            "```bash",
            "```sh",
            "```shell",
            "```cmd",
            "```batch",
            "```powershell",
            "```ps1",
            "```zsh",
            "```fish",
            "```ksh",
            "```csh",
            "```tcsh",
        ]

        if any(line.strip().startswith(start) for start in shell_starts):
            shell_content = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                shell_content.append(lines[i])
                i += 1
            if i < len(lines) and lines[i].strip().startswith("```"):
                i += 1  # Skip the closing ```

            yield None, "".join(shell_content)
            continue

        i += 1
