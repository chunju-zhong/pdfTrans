# LLM Token Truncation Warning - Product Requirement Document

## Overview
- **Summary**: Implement a feature to detect LLM token truncation during translation and Markdown generation, and notify the frontend with detailed warnings while continuing the process.
- **Purpose**: To ensure users are aware when LLM responses are truncated due to token limits, allowing them to take appropriate action if needed, while maintaining the integrity of the overall process.
- **Target Users**: Users of the PDF translation tool who need to process large documents or sections that may exceed LLM token limits.

## Goals
- Detect when LLM responses are truncated during translation and Markdown generation
- Send detailed warning notifications to the frontend when truncation occurs
- Continue the entire process despite truncation

## Non-Goals (Out of Scope)
- Increasing LLM token limits
- Modifying the processes to avoid truncation
- Changing the LLM models or providers
- Detecting truncation during semantic analysis merging

## Background & Context
- The PDF translation tool uses LLM models (aiping and silicon_flow) for multiple purposes:
  - Translation of text blocks
  - Semantic analysis for block merging
  - Markdown generation with layout analysis
- These models have token limits that may be exceeded by large text blocks
- When responses are truncated, users may not be aware that some content was lost
- The current implementation does not check for or notify users about truncation in any of these processes
- Semantic analysis merging is excluded from truncation detection per user request

## Functional Requirements
- **FR-1**: Modify translator implementations to capture token usage and truncation information from LLM responses
- **FR-2**: Update Markdown generator implementations to capture token usage and truncation information
- **FR-3**: Update the translation service to detect truncation and generate detailed warnings
- **FR-4**: Pass warning information to the frontend for user notification
- **FR-5**: Continue all processes even when truncation occurs
- **FR-6**: Provide detailed warning messages that include context about where truncation occurred

## Non-Functional Requirements
- **NFR-1**: The feature should not impact performance of any process (translation, Markdown generation)
- **NFR-2**: The feature should be compatible with both aiping and silicon_flow services
- **NFR-3**: Warning messages should be clear, informative, and include context
- **NFR-4**: The feature should not interrupt the execution of any process

## Constraints
- **Technical**: Limited by the token information provided by the LLM APIs
- **Dependencies**: Requires access to token usage and truncation information from the OpenAI API response

## Assumptions
- The OpenAI API returns token usage and truncation information in its response
- The frontend has the capability to display warning messages to users
- Truncation is rare but possible for large text blocks
- LLM-based processes (translation, Markdown generation) return similar token usage information

## Acceptance Criteria

### AC-1: Token Truncation Detection in Translation
- **Given**: A large text block that exceeds the LLM token limit
- **When**: The translation API is called
- **Then**: The system detects that the response was truncated
- **Verification**: `programmatic`

### AC-2: Token Truncation Detection in Markdown Generation
- **Given**: A large text block that exceeds the LLM token limit
- **When**: The Markdown generation API is called
- **Then**: The system detects that the response was truncated
- **Verification**: `programmatic`

### AC-3: Warning Notification
- **Given**: The system detects a truncated LLM response in any process
- **When**: The process continues
- **Then**: A detailed warning is sent to the frontend
- **Verification**: `programmatic`

### AC-4: Process Continuation
- **Given**: A truncated LLM response in any process
- **When**: The system detects the truncation
- **Then**: The process continues with the partial response
- **Verification**: `programmatic`



### AC-6: Detailed Warning Messages
- **Given**: The system detects a truncated LLM response
- **When**: A warning is generated
- **Then**: The warning includes details about which process was affected and the context of the truncation
- **Verification**: `human-judgment`

## Open Questions
- [ ] Where in the frontend should the warning be displayed?

## Token Information Available from LLM Providers

### Aiping API Response Format
Based on the Aiping API documentation, the response includes a `usage` field with the following token information:
- `prompt_tokens`: Number of tokens in the prompt
- `completion_tokens`: Number of tokens in the completion
- `total_tokens`: Total number of tokens used
- `prompt_tokens_details`: Optional details about prompt tokens (e.g., cached tokens)
- `completion_tokens_details`: Optional details about completion tokens (e.g., reasoning tokens)

### Silicon Flow API Response Format
Based on the OpenAI-compatible API format that Silicon Flow uses, the response includes a `usage` field with the following token information:
- `prompt_tokens`: Number of tokens in the prompt
- `completion_tokens`: Number of tokens in the completion
- `total_tokens`: Total number of tokens used

### Truncation Detection
Both APIs include a `finish_reason` field in the response, which will be set to "length" when the response was truncated due to token limits. This is consistent with the OpenAI API specification that Silicon Flow follows.

### API Response Structure
The API response from both providers follows this structure:
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Translated text..."
      },
      "finish_reason": "length"  // This indicates truncation
    }
  ],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 200,
    "total_tokens": 300
  }
}
```

### Implementation Details
To implement token truncation detection for both Aiping and Silicon Flow:
1. Capture the `usage` field from the API response to get token usage information
2. Check the `finish_reason` field - if it's "length", the response was truncated
3. Generate a warning with detailed token usage information
4. Continue processing with the partial response
5. Pass the warning to the frontend for user notification



## Warning Message Format

### Backend Warning Format
Warnings should be structured as objects with the following properties:
- `message`: A detailed message about the truncation
- `severity`: Level of severity (e.g., "warning")
- `context`: Additional context about where the truncation occurred
  - `process`: Which process was affected (e.g., "translation", "markdown_generation")
  - `block_id`: Identifier of the block being processed
  - `token_usage`: Token usage information
    - `prompt_tokens`: Number of tokens in the prompt
    - `completion_tokens`: Number of tokens in the completion
    - `total_tokens`: Total number of tokens used

### Frontend Warning Display
Warnings should be displayed as non-blocking notifications with the following information:
- A clear warning icon and title
- Detailed message explaining that the LLM response was truncated
- Context about which process was affected
- Information about the token usage
- A suggestion to split large documents or sections if truncation occurs frequently