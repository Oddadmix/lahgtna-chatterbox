"""
config.py — Central configuration for Lahgtna TTS
==================================================
All model IDs, file paths, dialect mappings, and generation defaults live
here.  Import from this module to avoid magic strings scattered across the
codebase.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Model identifiers
# ---------------------------------------------------------------------------

#: Hugging Face repo hosting the fine-tuned Chatterbox checkpoint.
MODEL_REPO_ID: str = "oddadmix/lahgtna-chatterbox-v1"

#: Hugging Face repo for the dialect-router classifier.
ROUTER_MODEL_ID: str = "oddadmix/dialect-router-v0.1"

#: Files to pull from the checkpoint repo (reduces download size).
SNAPSHOT_PATTERNS: list[str] = [
    "ve.pt",
    "t3_mtl23ls_v2.safetensors",
    "s3gen.pt",
    "grapheme_mtl_merged_expanded_v1.json",
    "conds.pt",
    "Cangjie5_TC.json",
]

# ---------------------------------------------------------------------------
# Dialect → Chatterbox language-code + reference audio mapping
# ---------------------------------------------------------------------------
# Keys are ISO 639-1 + region codes used by the dialect router.
# "code" is the Chatterbox backbone's internal language identifier.
# "ref"  is the path to the speaker reference audio; paths are relative to
#         the project root.  Symlink or copy your own .wav/.flac files there.
#
# Note: The Chatterbox backbone was originally trained on multilingual data,
# so non-Arabic ISO codes (e.g. "ms", "sv") are repurposed here as dialect
# identifiers — this is intentional and not a bug.

LANGUAGE_CODES: dict[str, dict[str, str]] = {
    "eg": {"code": "ms", "ref": "./wavs/ar_prompts2.flac"},        # Egyptian
    "sa": {"code": "sv", "ref": "./wavs/saudi.wav"},            # Saudi
    "mo": {"code": "pl", "ref": "./wavs/mor-enhanced.wav"},     # Moroccan
    "iq": {"code": "no", "ref": "./wavs/iraqi-enhanced.wav"},   # Iraqi
    "sd": {"code": "pt", "ref": "./wavs/sud-ref.wav"},        # Sudanese 
    "tn": {"code": "da", "ref": "./wavs/tun-ref.wav"},          # Tunisian
    "lb": {"code": "nl", "ref": "./wavs/leb-ref.wav"},          # Lebanese
    "sy": {"code": "ko", "ref": "./wavs/syrian-ref.wav"},       # Syrian
    "ly": {"code": "sw", "ref": "./wavs/lib-ref.wav"},          # Libyan
    "ps": {"code": "he", "ref": "./wavs/pal-ref.wav"},          # Palestinian
    "ar": {"code": "ar", "ref": "./wavs/ar_prompts2.flac"},     # MSA / fallback
}

# ---------------------------------------------------------------------------
# Generation defaults
# ---------------------------------------------------------------------------

DEFAULT_GENERATION_KWARGS: dict[str, float] = {
    "exaggeration": 0.5,  # Prosody expressiveness [0, 1]
    "temperature": 0.8,   # Sampling temperature
    "cfg_weight": 0.5,    # Classifier-free guidance weight
}