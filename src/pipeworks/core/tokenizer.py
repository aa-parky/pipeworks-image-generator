"""Tokenizer utility for analyzing prompts."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class TokenizerAnalyzer:
    """Lightweight tokenizer analyzer for Z-Image-Turbo prompts."""

    def __init__(self, model_id: str = "Tongyi-MAI/Z-Image-Turbo", cache_dir: Optional[Path] = None):
        """
        Initialize the tokenizer analyzer.

        Args:
            model_id: HuggingFace model ID
            cache_dir: Directory to cache tokenizer files
        """
        self.model_id = model_id
        self.cache_dir = cache_dir
        self.tokenizer = None
        self._loaded = False

    def load(self) -> None:
        """Load the tokenizer (lazy loading)."""
        if self._loaded:
            return

        try:
            from transformers import AutoTokenizer

            logger.info(f"Loading tokenizer from {self.model_id}...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_id,
                subfolder="tokenizer",
                cache_dir=str(self.cache_dir) if self.cache_dir else None,
                trust_remote_code=True,
            )
            self._loaded = True
            logger.info("Tokenizer loaded successfully!")

        except Exception as e:
            logger.error(f"Failed to load tokenizer: {e}")
            raise

    def analyze(self, text: str) -> Dict[str, any]:
        """
        Analyze a text prompt and return tokenization details.

        Args:
            text: The text prompt to analyze

        Returns:
            Dictionary containing tokenization analysis:
            - token_count: Number of tokens
            - tokens: List of decoded tokens
            - token_ids: List of token IDs
            - special_tokens: List of special tokens found
        """
        if not self._loaded:
            self.load()

        if not text or text.strip() == "":
            return {
                "token_count": 0,
                "tokens": [],
                "token_ids": [],
                "special_tokens": [],
            }

        # Tokenize the text
        encoded = self.tokenizer(text, return_tensors="pt", add_special_tokens=False)
        token_ids = encoded["input_ids"][0].tolist()

        # Decode individual tokens
        tokens = []
        special_tokens = []
        for token_id in token_ids:
            token_str = self.tokenizer.decode([token_id])
            tokens.append(token_str)

            # Check if it's a special token
            if token_str in self.tokenizer.all_special_tokens:
                special_tokens.append(token_str)

        return {
            "token_count": len(token_ids),
            "tokens": tokens,
            "token_ids": token_ids,
            "special_tokens": special_tokens,
        }

    def format_tokens(self, tokens: List[str]) -> str:
        """
        Format tokens for display with visual separators.

        Args:
            tokens: List of token strings

        Returns:
            Formatted string with tokens separated by markers
        """
        # Use | as separator and wrap each token
        return " | ".join([f"'{token}'" for token in tokens])

    def get_info(self) -> Dict[str, any]:
        """
        Get tokenizer information.

        Returns:
            Dictionary with tokenizer metadata
        """
        if not self._loaded:
            self.load()

        return {
            "name": self.tokenizer.__class__.__name__,
            "vocab_size": self.tokenizer.vocab_size,
            "model_max_length": self.tokenizer.model_max_length,
            "special_tokens": self.tokenizer.all_special_tokens,
        }
