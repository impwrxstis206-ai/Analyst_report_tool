"""Shared configuration for the market intelligence agent pair."""

import os

import anthropic

MODEL = "claude-opus-5"
EFFORT = "high"

CATEGORIES = [
    "株式(個別銘柄・主要指数)",
    "為替(FX)",
    "暗号資産",
    "マクロ経済全般(金利・金融政策・地政学リスクなど)",
]


def get_client() -> anthropic.Anthropic:
    """Build the Anthropic client, resolving credentials from the environment."""
    return anthropic.Anthropic()
