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


class MarkdownGenerationResult(Result):
    """Result class for Markdown generation results, including batch processing.
    
    This class is used to return aggregated results from Markdown generation,
    including both single Markdown and chapter-based Markdown generation.
    """

    def __init__(self, content="", chapter_results=None, warnings=None, truncation_info=None):
        """Initialize a MarkdownGenerationResult instance.

        Args:
            content: The main Markdown content (for single Markdown generation)
            chapter_results: List of chapter generation results
            warnings: List of warnings from the generation process
            truncation_info: TruncationInfo instance containing truncation information
        """
        super().__init__(content, truncation_info)
        self.chapter_results = chapter_results or []
        self.warnings = warnings or []

    def add_warning(self, message, context=None):
        """Add a warning to the result.

        Args:
            message: Warning message
            context: Additional context information
        """
        warning = {
            'message': message,
            'context': context or {}
        }
        self.warnings.append(warning)

    def add_chapter_result(self, chapter_number, chapter_title, success, error_message=None):
        """Add a chapter generation result.

        Args:
            chapter_number: Chapter number
            chapter_title: Chapter title
            success: Whether the chapter was generated successfully
            error_message: Error message if generation failed
        """
        chapter_result = {
            'chapter_number': chapter_number,
            'chapter_title': chapter_title,
            'success': success,
            'error_message': error_message
        }
        self.chapter_results.append(chapter_result)
