# PDF Translation Tool - Image Extraction Fix

## Overview
- **Summary**: Fix the image extraction permission issue in sandbox mode by modifying the temporary image directory location to use a writable path.
- **Purpose**: To ensure the PDF translation tool can extract images successfully in sandboxed environments where the project root directory may have restricted write permissions.
- **Target Users**: Users running the PDF translation tool in sandboxed environments or other restricted permission contexts.

## Goals
- Modify the temporary image directory location to use a writable path
- Ensure the fix works for both default and custom output directories
- Maintain backward compatibility
- Resolve permission errors during image extraction in sandbox mode

## Non-Goals (Out of Scope)
- Changing the image extraction functionality itself
- Modifying other parts of the PDF extraction process
- Altering the overall architecture of the tool

## Background & Context
- The current implementation hardcodes the temporary image directory to `temp_images/` in the project root
- This causes permission errors in sandboxed environments where the project root may not be writable
- The fix should use a temporary directory that is guaranteed to be writable, preferably in the same directory as the output file

## Functional Requirements
- **FR-1**: The temporary image directory should be created in a writable location
- **FR-2**: When a custom output directory is specified, the temporary image directory should be created in the same directory
- **FR-3**: When no output directory is specified, the temporary image directory should be created in the default `outputs/` directory

## Non-Functional Requirements
- **NFR-1**: The fix should maintain backward compatibility
- **NFR-2**: The fix should not impact performance
- **NFR-3**: The fix should be minimal and focused on the specific issue

## Constraints
- **Technical**: Must work with the existing codebase structure and dependencies
- **Dependencies**: No new dependencies required

## Assumptions
- The user has write permissions to the specified output directory
- The output directory exists or can be created

## Acceptance Criteria

### AC-1: Sandbox Mode Image Extraction
- **Given**: The tool is running in a sandboxed environment with restricted write permissions to the project root
- **When**: The user runs a translation command with image extraction
- **Then**: The tool should successfully extract images without permission errors
- **Verification**: `programmatic`

### AC-2: Custom Output Directory
- **Given**: The user specifies a custom output directory
- **When**: The tool extracts images
- **Then**: The temporary image directory should be created in the custom output directory
- **Verification**: `programmatic`

### AC-3: Default Output Directory
- **Given**: No custom output directory is specified
- **When**: The tool extracts images
- **Then**: The temporary image directory should be created in the default `outputs/` directory
- **Verification**: `programmatic`



## Open Questions
- [x] How to pass the output directory information to the image extraction process
  - **Answer**: The output directory information can be passed through the following steps:
    1. Modify the `extract_pdf_content` method in `translation_service.py` to accept an optional `output_path` parameter
    2. Pass this parameter from `process_translation_sync` when calling `extract_pdf_content`
    3. Update the `pdf_extractor.extract` method to accept a `temp_images_dir` parameter
    4. Create the temporary image directory within the output path when provided

- [x] What is the best way to determine a writable temporary directory
  - **Answer**: The best approach is:
    - When a custom output directory is specified, use that directory for temporary images
    - When no output directory is specified, use the default `outputs/` directory
    - Ensure the directory exists by creating it if necessary
    - This ensures we're using a directory the user has already specified and presumably has write permissions to

- [x] How to handle edge cases where no writable directory is available
  - **Answer**: To handle edge cases:
    - Add error handling to catch permission errors when creating the temporary directory
    - If the specified directory is not writable, try to use a system temporary directory
    - If all else fails, raise a clear error message indicating the permission issue
    - Log detailed error information for debugging
