"""
Lahgtna TTS — Arabic Dialect-Aware Text-to-Speech Inference
============================================================
Detects the Arabic dialect of the input text and synthesises speech using
the matching reference audio, via the Chatterbox Multilingual TTS backbone.

Usage
-----
    python inference.py --text "اه ياراسي الواحد دماغه وجعاه" --output output.wav

    # Override dialect detection
    python inference.py --text "..." --dialect eg --output egypt.wav

    # Tune generation parameters
    python inference.py --text "..." --exaggeration 0.9 --temperature 0.7 --cfg-weight 0.4
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import torch
import torchaudio as ta
from huggingface_hub import snapshot_download
from safetensors.torch import load_file as load_safetensors
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from chatterbox.mtl_tts import ChatterboxMultilingualTTS
from config import DEFAULT_GENERATION_KWARGS, LANGUAGE_CODES, MODEL_REPO_ID, ROUTER_MODEL_ID, SNAPSHOT_PATTERNS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Device helpers
# ---------------------------------------------------------------------------

def get_device() -> str:
    """Return 'cuda' when a GPU is available, otherwise 'cpu'."""
    return "cuda" if torch.cuda.is_available() else "cpu"


# ---------------------------------------------------------------------------
# Dialect router
# ---------------------------------------------------------------------------

class DialectRouter:
    """
    Thin wrapper around the dialect-classification model.

    The model maps Arabic text to one of the dialect codes defined in
    ``config.LANGUAGE_CODES``.  Falls back to ``"ar"`` (Modern Standard
    Arabic) when prediction fails.
    """

    FALLBACK = "ar"

    def __init__(self, model_id: str = ROUTER_MODEL_ID, device: str | None = None) -> None:
        self.device = device or get_device()
        logger.info("Loading dialect router from %s …", model_id)
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_id)
        self.model.to(self.device).eval()

    def predict(self, text: str) -> str:
        """Return the predicted dialect code for *text*."""
        try:
            inputs = self.tokenizer(
                text, return_tensors="pt", truncation=True, max_length=512
            ).to(self.device)
            with torch.no_grad():
                logits = self.model(**inputs).logits
            pred_id = int(torch.argmax(logits, dim=-1).item())
            label: str = self.model.config.id2label[pred_id]
            if label not in LANGUAGE_CODES:
                logger.warning(
                    "Predicted label '%s' not in LANGUAGE_CODES — falling back to '%s'.",
                    label,
                    self.FALLBACK,
                )
                return self.FALLBACK
            return label
        except Exception:
            logger.exception("Dialect prediction failed; defaulting to '%s'.", self.FALLBACK)
            return self.FALLBACK


# ---------------------------------------------------------------------------
# TTS engine
# ---------------------------------------------------------------------------

class TTSEngine:
    """
    Wraps the Chatterbox Multilingual TTS model and exposes a simple
    ``synthesise`` method.
    """

    def __init__(self, device: str | None = None, hf_token: str | None = None) -> None:
        self.device = device or get_device()
        self._load_model(hf_token=hf_token)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _download_checkpoint(self, hf_token: str | None) -> Path:
        logger.info("Downloading checkpoint from %s …", MODEL_REPO_ID)
        return Path(
            snapshot_download(
                repo_id=MODEL_REPO_ID,
                repo_type="model",
                revision="main",
                allow_patterns=SNAPSHOT_PATTERNS,
                token=hf_token,
            )
        )

    def _load_model(self, hf_token: str | None) -> None:
        ckpt_dir = self._download_checkpoint(hf_token)

        logger.info("Initialising ChatterboxMultilingualTTS …")
        self.model = ChatterboxMultilingualTTS.from_pretrained(device=self.device)

        t3_path = ckpt_dir / "t3_mtl23ls_v2.safetensors"
        logger.info("Loading T3 weights from %s …", t3_path)
        t3_state = load_safetensors(str(t3_path), device=self.device)
        self.model.t3.load_state_dict(t3_state)
        self.model.t3.to(self.device).eval()

        self.sample_rate: int = self.model.sr
        logger.info("Model ready — sample rate: %d Hz", self.sample_rate)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def synthesise(
        self,
        text: str,
        language_code: str,
        ref_audio_path: str | Path,
        exaggeration: float = DEFAULT_GENERATION_KWARGS["exaggeration"],
        temperature: float = DEFAULT_GENERATION_KWARGS["temperature"],
        cfg_weight: float = DEFAULT_GENERATION_KWARGS["cfg_weight"],
    ) -> torch.Tensor:
        """
        Generate speech for *text* and return a CPU waveform tensor.

        Parameters
        ----------
        text:
            Input text in the target dialect / language.
        language_code:
            Internal language code used by the Chatterbox backbone
            (e.g. ``"ms"`` for Egyptian Arabic, ``"ar"`` for MSA).
        ref_audio_path:
            Path to the reference audio file that sets the target voice.
        exaggeration:
            Controls prosody exaggeration (0 = flat, 1 = very expressive).
        temperature:
            Sampling temperature; higher values increase diversity.
        cfg_weight:
            Classifier-free guidance weight; higher values improve adherence
            to the language code at the cost of naturalness.

        Returns
        -------
        torch.Tensor
            1-D waveform on CPU, ready to be saved with :func:`torchaudio.save`.
        """
        wav = self.model.generate(
            text,
            language_id=language_code,
            audio_prompt_path=str(ref_audio_path),
            exaggeration=float(exaggeration),
            temperature=float(temperature),
            cfg_weight=float(cfg_weight),
        )
        return wav.cpu()


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(
    text: str,
    output_path: str | Path,
    dialect: str | None = None,
    exaggeration: float = DEFAULT_GENERATION_KWARGS["exaggeration"],
    temperature: float = DEFAULT_GENERATION_KWARGS["temperature"],
    cfg_weight: float = DEFAULT_GENERATION_KWARGS["cfg_weight"],
    hf_token: str | None = None,
) -> Path:
    """
    End-to-end pipeline: detect dialect → select reference audio → synthesise.

    Parameters
    ----------
    text:
        Arabic (or other supported language) input text.
    output_path:
        Destination ``.wav`` file.
    dialect:
        When provided, skips dialect detection and uses this code directly.
        Must be a key in ``config.LANGUAGE_CODES``.
    exaggeration / temperature / cfg_weight:
        Generation hyper-parameters forwarded to :class:`TTSEngine`.
    hf_token:
        Hugging Face access token (optional; reads ``HF_TOKEN`` env var if
        not supplied).

    Returns
    -------
    Path
        Resolved path of the written audio file.
    """
    hf_token = hf_token or os.getenv("HF_TOKEN")
    output_path = Path(output_path)

    # --- Dialect detection ---------------------------------------------------
    if dialect is not None:
        if dialect not in LANGUAGE_CODES:
            raise ValueError(
                f"Unknown dialect '{dialect}'. "
                f"Valid options: {sorted(LANGUAGE_CODES)}"
            )
        language_id = dialect
        logger.info("Using user-specified dialect: %s", language_id)
    else:
        router = DialectRouter()
        language_id = router.predict(text)
        logger.info("Detected dialect: %s", language_id)

    lang_cfg = LANGUAGE_CODES[language_id]
    ref_audio = Path(lang_cfg["ref"])
    if not ref_audio.exists():
        raise FileNotFoundError(
            f"Reference audio not found: {ref_audio}\n"
            "Make sure the ./wavs/ directory is present and populated."
        )

    # --- Synthesis -----------------------------------------------------------
    engine = TTSEngine(hf_token=hf_token)
    logger.info("Synthesising text (%d chars) …", len(text))
    wav = engine.synthesise(
        text,
        language_code=lang_cfg["code"],
        ref_audio_path=ref_audio,
        exaggeration=exaggeration,
        temperature=temperature,
        cfg_weight=cfg_weight,
    )

    # --- Save ----------------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ta.save(str(output_path), wav, engine.sample_rate)
    logger.info("Saved audio → %s", output_path)
    return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Arabic dialect-aware TTS inference.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--text", required=True, help="Input text to synthesise.")
    p.add_argument(
        "--output", default="output.wav", help="Path for the output WAV file."
    )
    p.add_argument(
        "--dialect",
        default=None,
        help=(
            "Force a specific dialect code (skips auto-detection). "
            f"Choices: {sorted(LANGUAGE_CODES)}"
        ),
    )
    p.add_argument(
        "--exaggeration",
        type=float,
        default=DEFAULT_GENERATION_KWARGS["exaggeration"],
        help="Prosody exaggeration level (0–1).",
    )
    p.add_argument(
        "--temperature",
        type=float,
        default=DEFAULT_GENERATION_KWARGS["temperature"],
        help="Sampling temperature.",
    )
    p.add_argument(
        "--cfg-weight",
        type=float,
        default=DEFAULT_GENERATION_KWARGS["cfg_weight"],
        dest="cfg_weight",
        help="Classifier-free guidance weight.",
    )
    p.add_argument(
        "--hf-token",
        default=None,
        help="Hugging Face token (falls back to HF_TOKEN env var).",
    )
    p.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity.",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        out = run_pipeline(
            text=args.text,
            output_path=args.output,
            dialect=args.dialect,
            exaggeration=args.exaggeration,
            temperature=args.temperature,
            cfg_weight=args.cfg_weight,
            hf_token=args.hf_token,
        )
        print(f"✓ Audio saved to: {out}")
    except (FileNotFoundError, ValueError) as exc:
        logger.error("%s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()