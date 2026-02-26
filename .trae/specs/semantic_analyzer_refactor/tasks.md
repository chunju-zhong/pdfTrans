# Semantic Analyzer Refactoring - The Implementation Plan

## \[x] Task 1: Create SemanticAnalyzer Base Class

* **Priority**: P0

* **Depends On**: None

* **Description**:

  * Create a new `semantic_analyzer.py` module with a base `SemanticAnalyzer` class

  * Implement core semantic analysis methods: `analyze_semantic_relationship` and `batch_analyze_semantic_relationship`

  * Use standard OpenAI API format for model calls

  * Include methods for generating semantic analysis prompts

* **Acceptance Criteria Addressed**: AC-1

* **Test Requirements**:

  * `programmatic` TR-1.1: Base SemanticAnalyzer class can be instantiated and used for semantic analysis

  * `programmatic` TR-1.2: Core semantic analysis methods return valid results

* **Notes**: The base class should be compatible with Silicon Flow's standard OpenAI implementation

## \[x] Task 2: Implement AipingSemanticAnalyzer Derived Class

* **Priority**: P0

* **Depends On**: Task 1

* **Description**:

  * Create `AipingSemanticAnalyzer` class derived from `SemanticAnalyzer`

  * Implement cost-priority parameters in API calls (as seen in aiping\_translator.py lines 155-167)

  * Override necessary methods to include aiping-specific parameters

* **Acceptance Criteria Addressed**: AC-2

* **Test Requirements**:

  * `programmatic` TR-2.1: AipingSemanticAnalyzer includes cost-priority parameters in API calls

  * `programmatic` TR-2.2: AipingSemanticAnalyzer correctly inherits and extends base class functionality

* **Notes**: Ensure the cost-priority parameters match the existing implementation in aiping\_translator.py

## [x] Task 3: Remove Semantic Analysis Functionality from SiliconFlowTranslator
- **Priority**: P1
- **Depends On**: Task 1
- **Description**: 
  - Remove all semantic analysis-related methods and functionality from `SiliconFlowTranslator` class
  - Ensure the class only focuses on translation functionality
  - No longer include semantic analyzer dependency in initialization
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**: 
  - `programmatic` TR-3.1: SiliconFlowTranslator no longer contains semantic analysis functionality
  - `programmatic` TR-3.2: Translation functionality remains intact
- **Notes**: SiliconFlowTranslator should only handle translation, not semantic analysis

## [x] Task 4: Remove Semantic Analysis Functionality from AipingTranslator
- **Priority**: P1
- **Depends On**: Task 1, Task 2
- **Description**: 
  - Remove all semantic analysis-related methods and functionality from `AipingTranslator` class
  - Ensure the class only focuses on translation functionality
  - No longer include semantic analyzer dependency in initialization
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**: 
  - `programmatic` TR-4.1: AipingTranslator no longer contains semantic analysis functionality
  - `programmatic` TR-4.2: Translation functionality remains intact
- **Notes**: AipingTranslator should only handle translation, not semantic analysis

## [x] Task 5: Add Semantic Analyzer Selection Mechanism
- **Priority**: P1
- **Depends On**: Task 1, Task 2
- **Description**: 
  - Create a mechanism for users to select which semantic analyzer implementation to use independently of the Translator classes
  - Update configuration or initialization to support semantic analyzer selection
  - Ensure proper instantiation of the selected analyzer
- **Acceptance Criteria Addressed**: AC-4
- **Test Requirements**: 
  - `programmatic` TR-5.1: Users can select between different semantic analyzer implementations
  - `programmatic` TR-5.2: The selected analyzer is correctly used for semantic analysis independently of Translator classes
- **Notes**: Consider how this selection will be exposed to users (configuration file, API parameter, etc.)

## [x] Task 6: Remove All Semantic Analysis Functions from Translator Classes
- **Priority**: P1
- **Depends On**: Task 1
- **Description**: 
  - Update the base `Translator` class to remove all semantic analysis-related functions
  - Ensure no semantic analysis functionality remains in any Translator class
  - Ensure backward compatibility while supporting the new architecture
  - Update any necessary methods or properties
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**: 
  - `programmatic` TR-6.1: Translator base class no longer contains semantic analysis functionality
  - `programmatic` TR-6.2: No semantic analysis-related functions remain in any Translator class
  - `programmatic` TR-6.3: Existing Translator functionality remains intact
- **Notes**: Be careful not to break existing Translator interface

## [x] Task 7: Update merge_semantic_blocks_with_llm to Use New Semantic Analysis Class
- **Priority**: P0
- **Depends On**: Task 1, Task 2, Task 5
- **Description**: 
  - Update merge_semantic_blocks_with_llm function to directly use the new semantic analysis class instead of indirectly calling through Translator classes
  - Ensure the function can select and use the appropriate semantic analyzer implementation
  - Update any necessary parameters or return values
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-4
- **Test Requirements**: 
  - `programmatic` TR-7.1: merge_semantic_blocks_with_llm directly uses the new semantic analysis class
  - `programmatic` TR-7.2: The function can select and use different semantic analyzer implementations
  - `programmatic` TR-7.3: Semantic analysis results are consistent with previous implementation
- **Notes**: This is a critical task as it ensures the main semantic analysis function uses the new system

## [ ] Task 8: Test and Verify Implementation
- **Priority**: P0
- **Depends On**: All previous tasks
- **Description**: 
  - Test all semantic analyzer implementations
  - Verify compatibility with existing Translator classes
  - Ensure proper error handling and logging
  - Test edge cases and performance
- **Acceptance Criteria Addressed**: All
- **Test Requirements**: 
  - `programmatic` TR-8.1: All semantic analyzer tests pass
  - `programmatic` TR-8.2: merge_semantic_blocks_with_llm correctly uses semantic analyzers
  - `human-judgment` TR-8.3: Code follows project style guidelines and is well-organized
- **Notes**: Comprehensive testing is crucial to ensure the refactoring doesn't break existing functionality

