# LLM Token Truncation Warning - Implementation Plan

## [ ] Task 1: Update AipingTranslator to capture token usage and truncation info
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - Modify the `translate` method in `AipingTranslator` to capture token usage and truncation information from the API response
  - Update the method to return both the translated text and truncation status
- **Acceptance Criteria Addressed**: AC-1, AC-6
- **Test Requirements**:
  - `programmatic` TR-1.1: Verify that the translator captures token usage information
  - `programmatic` TR-1.2: Verify that the translator detects when a response is truncated
- **Notes**: The OpenAI API response includes `usage` and `finish_reason` fields that can be used to detect truncation

## [ ] Task 2: Update SiliconFlowTranslator to capture token usage and truncation info
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - Modify the `translate` method in `SiliconFlowTranslator` to capture token usage and truncation information from the API response
  - Update the method to return both the translated text and truncation status
- **Acceptance Criteria Addressed**: AC-1, AC-6
- **Test Requirements**:
  - `programmatic` TR-2.1: Verify that the translator captures token usage information
  - `programmatic` TR-2.2: Verify that the translator detects when a response is truncated
- **Notes**: The SiliconFlow API uses the same OpenAI format, so it should return similar token usage information

## [ ] Task 3: Update Markdown generator implementations to capture token usage and truncation info
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - Modify the Markdown generator implementations to capture token usage and truncation information from LLM responses
  - Update the methods to return both the generated Markdown and truncation status
- **Acceptance Criteria Addressed**: AC-2, AC-5
- **Test Requirements**:
  - `programmatic` TR-3.1: Verify that the Markdown generator captures token usage information
  - `programmatic` TR-3.2: Verify that the Markdown generator detects when a response is truncated
- **Notes**: Markdown generators use the same OpenAI API format, so they should return similar token usage information

## [ ] Task 4: Update TranslationService to handle truncation warnings
- **Priority**: P0
- **Depends On**: Task 1, Task 2, Task 3
- **Description**:
  - Update the `process_merged_blocks`, `process_original_blocks`, and other methods to handle truncation information from translation and Markdown generation processes
  - Modify the methods to collect warnings when truncation occurs
  - Update the task object to store and track warnings with detailed context
- **Acceptance Criteria Addressed**: AC-3, AC-4, AC-6
- **Test Requirements**:
  - `programmatic` TR-4.1: Verify that the service detects truncation warnings from translation and Markdown generation processes
  - `programmatic` TR-4.2: Verify that the service continues processing despite truncation
  - `programmatic` TR-4.3: Verify that warnings are stored in the task object with detailed context
- **Notes**: The service should collect warnings and associate them with specific processes and blocks

## [ ] Task 5: Update task model to support warnings
- **Priority**: P1
- **Depends On**: None
- **Description**:
  - Update the task model to include a warnings property
  - Add methods to add and retrieve warnings
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `programmatic` TR-5.1: Verify that the task model can store warnings
- **Notes**: The warnings should be stored as a list of warning objects with message, severity, and context information

## [ ] Task 6: Update frontend to display truncation warnings
- **Priority**: P1
- **Depends On**: Task 4, Task 5
- **Description**:
  - Update the frontend to check for warnings in task status updates
  - Add UI components to display warning messages with detailed context
  - Ensure warnings are prominently displayed but don't block the user interface
- **Acceptance Criteria Addressed**: AC-3, AC-6
- **Test Requirements**:
  - `human-judgment` TR-6.1: Verify that warnings are clearly displayed in the frontend
  - `human-judgment` TR-6.2: Verify that the warning message is informative and includes context
- **Notes**: The frontend should display warnings as non-blocking notifications

## [ ] Task 7: Test the complete feature
- **Priority**: P0
- **Depends On**: All previous tasks
- **Description**:
  - Create test cases with large text blocks that exceed token limits for translation and Markdown generation processes
  - Verify that truncation is detected and warnings are generated for each process
  - Test with both aiping and silicon_flow services
  - Verify that all processes complete despite truncation
  - Verify that warnings are correctly passed from backend to frontend
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4, AC-5, AC-6
- **Test Requirements**:
  - `programmatic` TR-7.1: Verify the complete end-to-end flow with truncated responses for translation
  - `programmatic` TR-7.2: Verify the complete end-to-end flow with truncated responses for Markdown generation
  - `programmatic` TR-7.3: Verify that warnings are correctly passed from backend to frontend
  - `programmatic` TR-7.4: Verify that existing functionality remains intact
- **Notes**: Test with different text sizes to ensure the feature works correctly across various scenarios