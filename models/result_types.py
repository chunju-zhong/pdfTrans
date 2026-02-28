"""Result type classes for translation and Markdown generation results."""


class TruncationInfo:
    """Truncation information model."""

    def __init__(self, truncated=False, token_usage=None, finish_reason=None):
        """Initialize a TruncationInfo instance.

        Args:
            truncated: Whether the result was truncated
            token_usage: Dictionary containing token usage information
            finish_reason: The reason the model stopped generating text
        """
        self.truncated = truncated
        self.token_usage = token_usage or {}
        self.finish_reason = finish_reason


class Result:
    """Base result class with common fields."""

    def __init__(self, content, truncation_info=None):
        """Initialize a Result instance.

        Args:
            content: The result content (e.g., translated text, generated Markdown)
            truncation_info: TruncationInfo instance containing truncation information
        """
        self.content = content
        self.truncation_info = truncation_info or TruncationInfo()


class OpenAIResult(Result):
    """Result class for OpenAI-compatible API responses."""

    def __init__(self, content, token_usage=None, finish_reason=None, truncation_info=None):
        """Initialize an OpenAIResult instance.

        Args:
            content: The result content
            token_usage: Dictionary containing token usage information
            finish_reason: The reason the model stopped generating text
            truncation_info: TruncationInfo instance containing truncation information
        """
        # If truncation_info is provided, use it; otherwise create a new one
        if truncation_info is None:
            truncated = finish_reason == "length"
            truncation_info = TruncationInfo(truncated=truncated, token_usage=token_usage, finish_reason=finish_reason)
        
        super().__init__(content, truncation_info)
        self.token_usage = token_usage or {}
        self.finish_reason = finish_reason

    @property
    def truncated(self):
        """Check if the result was truncated."""
        return self.truncation_info.truncated


class TranslationResult(OpenAIResult):
    """Result class for translation results."""

    def __init__(self, content, token_usage=None, finish_reason=None, truncation_info=None):
        """Initialize a TranslationResult instance.

        Args:
            content: The translated text
            token_usage: Dictionary containing token usage information
            finish_reason: The reason the model stopped generating text
            truncation_info: Dictionary containing truncation information
        """
        super().__init__(content, token_usage, finish_reason, truncation_info)


class MarkdownResult(OpenAIResult):
    """Result class for Markdown generation results."""

    def __init__(self, content, token_usage=None, finish_reason=None, truncation_info=None):
        """Initialize a MarkdownResult instance.

        Args:
            content: The generated Markdown
            token_usage: Dictionary containing token usage information
            finish_reason: The reason the model stopped generating text
            truncation_info: Dictionary containing truncation information
        """
        super().__init__(content, token_usage, finish_reason, truncation_info)
