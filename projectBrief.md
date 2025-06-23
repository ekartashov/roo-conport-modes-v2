# Roo ConPort Modes v2 - Project Brief

## Project Overview

**roo-conport-modes-v2** is a mode development framework for the roo coding agent that solves the "smart worker with Alzheimer's" problem through mandatory ConPort integration. This project implements a dual-track versioning system where human-readable source specifications drive AI-generated modes, with comprehensive knowledge preservation across development sessions.

## Core Purpose

Establish a **meta-development system** that provides:
- Persistent AI memory across sessions through mandatory ConPort integration
- Multi-file human/AI-readable mode specifications with semantic behavior transmission
- Dual-track versioning: filesystem for humans, ConPort for AI metadata
- Automatic knowledge preservation with real-time logging via MCP server
- Horizontal version expansion with source/binary separation concepts

## Project Scope

### Primary Components

1. **Dual-Track Version Management System**
   - Multi-file mode specifications with dual-axis organization (Scope × Purpose)
   - Hierarchical file resolution: global → shared → template → mode-specific
   - Type-aware processing: knowledge, tests, metadata, and configuration files
   - Horizontal version expansion with complete specification sets per version
   - Filesystem-based human access with Git tracking
   - ConPort-based AI metadata storage with behavioral vectors

2. **ConPort-Filesystem Integration Bridge**
   - Automatic logging of filesystem changes via ConPort MCP server
   - Real-time synchronization between file operations and knowledge management
   - Scoped history files for selective context loading
   - Bidirectional linking between filesystem versions and ConPort entries

3. **AI-Enhanced Testing Framework**
   - Hybrid behavior/artifact testing with conventional and AI-driven quality assurance
   - Statistical approach to AI test results with adaptive scope management
   - Live testing through existing MCP server/CLI integration
   - Change impact tracking with conflict resolution procedures

4. **Mode Development Meta-System**
   - Local project mode for creating and maintaining other modes
   - Semantic extraction for cross-mode idea sharing
   - Non-executable programming language concepts for deterministic AI behavior
   - Template-driven mode creation with guided development workflows

## Key Principles

### Integration Architecture
- **Roo-Centric with ConPort Enhancement**: No system without roo extension, ConPort provides exponential workflow enhancement
- **Mandatory ConPort Integration**: All development decisions and progress flow through ConPort in real-time
- **Context Preservation**: Prevents task regression and forgotten progress across chat sessions

### Version Management Philosophy
- **Source vs Binary Separation**: Specification files are diffable source code, generated modes are conceptual binaries
- **Horizontal Expansion**: Each version gets complete directory with preserved change tracking
- **Scoped History**: Multiple selective history files instead of monolithic history loading

### Knowledge Management Strategy
- **Real-Time Logging**: Automatic ConPort updates via scripts with rich metadata (confidence, purpose, risk assessment)
- **Semantic Extraction**: Cross-mode idea generation without direct composition complexity
- **Mandatory Discovery/Categorization**: Context preservation through systematic organization

## Current Development Phase

### Phase 1: Foundation Architecture (COMPLETE)

**Completed Components:**
1. **Mode Synchronization System** ✅
   - Comprehensive CLI tool (`roo_modes_sync`) with professional features
   - Sophisticated backup/restore system with automatic versioning
   - Multiple ordering strategies (strategic, alphabetical, category, custom)
   - Robust validation and error handling throughout

2. **Testing Infrastructure** ✅
   - Comprehensive test suite (25+ test files) with >95% coverage
   - TDD practices demonstrated throughout codebase
   - MCP server integration with resource access and tool definitions
   - End-to-end testing capabilities

### Phase 2: Implementation & Documentation (CURRENT)

**Immediate Objectives:**
1. **Dual-Track Version System Implementation**
   - Multi-file specification architecture
   - Horizontal version directory structure
   - ConPort-filesystem integration scripts
   - Scoped history file generation

2. **Knowledge Documentation Sprint**
   - Retroactive logging of architectural decisions in ConPort
   - Extraction of design patterns from existing codebase
   - Formalization of implicit TDD workflow
   - Template creation for mode development

3. **Meta-Mode Development**
   - Local mode-development mode creation
   - Integration with existing roo_modes_sync tooling
   - AI-guided mode creation workflows
   - Testing framework for mode specifications

### Implementation Deliverables

1. **Version Management System**
   - Directory structure: `modes/mode_name/versions/vX/` with symlink current pointers
   - Multi-file specifications with dual-axis organization (knowledge/tests/metadata/config)
   - Hierarchical file resolution with shared knowledge repositories
   - Mode compilation manifests with dependency tracking and build instructions
   - Scoped history files: behavioral_history.md, technical_history.md, test_history.md
   - ConPort integration with version_meta.json mapping

2. **Development Workflow Automation**
   - Script-driven ConPort logging via MCP server
   - Automatic behavioral vector generation
   - Radical change detection between versions
   - Hardlink optimization for unchanged files
   - Roo evals integration for automated compilation and testing
   - CLI-driven quality assurance pipelines without human intervention

3. **Mode Development Templates**
   - Specification file templates for different mode types
   - Guided creation workflows with AI assistance
   - Quality gate definitions and automated enforcement
   - Testing patterns for AI-driven quality assurance

## Technical Architecture

### Dual-Track Directory Structure with Dual-Axis Organization
```
/modes/                           # Mode development workspace
├── shared/                       # SCOPE: Cross-mode shared resources
│   ├── knowledge/               # PURPOSE: Shared knowledge files
│   │   ├── behavioral_patterns.knowledge.md
│   │   ├── interaction_flows.knowledge.md
│   │   └── conport_workflows.knowledge.md
│   ├── tests/                   # PURPOSE: Shared test files
│   │   ├── common_behaviors.test.yaml
│   │   ├── integration_patterns.test.yaml
│   │   └── quality_gates.test.yaml
│   ├── metadata/                # PURPOSE: Shared metadata files
│   │   ├── shared_dependencies.metadata.yaml
│   │   └── compatibility_matrix.metadata.yaml
│   └── config/                  # PURPOSE: Shared configuration files
│       ├── validation_rules.config.yaml
│       └── processing_options.config.yaml
├── templates/                   # SCOPE: Template inheritance
│   ├── base_mode_template/
│   │   ├── knowledge/
│   │   │   ├── purpose.template.knowledge.md
│   │   │   └── algorithms.template.knowledge.md
│   │   ├── tests/
│   │   │   └── basic_validation.template.test.yaml
│   │   ├── metadata/
│   │   │   └── mode_manifest.template.yaml
│   │   └── config/
│   │       └── build_options.template.config.yaml
│   ├── knowledge_aware_template/    # Template for ConPort-enabled modes
│   └── orchestrator_template/       # Template for multi-mode coordination
├── global_knowledge/            # SCOPE: Universal principles
│   ├── knowledge/
│   │   ├── core_principles.knowledge.md
│   │   └── interaction_guidelines.knowledge.md
│   ├── tests/
│   │   └── universal_quality.test.yaml
│   └── metadata/
│       └── global_standards.metadata.yaml
├── mode_name/                   # SCOPE: Mode-specific implementation
│   ├── versions/
│   │   ├── v1/
│   │   │   ├── knowledge/       # Mode-specific knowledge
│   │   │   │   ├── purpose.knowledge.md
│   │   │   │   ├── algorithms.knowledge.md
│   │   │   │   ├── anti_patterns.knowledge.md
│   │   │   │   └── specializations/
│   │   │   │       └── domain_specific.knowledge.md
│   │   │   ├── tests/           # Mode-specific tests
│   │   │   │   ├── behavior_validation.test.yaml
│   │   │   │   ├── integration_tests.test.yaml
│   │   │   │   └── quality_assurance.test.yaml
│   │   │   ├── metadata/        # Mode-specific metadata
│   │   │   │   ├── mode_manifest.yaml    # Build instructions & dependencies
│   │   │   │   ├── version_meta.json     # ConPort ID mapping
│   │   │   │   ├── dependencies.metadata.yaml
│   │   │   │   └── CHANGES.metadata.yaml # Version-specific change metadata
│   │   │   ├── config/          # Mode-specific config
│   │   │   │   ├── build_options.config.yaml
│   │   │   │   └── processing_rules.config.yaml
│   │   │   └── changelog/       # Version-specific changelog files
│   │   │       ├── CHANGELOG.md          # Human-readable changes summary
│   │   │       ├── BREAKING_CHANGES.md   # Breaking changes documentation
│   │   │       ├── MIGRATION_GUIDE.md    # Version migration instructions
│   │   │       └── context_scope.yaml    # Selective loading configuration
│   │   ├── v2/                  # Next version with changes
│   │   └── ...
│   ├── current -> versions/vX   # Symlink to active version
│   ├── behavioral_history.md    # Mode behavior evolution
│   ├── technical_history.md     # Implementation changes
│   ├── test_history.md         # Quality metrics tracking
│   └── decision_history.md     # Architectural decisions
├── /context_portal/            # ConPort MCP server (existing)
├── /scripts/roo_modes_sync/    # Sync system (existing, to be extended)
└── /mode_development/          # Meta-mode for creating modes
```

### Technology Stack
- **Mode Specifications**: Dual-axis organized files (knowledge, tests, metadata, config)
- **File Organization**: Hierarchical resolution with scope-based inheritance
- **Compilation System**: YAML-based manifests with dependency tracking
- **Version Management**: Filesystem directories + ConPort metadata storage
- **MCP Integration**: ConPort server for automatic knowledge logging
- **Sync System**: Extended roo_modes_sync with manifest-driven builds
- **Testing**: Type-aware validation with AI-driven quality assurance
- **Knowledge Management**: Real-time ConPort integration with rich metadata

### Integration Patterns
- **Filesystem-ConPort Bridge**: Scripts automatically sync changes via MCP server
- **Version Linking**: Bidirectional mapping between directories and ConPort entries
- **Behavioral Vectors**: AI-generated fingerprints for semantic version comparison
- **Change Detection**: Automatic flagging of radical vs incremental changes
- **Hierarchical File Resolution**: Global → Shared → Template → Mode-specific precedence
- **Manifest-Driven Compilation**: Dependency tracking with checksum-based change detection
- **Type-Aware Processing**: Purpose-specific validation and build rules

### Mode Compilation Manifest System
Each mode version includes a `mode_manifest.yaml` that functions as build instructions:

```yaml
# mode_manifest.yaml - Build instructions for mode generation
version: "v2.1"
mode_name: "architect"
created: "2025-06-23T20:20:00Z"
generator_version: "roo_modes_sync v1.2.0"

# Hierarchical source file resolution
source_files:
  knowledge_files:
    global:
      - "../../../global_knowledge/knowledge/core_principles.knowledge.md"
    shared:
      - "../../shared/knowledge/behavioral_patterns.knowledge.md"
      - "../../shared/knowledge/conport_workflows.knowledge.md"
    mode_specific:
      - "knowledge/purpose.knowledge.md"
      - "knowledge/algorithms.knowledge.md"
      - "knowledge/specializations/architecture_domain.knowledge.md"
  
  test_files:
    shared:
      - "../../shared/tests/common_behaviors.test.yaml"
    mode_specific:
      - "tests/behavior_validation.test.yaml"
      - "tests/integration_tests.test.yaml"
  
  metadata_files:
    mode_specific:
      - "metadata/dependencies.metadata.yaml"
      - "metadata/version_meta.json"
  
  config_files:
    global:
      - "../../../global_knowledge/config/global_processing.config.yaml"
    mode_specific:
      - "config/build_options.config.yaml"

# File precedence rules (highest to lowest)
precedence:
  1: "mode_specific"     # Mode files override everything
  2: "shared"           # Shared files override templates/global
  3: "inherits_from"    # Template files override global
  4: "global"          # Global files are base layer

# Processing rules by file type
processing_rules:
  knowledge_files:
    validation: "markdown_lint + semantic_check"
    compilation: "merge_with_precedence"
    output: "compiled_knowledge_base"
  
  test_files:
    validation: "yaml_syntax + test_case_structure"
    execution: "ai_behavior_testing"
    output: "test_results + quality_metrics"
  
  metadata_files:
    validation: "schema_validation"
    processing: "dependency_resolution"
    output: "build_metadata"
  
  config_files:
    validation: "config_schema_check"
    processing: "parameter_resolution"
    output: "build_configuration"

# Source file checksums for change detection
checksums:
  "knowledge/purpose.knowledge.md": "sha256:a1b2c3d4..."
  "knowledge/algorithms.knowledge.md": "sha256:e5f6g7h8..."
  "tests/behavior_validation.test.yaml": "sha256:i9j0k1l2..."

# Build pipeline with type-aware processing
build_pipeline:
  1: "load_and_validate_config_files"
  2: "resolve_dependencies_from_metadata"
  3: "compile_knowledge_files_with_precedence"
  4: "execute_test_files_for_validation"
  5: "generate_final_mode_specification"
```

### File Type Processing Rules

**Knowledge Files (`.knowledge.md`)**
- **Purpose**: AI behavior specifications and domain knowledge
- **Processing**: Semantic merging with precedence rules
- **Validation**: Markdown syntax + semantic consistency checking
- **Output**: Compiled knowledge base for mode generation

**Test Files (`.test.yaml`)**
- **Purpose**: Validation, quality assurance, and behavior testing
- **Processing**: Execution with pass/fail results and metrics
- **Validation**: YAML syntax + test case structure validation
- **Output**: Test results and quality metrics

**Metadata Files (`.metadata.yaml`)**
- **Purpose**: Build information, dependencies, version tracking
- **Processing**: Dependency resolution and compatibility checking
- **Validation**: Schema validation against metadata standards
- **Output**: Build metadata and dependency graphs

**Configuration Files (`.config.yaml`)**
- **Purpose**: Processing options, build flags, validation rules
- **Processing**: Parameter resolution and build control
- **Validation**: Configuration schema validation
- **Output**: Build configuration for processing pipeline

### Build System Integration

**Manifest-Driven Build Commands**
```bash
# Dependency-aware builds with scope tracking
roo_modes_sync build architect --check-dependencies
roo_modes_sync build --affected-by=shared/knowledge/behavioral_patterns.knowledge.md

# Conditional compilation based on manifest rules
roo_modes_sync build architect --mode-type=knowledge_aware
roo_modes_sync build --include-conditionals="supports_orchestration"

# Incremental builds using checksums
roo_modes_sync build --incremental architect
roo_modes_sync validate --type=knowledge architect

# Cross-scope impact analysis
roo_modes_sync impact-analysis global_knowledge/knowledge/core_principles.knowledge.md
roo_modes_sync trace-dependencies architect --show-inheritance
```

### Roo Evals Integration for Automated Compilation & Testing

**Architecture Overview**
- **Roo Code Agent**: VSCodium IDE extension for interactive development
- **Roo Evals Package**: CLI-based automation for compilation and testing without human assistance
- **Integration Point**: Our manifest-driven build system feeds into roo evals pipeline

**Automated Mode Compilation Pipeline**
```bash
# Mode compilation from dual-axis source files
roo_modes_sync compile architect --target=roo_evals
# → Generates mode specification compatible with roo evals input format

# Automated testing via roo evals CLI
roo-evals test-mode architect --source=modes/architect/current/ --manifest=mode_manifest.yaml
# → Runs comprehensive behavioral and integration tests without human intervention

# Continuous integration pipeline
roo-evals validate-mode-build --workspace=. --mode=architect --strict
# → Full validation including dependency resolution, compilation, and testing
```

**Integration Architecture**
```yaml
# Integration workflow in mode_manifest.yaml
compilation_targets:
  roo_evals:
    output_format: "roo_evals_specification"
    test_automation: true
    validation_level: "strict"
    
testing_integration:
  roo_evals_config:
    test_runner: "roo-evals"
    automation_level: "full"
    human_intervention: false
    test_types:
      - "behavioral_validation"
      - "integration_testing"
      - "quality_assurance"
      - "cross_mode_compatibility"

# Build pipeline integration
build_pipeline:
  1: "load_and_validate_config_files"
  2: "resolve_dependencies_from_metadata"
  3: "compile_knowledge_files_with_precedence"
  4: "generate_roo_evals_compatible_output"     # ← NEW
  5: "execute_roo_evals_automated_testing"     # ← NEW
  6: "validate_compilation_success"            # ← NEW
```

**Research & Implementation Requirements**
- **Roo Evals CLI Interface**: Investigate command structure and input/output formats
- **Compilation Targets**: Understand how roo evals expects mode specifications
- **Testing Automation**: Map our dual-axis test files to roo evals test execution
- **Integration Points**: Define handoff between roo_modes_sync and roo evals
- **Quality Pipelines**: Automate end-to-end validation without human oversight

### Selective Changelog Loading & Context Scope Management

**Problem**: Prevent automatic loading of irrelevant changelog context during development sessions to avoid information overload and maintain focus.

**Solution Architecture**: Version-specific changelog files with selective loading mechanisms

**Version-Specific Changelog Structure**
```yaml
# context_scope.yaml - Controls selective changelog loading
changelog_scope:
  default_load: false              # Don't auto-load changelogs
  load_triggers:
    - "version_comparison_requested"
    - "migration_planning_session"
    - "breaking_changes_analysis"
    - "explicit_changelog_request"
  
  context_filters:
    current_session_relevant: true  # Only load changes relevant to current work
    breaking_changes_only: false    # Filter to show only breaking changes
    since_version: null            # Load changes since specific version
    max_versions_back: 3           # Limit historical depth
    
  auto_load_conditions:
    when_editing_tests: false      # Don't auto-load when editing test files
    when_creating_new_version: true # DO load when creating new version
    when_debugging_issues: "smart" # Load only if related to current issue
```

**Smart Loading Commands**
```bash
# Development-focused commands (NO changelog auto-loading)
roo_modes_sync work-on architect
roo_modes_sync build architect --focus-mode

# History-aware commands (selective changelog loading)
roo_modes_sync compare-versions architect v2.0 v2.1 --include-changelogs
roo_modes_sync plan-migration architect v2.1 v3.0 --load-breaking-changes
roo_modes_sync debug-issue architect --smart-changelog-loading

# Explicit changelog access
roo_modes_sync show-changelog architect v2.1
roo_modes_sync show-breaking-changes architect --since=v2.0
```

**Integration with Mode Manifest**
```yaml
# mode_manifest.yaml - Changelog management integration
changelog_management:
  version_changelog_path: "changelog/"
  auto_load_policy: "selective"
  context_pollution_prevention: true
  
  loading_rules:
    development_sessions: "no_auto_load"
    version_planning: "load_relevant_only"
    migration_analysis: "load_breaking_changes"
    debugging: "smart_contextual_loading"
    
  changelog_dependencies:
    - file: "changelog/CHANGELOG.md"
      load_condition: "explicit_request_only"
    - file: "changelog/BREAKING_CHANGES.md"
      load_condition: "migration_or_version_comparison"
    - file: "metadata/CHANGES.metadata.yaml"
      load_condition: "build_system_needs_only"
```

**Benefits of Selective Loading**
- **Focused Development**: No irrelevant historical context during coding sessions
- **Reduced Cognitive Load**: Prevents information overload from extensive change histories
- **Contextual Relevance**: Loads changelog information only when planning or migration tasks require it
- **Performance Optimization**: Faster session startup without loading unnecessary historical data
- **Smart Defaults**: Intelligent loading based on session type and current task context

## Success Criteria

### Phase 1 (Foundation) - COMPLETE ✅
- [x] Mode synchronization system with comprehensive CLI
- [x] Robust testing framework with TDD practices
- [x] MCP server integration with backup capabilities
- [x] Multiple ordering strategies and validation systems

### Phase 2 (Implementation) Success Metrics
- [ ] Dual-axis file organization system (Scope × Purpose) implemented
- [ ] Mode compilation manifest system with dependency tracking operational
- [ ] Hierarchical file resolution with shared knowledge repositories functional
- [ ] Type-aware processing rules for knowledge/tests/metadata/config files
- [ ] Extended roo_modes_sync CLI with manifest-driven build commands
- [ ] ConPort-filesystem integration scripts with automatic decision logging
- [ ] Local mode-development mode created and tested with dual-axis structure
- [ ] Template-driven mode creation workflow with inheritance patterns established

### Overall Project Success
- [ ] Persistent AI memory across development sessions
- [ ] Zero context loss during mode development
- [ ] Automatic knowledge preservation with rich metadata
- [ ] Self-guided mode development through meta-modes
- [ ] Horizontal scalability for multiple concurrent mode development

## Development Principles

### Architectural Foundations
- **Dual-Track Philosophy**: Filesystem for humans, ConPort for AI metadata
- **Source/Binary Separation**: Specifications are diffable, generated modes are conceptual binaries
- **Mandatory Integration**: ConPort integration required for all mode development
- **Horizontal Expansion**: Version growth through complete specification sets

### Implementation Strategy
- **Build on Existing Foundation**: Extend proven roo_modes_sync system
- **Real-Time Knowledge Flow**: Automatic ConPort updates prevent knowledge debt
- **Scoped Context Loading**: Multiple history files for targeted information retrieval
- **AI-Enhanced Quality**: Statistical testing approaches for non-conventional aspects

## Next Steps

### Immediate Implementation (2-4 weeks)
1. **Dual-Axis File Organization System**
   - Create `/shared/`, `/templates/`, `/global_knowledge/` directory structure
   - Implement hierarchical file resolution with precedence rules
   - Define file naming conventions (`.knowledge.md`, `.test.yaml`, `.metadata.yaml`, `.config.yaml`)
   - Extract common patterns from existing modes into shared knowledge repositories

2. **Mode Compilation Manifest System**
   - Design `mode_manifest.yaml` schema with dependency tracking
   - Implement checksum-based change detection for incremental builds
   - Create conditional inclusion rules for different mode types
   - Integrate with existing `version_meta.json` ConPort linking system

3. **Extended roo_modes_sync CLI**
   - Add `build`, `check-dependencies`, `validate` commands with type awareness
   - Implement manifest-driven compilation with scope resolution
   - Create impact analysis tools for cross-scope dependency tracking
   - Add template inheritance and shared knowledge management features

### Medium-Term Goals (1-2 months)
1. **Template System with Inheritance**
   - Create base templates: `base_mode_template`, `knowledge_aware_template`, `orchestrator_template`
   - Implement template inheritance with override capabilities
   - Design guided mode creation workflows using template patterns
   - Develop quality gate enforcement with type-specific validation rules

2. **Advanced Build System Integration**
   - Implement AI-driven testing for multi-file specifications
   - Create statistical quality assessment with type-aware metrics
   - Develop automated change impact analysis across file hierarchies
   - Build cross-mode knowledge extraction and sharing capabilities

## Project Status

**Current Phase**: Implementation & Documentation
**Foundation**: Complete sync system with comprehensive testing
**Focus**: Dual-track version management, ConPort integration, meta-mode development
**Approach**: Build on existing proven foundation with strategic extensions
**Architecture**: Ready for implementation with clear separation of concerns