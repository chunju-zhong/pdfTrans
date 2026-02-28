# Refactor Truncation Info to Model - Implementation Plan

## Overview

Refactor the `truncation_info` field in the result types from a dictionary to a dedicated model class for better type safety and code clarity.

## \[ ] Task 1: Create TruncationInfo Model Class

* **Priority**: P0

* **Depends On**: None

* **Description**:

  * Create a new `TruncationInfo` class in `result_types.py`

  * Define fields for `truncated` (bool), `token_usage` (dict), and `finish_reason` (str)

  * Add appropriate initialization and properties

* **Success Criteria**:

  * `TruncationInfo` class is defined with all necessary fields

  * Class is properly documented

* **Test Requirements**:

  * `programmatic` TR-1.1: Verify that `TruncationInfo` can be instantiated with required fields

  * `human-judgement` TR-1.2: Verify that class definition is clear and well-documented

* **Notes**: The class should provide a clean way to represent truncation information

## \[ ] Task 2: Update Result Class to Use TruncationInfo

* **Priority**: P0

* **Depends On**: Task 1

* **Description**:

  * Modify the `Result` class to accept a `TruncationInfo` instance instead of a dictionary

  * Update the `__init__` method signature and implementation

* **Success Criteria**:

  * `Result` class now uses `TruncationInfo` instead of dictionary for `truncation_info`

  * Backward compatibility is maintained if needed

* **Test Requirements**:

  * `programmatic` TR-2.1: Verify that `Result` can be instantiated with a `TruncationInfo` instance

  * `programmatic` TR-2.2: Verify that `Result` still works with the updated implementation

* **Notes**: Ensure that existing code that creates `Result` instances is updated

## \[ ] Task 3: Update OpenAIResult Class

* **Priority**: P0

* **Depends On**: Task 2

* **Description**:

  * Update the `OpenAIResult` class to work with the new `TruncationInfo` model

  * Ensure that the `truncated` property still works correctly

* **Success Criteria**:

  * `OpenAIResult` properly handles `TruncationInfo`

  * `truncated` property returns correct value

* **Test Requirements**:

  * `programmatic` TR-3.1: Verify that `OpenAIResult` can be instantiated with `TruncationInfo`

  * `programmatic` TR-3.2: Verify that `truncated` property works correctly

* **Notes**: Check that the `finish_reason` field is properly used

## \[ ] Task 4: Update Translators to Use TruncationInfo

* **Priority**: P0

* **Depends On**: Task 3

* **Description**:

  * Update `AipingTranslator` to create `TruncationInfo` instances instead of dictionaries

  * Update `SiliconFlowTranslator` to create `TruncationInfo` instances instead of dictionaries

* **Success Criteria**:

  * Both translators now return results with `TruncationInfo` instances

  * Translators continue to work correctly

* **Test Requirements**:

  * `programmatic` TR-4.1: Verify that `AipingTranslator.translate()` returns `TranslationResult` with `TruncationInfo`

  * `programmatic` TR-4.2: Verify that `SiliconFlowTranslator.translate()` returns `TranslationResult` with `TruncationInfo`

* **Notes**: Update both `translate` and `batch_translate` methods

## \[ ] Task 5: Update Markdown Generator to Use TruncationInfo

* **Priority**: P0

* **Depends On**: Task 3

* **Description**:

  * Update `MarkdownGenerator` to create `TruncationInfo` instances instead of dictionaries

  * Ensure that the `generate_markdown` method returns `MarkdownResult` with `TruncationInfo`

* **Success Criteria**:

  * `MarkdownGenerator.generate_markdown()` returns `MarkdownResult` with `TruncationInfo`

  * Markdown generation continues to work correctly

* **Test Requirements**:

  * `programmatic` TR-5.1: Verify that `generate_markdown()` returns `MarkdownResult` with `TruncationInfo`

* **Notes**: Update both `_format_with_layout_model` and `_call_api` methods

## \[ ] Task 6: Update TranslationService to Use TruncationInfo

* **Priority**: P0

* **Depends On**: Tasks 4, 5

* **Description**:

  * Update `TranslationService` to work with `TruncationInfo` instances instead of dictionaries

  * Update methods that check for truncation and generate warnings

* **Success Criteria**:

  * `TranslationService` correctly processes `TruncationInfo` from translators and Markdown generator

  * Warnings are still generated correctly for truncated results

* **Test Requirements**:

  * `programmatic` TR-6.1: Verify that `TranslationService` correctly extracts truncation info from result objects

  * `programmatic` TR-6.2: Verify that warnings are generated for truncated results

* **Notes**: Update `process_merged_blocks`, `process_original_blocks`, `translate_tables`, and `generate_output_files` methods

## \[ ] Task 7: Update Tests to Use TruncationInfo

* **Priority**: P1

* **Depends On**: All previous tasks

* **Description**:

  * Update all tests that create or use `truncation_info` to use the new `TruncationInfo` model

  * Update mock implementations to return `TruncationInfo` instances

* **Success Criteria**:

  * All tests pass with the new `TruncationInfo` model

* **Test Requirements**:

  * `programmatic` TR-7.1: Verify that all tests pass

* **Notes**: Update tests in `test_aiping_translator.py`, `test_silicon_flow_translator.py`, `test_translator.py`, `test_performance_multithread.py`, and `test_thread_safety.py`

## \[ ] Task 8: Test the Complete Implementation

* **Priority**: P0

* **Depends On**: All previous tasks

* **Description**:

  * Run the complete test suite to ensure all functionality works correctly

  * Verify that token truncation warnings still work as expected

* **Success Criteria**:

  * All 144 tests pass

  * Token truncation warnings are still generated and displayed correctly

* **Test Requirements**:

  * `programmatic` TR-8.1: Verify that all tests pass

  * `human-judgement` TR-8.2: Verify that the code is more readable with the new model

* **Notes**: Test with both aiping and silicon\_flow services to ensure compatibility

