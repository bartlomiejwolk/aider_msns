#!/usr/bin/env python

from aider import prompts
from aider.coders.base_coder import Coder
from aider.coders.ask_prompts import AskPrompts


class ExploreCoder(Coder):
    edit_format = "explore"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gpt_prompts = AskPrompts()

    def get_edits(self, mode="update"):
        return []

    def apply_edits(self, edits):
        return

    def apply_edits_dry_run(self, edits):
        return
