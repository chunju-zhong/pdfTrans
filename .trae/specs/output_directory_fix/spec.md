# PDF Translation Tool - Output Directory Fix

## Overview

* **Summary**: Fix the command-line mode output directory to use the user-specified directory instead of the default `outputs` directory, resolving write permission issues in sandbox mode.

* **Purpose**: To ensure the CLI tool can write output files to user-specified directories even when the default `outputs` directory has restricted permissions.

* **Target Users**: Users running the PDF translation tool in command-line mode, especially in sandboxed environments.

## Goals
- Modify the CLI translation process to use the user-specified output directory directly instead of the default `outputs` directory
- Ensure the fix works for all output formats (PDF, DOCX, Markdown)
- Maintain backward compatibility when no output directory is specified
- Resolve write permission issues in sandbox mode

## Non-Goals (Out of Scope)
- Changing the default output directory structure
- Modifying web interface functionality
- Altering the translation service API

## Background & Context
- The current implementation generates files in the default `outputs` directory first, then copies them to the user-specified location
- This causes write permission issues in sandboxed environments where the default directory might not be writable
- The fix should modify the translation service to respect the user-specified output directory directly

## Functional Requirements
- **FR-1**: When a user specifies an output path via the `-o` or `--output` parameter, the tool should generate files directly in the specified directory
- **FR-2**: When no output path is specified, the tool should continue to use the default `outputs` directory
- **FR-3**: The fix should work for both the `translate` and `glossary` commands
- **FR-4**: The tool should ensure the specified output directory exists before writing files

## Non-Functional Requirements
- **NFR-1**: The fix should maintain the same user interface and command-line options
- **NFR-2**: The fix should not impact the web interface functionality
- **NFR-3**: The fix should be backward compatible with existing usage

## Constraints
- **Technical**: Must work with the existing codebase structure and dependencies
- **Dependencies**: No new dependencies required

## Assumptions
- The user has write permissions to the specified output directory
- The output directory parameter is either a file path or a directory path

## Acceptance Criteria

### AC-1: CLI Output Directory Usage
- **Given**: A user runs the `pdftrans translate` command with an `-o` parameter specifying a custom directory
- **When**: The translation process completes
- **Then**: The output file should be generated directly in the specified directory, not in the default `outputs` directory
- **Verification**: `programmatic`

### AC-2: Backward Compatibility
- **Given**: A user runs the `pdftrans translate` command without specifying an output directory
- **When**: The translation process completes
- **Then**: The output file should be generated in the default `outputs` directory
- **Verification**: `programmatic`

### AC-3: Glossary Command Fix
- **Given**: A user runs the `pdftrans glossary` command with an `-o` parameter specifying a custom directory
- **When**: The glossary extraction process completes
- **Then**: The output file should be generated directly in the specified directory
- **Verification**: `programmatic`

### AC-4: Directory Creation
- **Given**: A user runs the tool with an output path in a non-existent directory
- **When**: The tool starts processing
- **Then**: The tool should create the necessary directories automatically
- **Verification**: `programmatic`

## Open Questions
- [x] How does the translation service currently handle output paths?
  - The translation service currently hardcodes the output directory to `config.OUTPUT_FOLDER` (default: `outputs/` directory in the project root)
  - All output generation methods (`generate_pdf_output`, `generate_docx_output`, `generate_markdown_output`) use this fixed directory
  - The CLI command generates files in this default directory first, then copies them to the user-specified location

- [x] What changes are needed in the translation service to support custom output directories?
  - Add an optional `output_path` parameter to the `process_translation_sync` method
  - Modify the output generation methods to accept and use this custom path when provided
  - Update the file path construction logic to use the custom directory instead of `config.OUTPUT_FOLDER`

- [x] How to pass the custom output directory from the CLI to the translation service?
  - Modify the `translate_handler` function in `translate_command.py` to extract the output directory from `args.output`
  - Pass this directory to the `process_translation_sync` method
  - Remove the file copying logic that currently copies from the default directory to the user-specified location

## Default Output Directory Behavior
- **Translate command**: When no output path is specified, the tool uses the default `outputs/` directory in the project root (defined in `config.py` as `config.OUTPUT_FOLDER`)
- **Glossary command**: When no output path is specified, it uses the current working directory
- **Reason for difference**: The glossary command was implemented to generate files in the current directory for convenience, while the translate command was designed to use a dedicated output directory
- **Implementation note**: The fix will maintain this difference in default behavior but ensure both commands respect user-specified output directories

