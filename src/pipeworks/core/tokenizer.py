"""Tokenizer utility for analyzing prompts.

This module provides the TokenizerAnalyzer class, which loads and uses the
tokenizer from the Z-Image-Turbo model to analyze text prompts. This helps
users understand how their prompts will be processed by the model.

Tokenization Analysis
---------------------
The analyzer provides insights into how text is converted to tokens:
- **Token Count**: Number of tokens in the prompt (important for model limits)
- **Token List**: Individual tokens extracted from the prompt
- **Token IDs**: Numeric IDs for each token
- **Special Tokens**: Identification of special tokens (BOS, EOS, etc.)

Why Tokenization Matters
-------------------------
Understanding tokenization helps users:
1. Stay within model token limits (typically 77 or 256 tokens)
2. Understand how the model "sees" their prompt
3. Debug unexpected generation results
4. Optimize prompts for efficiency and clarity

Different models tokenize text differently based on their training data.
For example:
- "photo" might be one token
- "photograph" might be split into ["photo", "graph"]
- "hyperrealistic" might be ["hyper", "realistic"] or a single token

Lazy Loading
------------
The tokenizer is loaded lazily (on first analysis) to avoid unnecessary
downloads and memory usage. The tokenizer files (~500MB) are downloaded
from HuggingFace and cached locally.

Usage Example
-------------
Basic usage:

    >>> from pipeworks.core.tokenizer import TokenizerAnalyzer
    >>> analyzer = TokenizerAnalyzer()
    >>>
    >>> # Analyze a prompt
    >>> result = analyzer.analyze("a beautiful landscape, photorealistic")
    >>> print(f"Token count: {result['token_count']}")
    Token count: 8
    >>> print(f"Tokens: {result['tokens']}")
    Tokens: ['a', 'beautiful', 'landscape', ',', 'photo', 'realistic']
    >>>
    >>> # Get formatted output
    >>> formatted = analyzer.format_tokens(result['tokens'])
    >>> print(formatted)
    'a' | 'beautiful' | 'landscape' | ',' | 'photo' | 'realistic'

Integration with UI
-------------------
The tokenizer integrates with the Gradio UI to provide live feedback
as users construct prompts, showing:
- Current token count
- Visual breakdown of tokens
- Warnings if approaching token limits

See Also
--------
- transformers.AutoTokenizer: HuggingFace tokenizer documentation
- ui/handlers.py: Tokenizer UI integration
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class TokenizerAnalyzer:
    """Lightweight tokenizer analyzer for Z-Image-Turbo prompts.

    This class wraps the HuggingFace tokenizer for the Z-Image-Turbo model,
    providing a simple interface for analyzing text prompts. It implements
    lazy loading to avoid unnecessary resource usage.

    The analyzer helps users understand how their prompts are tokenized,
    which is important for:
    - Staying within model token limits
    - Understanding model behavior
    - Optimizing prompt efficiency

    Attributes
    ----------
    model_id : str
        HuggingFace model identifier
    cache_dir : Path | None
        Directory to cache tokenizer files
    tokenizer : AutoTokenizer | None
        HuggingFace tokenizer instance (None until loaded)
    _loaded : bool
        Whether tokenizer has been loaded

    Notes
    -----
    - Tokenizer files (~500MB) are downloaded from HuggingFace on first use
    - Subsequent uses load from cache in config.models_dir
    - Loading typically takes 5-10 seconds on first run
    - The tokenizer is shared across all analyzer instances with same model_id

    Examples
    --------
    Create analyzer and analyze text:

        >>> analyzer = TokenizerAnalyzer()
        >>> result = analyzer.analyze("a wizard in a forest")
        >>> print(result['token_count'])
        6
        >>> print(result['tokens'])
        ['a', 'wizard', 'in', 'a', 'forest']

    Check tokenizer info:

        >>> info = analyzer.get_info()
        >>> print(info['vocab_size'])
        49408
        >>> print(info['model_max_length'])
        77
    """

    def __init__(self, model_id: str = "Tongyi-MAI/Z-Image-Turbo", cache_dir: Path | None = None):
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

    def analyze(self, text: str) -> dict[str, any]:
        """Analyze a text prompt and return tokenization details.

        This method tokenizes the input text and provides detailed information
        about how the tokenizer breaks it down into tokens. This is useful for
        understanding prompt behavior and staying within model limits.

        Args:
            text: The text prompt to analyze

        Returns:
            Dictionary containing tokenization analysis:
            - token_count: Number of tokens (int)
            - tokens: List of decoded token strings (list[str])
            - token_ids: List of token IDs (list[int])
            - special_tokens: List of special tokens found (list[str])

        Notes:
            - Empty or whitespace-only text returns zero counts
            - Special tokens (BOS, EOS, PAD, etc.) are not added by default
            - Token count is important for model limits (typically 77 or 256)
            - Each token ID maps to a specific entry in the model's vocabulary

        Examples:
            >>> analyzer = TokenizerAnalyzer()
            >>> result = analyzer.analyze("a beautiful landscape")
            >>> print(result['token_count'])
            4
            >>> print(result['tokens'])
            ['a', 'beautiful', 'landscape']
        """
        # Lazy load tokenizer on first use
        if not self._loaded:
            self.load()

        # Handle empty input
        if not text or text.strip() == "":
            return {
                "token_count": 0,
                "tokens": [],
                "token_ids": [],
                "special_tokens": [],
            }

        # Tokenize the text using HuggingFace tokenizer
        # return_tensors="pt" returns PyTorch tensors
        # add_special_tokens=False excludes BOS/EOS tokens for cleaner analysis
        encoded = self.tokenizer(text, return_tensors="pt", add_special_tokens=False)
        token_ids = encoded["input_ids"][0].tolist()

        # Decode individual tokens back to strings
        # This helps users see how the text is split
        tokens = []
        special_tokens = []
        for token_id in token_ids:
            # Decode each token ID individually to get the token string
            token_str = self.tokenizer.decode([token_id])
            tokens.append(token_str)

            # Check if this token is a special token (BOS, EOS, PAD, UNK, etc.)
            if token_str in self.tokenizer.all_special_tokens:
                special_tokens.append(token_str)

        return {
            "token_count": len(token_ids),
            "tokens": tokens,
            "token_ids": token_ids,
            "special_tokens": special_tokens,
        }

    def format_tokens(self, tokens: list[str]) -> str:
        """
        Format tokens for display with visual separators.

        Args:
            tokens: List of token strings

        Returns:
            Formatted string with tokens separated by markers
        """
        # Use | as separator and wrap each token
        return " | ".join([f"'{token}'" for token in tokens])

    def get_info(self) -> dict[str, any]:
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
