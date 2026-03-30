# PDF Translation Tool - Image Extraction Fix Implementation Plan

## [x] Task 1: Modify pdf_extractor.py to accept custom temp_images_dir parameter
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - Update the `extract` method in `pdf_extractor.py` to accept an optional `temp_images_dir` parameter
  - Modify the `_extract_images` method to use this parameter when provided
  - Ensure backward compatibility by using the current hardcoded path as default
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3
- **Test Requirements**:
  - `programmatic` TR-1.1: When temp_images_dir is provided, images should be extracted to that directory
  - `programmatic` TR-1.2: When temp_images_dir is not provided, images should be extracted to the default location
- **Notes**: Need to ensure the directory is created if it doesn't exist

## [x] Task 2: Update translation_service.py to pass output directory to extract_pdf_content
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - Modify the `extract_pdf_content` method in `translation_service.py` to accept an optional `output_path` parameter
  - Pass this parameter to the `pdf_extractor.extract` method
  - Update the `process_translation_sync` method to pass the output_path when calling `extract_pdf_content`
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3
- **Test Requirements**:
  - `programmatic` TR-2.1: When output_path is provided, images should be extracted to a directory within the output path
  - `programmatic` TR-2.2: When output_path is not provided, images should be extracted to the default outputs directory
- **Notes**: Need to create the temporary image directory within the output directory



## [x] Task 3: Test the fix with various scenarios
- **Priority**: P1
- **Depends On**: Tasks 1, 2
- **Description**: 
  - Test image extraction with custom output directory
  - Test image extraction with default output directory
  - Test in a simulated sandbox environment with restricted permissions
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3
- **Test Requirements**:
  - `programmatic` TR-3.1: Image extraction works with custom output directory
  - `programmatic` TR-3.2: Image extraction works with default output directory
  - `programmatic` TR-3.3: No permission errors occur during image extraction
- **Notes**: Create a test PDF with images for testing

## [x] Task 4: Update documentation if necessary
- **Priority**: P2
- **Depends On**: Tasks 1, 2, 3
- **Description**: 
  - Check if any documentation needs to be updated to reflect the changes
  - Update README.md or other documentation if necessary
- **Acceptance Criteria Addressed**: None (documentation update)
- **Test Requirements**:
  - `human-judgment` TR-5.1: Documentation should accurately reflect the current behavior
- **Notes**: Minimal documentation changes expected
