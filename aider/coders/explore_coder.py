#!/usr/bin/env python

from aider.coders.base_coder import Coder
from .explore_prompts import ExplorePrompts


class ExploreCoder(Coder):
    edit_format = "explore"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gpt_prompts = ExplorePrompts()

    def get_edits(self, mode="update"):
        return []

    def apply_edits(self, edits):
        return []

    def apply_edits_dry_run(self, edits):
        return []
