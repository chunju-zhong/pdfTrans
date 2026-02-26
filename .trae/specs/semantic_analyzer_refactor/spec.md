# Semantic Analyzer Refactoring - Product Requirement Document

## Overview
- **Summary**: Refactor the semantic analysis functionality from the existing Translator classes into a separate, modular system with a base SemanticAnalyzer class and specialized derived classes. All semantic analysis-related functions are removed from Translator classes, and semantic analysis (including merge_semantic_blocks_with_llm) will be handled entirely by the new separate module.
- **Purpose**: To allow for more flexible and model-specific parameterization of semantic analysis, particularly for different translation APIs like aiping and Silicon Flow, while completely separating semantic analysis from translation functionality.
- **Target Users**: Developers working on the PDF translation tool who need to customize semantic analysis behavior for different translation services.

## Goals
- Create a new modular semantic analysis system with a base class and derived classes
- Allow for model-specific parameterization of semantic analysis
- Remove all semantic analysis-related functions from Translator classes
- Enable merge_semantic_blocks_with_llm to directly use the new semantic analysis class instead of indirectly calling through Translator classes
- Enable users to choose different semantic analyzer implementations
- Ensure Silicon Flow can use the base SemanticAnalyzer class directly
- Implement aiping-specific cost-priority parameters in its derived class

## Non-Goals (Out of Scope)
- Changing the core semantic analysis logic
- Modifying the Translator base class interface
- Adding new translation APIs
- Altering existing PDF extraction or generation functionality

## Background & Context
- The current implementation embeds semantic analysis functionality within each Translator derived class
- Different translation services require different API parameters (e.g., aiping requires cost-priority parameters)
- Silicon Flow uses standard OpenAI API format, while aiping has additional parameters
- The refactoring will enable better code organization and easier maintenance

## Functional Requirements
- **FR-1**: Create a new base `SemanticAnalyzer` class with core semantic analysis functionality
- **FR-2**: Implement `AipingSemanticAnalyzer` derived class with cost-priority parameters
- **FR-3**: Remove semantic analysis functionality from SiliconFlowTranslator and AipingTranslator
- **FR-4**: Allow users to select which semantic analyzer implementation to use
- **FR-5**: Ensure the new semantic analyzer system can be used independently of the Translator classes
- **FR-6**: Enable merge_semantic_blocks_with_llm to directly use the new semantic analysis class instead of indirectly calling through Translator classes

## Non-Functional Requirements
- **NFR-1**: Maintain backward compatibility with existing code
- **NFR-2**: Follow existing code style and project structure
- **NFR-3**: Implement proper error handling and logging
- **NFR-4**: Ensure modular design with clear separation of concerns

## Constraints
- **Technical**: Must use existing OpenAI client library and API format
- **Dependencies**: Depends on the existing Translator class hierarchy
- **Business**: Must maintain existing functionality while improving code structure

## Assumptions
- Existing semantic analysis logic is correct and should be preserved
- Both aiping and Silicon Flow use OpenAI-compatible chat completions API
- The cost-priority parameters are specific to aiping's API implementation

## Acceptance Criteria

### AC-1: New SemanticAnalyzer Base Class
- **Given**: The new semantic analyzer module is created
- **When**: A developer instantiates the base SemanticAnalyzer class
- **Then**: It should provide all core semantic analysis functionality without service-specific parameters
- **Verification**: `programmatic`

### AC-2: AipingSemanticAnalyzer Derived Class
- **Given**: The AipingSemanticAnalyzer class is implemented
- **When**: It's used for semantic analysis
- **Then**: It should include the cost-priority parameters in API calls
- **Verification**: `programmatic`

### AC-3: Translator Classes Updated
- **Given**: Translator classes have all semantic analysis-related functions removed
- **When**: Semantic analysis is performed
- **Then**: It should be handled entirely by the new semantic analyzer classes, not through Translator classes
- **Verification**: `programmatic`

### AC-4: User Selection of Semantic Analyzer
- **Given**: The system is configured with multiple semantic analyzer options
- **When**: A user selects a specific analyzer
- **Then**: The system should use that analyzer for semantic analysis
- **Verification**: `programmatic`

### AC-5: Silicon Flow Compatibility
- **Given**: Silicon Flow translator is configured
- **When**: Semantic analysis is performed
- **Then**: It should use the base SemanticAnalyzer class directly
- **Verification**: `programmatic`

## Open Questions
- How will users select which semantic analyzer to use? (Configuration file, UI setting, etc.)
- Should the semantic analyzer be instantiated per request or as a singleton?
- How to handle dependency injection of the semantic analyzer into Translator classes?