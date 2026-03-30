# PDF Translation Tool - Output Directory Fix Implementation Plan

## [ ] Task 1: Modify translation_service.py to accept custom output directory
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - Update the `process_translation_sync` method to accept an optional `output_path` parameter
  - Modify the `generate_pdf_output`, `generate_docx_output`, and `generate_markdown_output` methods to accept and use this custom path
  - Update the file path construction logic in each output generation method to use the custom directory instead of `config.OUTPUT_FOLDER`
  - Ensure backward compatibility when no output path is specified
- **Acceptance Criteria Addressed**: AC-1, AC-2
- **Test Requirements**:
  - `programmatic` TR-1.1: When output_path is provided, files should be generated directly in that directory
  - `programmatic` TR-1.2: When output_path is not provided, files should be generated in the default outputs directory
- **Notes**: The output_path parameter should be the full path to the output file, not just the directory

## [ ] Task 2: Update translate_command.py to pass custom output directory
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - Modify the `translate_handler` function to pass the full output_path to `process_translation_sync`
  - Remove the file copying logic that currently copies from default directory to user-specified location
  - Keep the directory creation logic to ensure the output directory exists
- **Acceptance Criteria Addressed**: AC-1, AC-4
- **Test Requirements**:
  - `programmatic` TR-2.1: CLI command with -o parameter should generate files directly in specified directory
  - `programmatic` TR-2.2: CLI command without -o parameter should use default outputs directory
  - `programmatic` TR-2.3: Non-existent output directories should be created automatically
- **Notes**: The output_path parameter should be the full path to the output file, which is already constructed in the translate_handler function

## [ ] Task 3: Verify glossary_command.py output directory behavior
- **Priority**: P1
- **Depends On**: None
- **Description**: 
  - Verify that the `glossary_handler` function already correctly uses the user-specified output directory
  - Ensure glossary files are generated directly in the specified directory without copying
  - Confirm that the default behavior (using current working directory when no output path is specified) is maintained
- **Acceptance Criteria Addressed**: AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-3.1: glossary command with -o parameter should generate files directly in specified directory
  - `programmatic` TR-3.2: glossary command without -o parameter should use current directory
  - `programmatic` TR-3.3: Non-existent output directories should be created automatically
- **Notes**: The glossary command already seems to have the correct behavior, but need to verify and ensure consistency with the translate command fix

## [ ] Task 4: Test the fix with various scenarios
- **Priority**: P1
- **Depends On**: Tasks 1, 2, 3
- **Description**: 
  - Test the fix with different output formats (PDF, DOCX, Markdown)
  - Test with custom output directories
  - Test with non-existent output directories
  - Test without specifying output directory (backward compatibility)
  - Test the glossary command with custom output directory
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-4.1: All output formats should work with custom directories
  - `programmatic` TR-4.2: Backward compatibility should be maintained
  - `programmatic` TR-4.3: Directory creation should work correctly
  - `programmatic` TR-4.4: Glossary command should work with custom directories
- **Notes**: Run comprehensive tests to ensure the fix works in all scenarios

## [ ] Task 5: Update documentation if necessary
- **Priority**: P2
- **Depends On**: Tasks 1, 2, 3, 4
- **Description**: 
  - Check if any documentation needs to be updated to reflect the changes
  - Update README.md or other documentation if necessary
- **Acceptance Criteria Addressed**: None (documentation update)
- **Test Requirements**:
  - `human-judgment` TR-5.1: Documentation should accurately reflect the current behavior
- **Notes**: Minimal documentation changes expected as the user interface remains the same
