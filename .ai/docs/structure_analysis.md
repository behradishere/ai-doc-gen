Perfect! Now I have a comprehensive understanding of the codebase. Let me create the final structure analysis document:

# Code Structure Analysis

## Architectural Overview

The AI Documentation Generator is a **multi-agent Python CLI application** built on a sophisticated **command-handler-agent architecture** that leverages AI language models to automatically analyze codebases and generate comprehensive documentation. The system employs a **tool-based agent framework** using pydantic-ai for LLM orchestration with OpenTelemetry observability.

**Core Architectural Patterns:**

- **Multi-Agent Architecture**: Specialized AI agents with distinct responsibilities - AnalyzerAgent orchestrates 5 concurrent sub-agents (Structure, Dependencies, Data Flow, Request Flow, API), while DocumenterAgent handles README generation
- **Command Pattern**: Handler-based execution model with separate handlers for analyze, document, and cronjob operations, each implementing the `AbstractHandler` interface
- **Tool Pattern**: Extensible tool system providing file operations (`FileReadTool`, `ListFilesTool`) to AI agents with retry mechanisms and error handling
- **Configuration-Driven Design**: Hierarchical YAML-based configuration with environment variable overrides and CLI argument precedence, all validated through Pydantic models
- **Async/Await Pattern**: Fully asynchronous execution model enabling concurrent agent operations using `asyncio.gather()` with error isolation

**Technology Stack:**

- **Core Framework**: Python 3.13 with pydantic-ai (v1.0.15) for AI agent orchestration
- **AI Integration**: OpenAI-compatible APIs with custom Gemini provider support (`CustomGeminiGLA`)
- **Observability**: OpenTelemetry tracing with Logfire (v4.12.0) integration for LLM monitoring
- **Git Integration**: GitPython (v3.1.45) and python-gitlab (v6.2.0) for repository operations and automated MR creation
- **Configuration**: YAML + python-dotenv with Pydantic (v2.12.0) validation and hierarchical merging
- **Template Engine**: Jinja2 (v3.1.6) for prompt management with caching
- **HTTP Client**: HTTPX with custom retry logic using tenacity for resilient API calls

**Project Structure:**

```
src/
├── main.py                    # CLI entry point with dynamic argument generation
├── config.py                  # Multi-source configuration management
├── handlers/                  # Command handlers implementing business logic
│   ├── base_handler.py       # Abstract handler interface
│   ├── analyze.py            # Analysis orchestration handler
│   ├── readme.py             # Documentation generation handler
│   └── cronjob.py            # GitLab automation handler
├── agents/                    # AI agent implementations
│   ├── analyzer.py           # Multi-agent analyzer coordinator
│   ├── documenter.py         # README generation agent
│   ├── prompts/              # YAML-based prompt templates
│   │   ├── analyzer.yaml     # Prompts for 5 analysis agents
│   │   └── documenter.yaml   # Documentation generation prompts
│   └── tools/                # Agent tools for file system access
│       ├── file_tool/        # File reading with line range support
│       └── dir_tool/         # Directory traversal with filtering
└── utils/                     # Shared utilities
    ├── logger.py             # Structured logging with JSON support
    ├── prompt_manager.py     # Jinja2 template management
    ├── retry_client.py       # HTTP client with exponential backoff
    ├── repo.py               # Git repository utilities
    ├── dict.py               # Configuration merging utilities
    └── custom_models/        # Custom LLM provider implementations
        └── gemini_provider.py
```

## Core Components

### 1. **Application Entry Point** (`src/main.py`)

**Purpose**: CLI interface orchestration and application lifecycle management

**Responsibilities**:
- Dynamic CLI argument generation from Pydantic models using reflection (`add_handler_args()`, `_add_field_arg()`)
- Command routing to appropriate handlers (analyze, document, cronjob)
- Logging configuration with repository-specific log directories
- Observability setup with Langfuse integration (`configure_langfuse()`)
- Handler instantiation and execution coordination

**Key Functions**:
- `main()`: Primary async entry point with command routing
- `parse_args()`: Dynamic argument parser generation from Pydantic model fields
- `configure_langfuse()`: OpenTelemetry configuration with base64 auth
- `analyze()`, `document()`, `cronjob_analyze()`: Command-specific entry points
- `configure_logging()`: Repository-specific logging setup

**Design Notes**: Uses `nest_asyncio.apply()` to enable nested event loops, supporting both CLI and programmatic usage.

### 2. **Configuration Management System** (`src/config.py`)

**Purpose**: Multi-source configuration management with hierarchical merging and type safety

**Responsibilities**:
- Environment variable loading with type conversion utilities (`str_to_bool()`)
- YAML configuration file parsing with nested key support
- Configuration precedence handling (defaults → file → CLI arguments)
- Pydantic model-based configuration validation
- Global configuration constants for LLM settings, GitLab integration, and tool settings

**Key Functions**:
- `load_config()`: Main configuration loading function with multi-source merging
- `load_config_from_file()`: YAML file parsing with dot-notation key extraction
- `load_config_as_dict()`: CLI argument extraction based on Pydantic model fields
- `str_to_bool()`: Environment variable type conversion helper

**Configuration Constants**:
- Analyzer LLM settings (model, base URL, API key, temperature, max tokens, timeout)
- Documenter LLM settings (separate configuration for documentation generation)
- Langfuse observability settings (public/secret keys, environment)
- GitLab integration settings (API URL, OAuth token, user credentials)
- Tool settings (retry counts for file reader and list files tools)
- HTTP retry settings (max attempts, multiplier, wait times)

### 3. **Handler Layer** (`src/handlers/`)

**Base Handler** (`base_handler.py`):
- **Purpose**: Abstract base class defining handler interface
- **Key Classes**: 
  - `AbstractHandler`: Pure interface with `handle()` method
  - `BaseHandler`: Base implementation with config storage
  - `BaseHandlerConfig`: Pydantic model with `repo_path` and optional `config` path, includes `@model_validator` for automatic config path resolution
- **Responsibilities**: Config path resolution, existence validation

**Analyze Handler** (`analyze.py`):
- **Purpose**: Orchestrates multi-agent code analysis execution
- **Configuration**: `AnalyzeHandlerConfig` extends base with analysis exclusion flags
- **Execution Flow**: Creates `AnalyzerAgent`, wraps execution in OpenTelemetry span with attributes
- **Output**: Up to 5 markdown analysis files in `.ai/docs/` directory

**README Handler** (`readme.py`):
- **Purpose**: Manages documentation generation through DocumenterAgent
- **Configuration**: `ReadmeHandlerConfig` with nested `ReadmeConfig` for section control
- **Execution Flow**: Creates `DocumenterAgent`, wraps in tracing span
- **Output**: `README.md` file in repository root

**Cronjob Handler** (`cronjob.py`):
- **Purpose**: Automated GitLab project discovery, analysis, and MR creation
- **Configuration**: `JobAnalyzeHandlerConfig` with GitLab-specific settings
- **Workflow**:
  1. Fetch projects from GitLab group with subgroup support
  2. Filter applicable projects (`_is_applicable_project()`) based on:
     - Not archived
     - Not in ignored subgroups/projects
     - Last commit not from analyzer
     - Recent activity (within `max_days_since_last_commit`)
     - No existing branch or MR
  3. Clone repository (`_clone_project()`) with branch creation
  4. Run analysis (`_analyze_project()`) using `AnalyzeHandler`
  5. Create merge request (`_create_merge_request()`) with standardized format
  6. Cleanup (`_cleanup_project()`) with error handling
- **Constants**: `COMMIT_MESSAGE_TITLE`, `IGNORED_PROJECTS`, `IGNORED_SUBGROUPS`

### 4. **Agent System** (`src/agents/`)

**AnalyzerAgent** (`analyzer.py`):
- **Purpose**: Coordinates 5 specialized analysis agents with concurrent execution
- **Configuration**: `AnalyzerAgentConfig` with repo path and exclusion flags
- **Sub-Agents** (all using same LLM model but different prompts):
  - `_structure_analyzer_agent`: Code architecture and component analysis
  - `_dependency_analyzer_agent`: Internal and external dependency mapping
  - `_data_flow_analyzer_agent`: Data transformation and persistence patterns
  - `_request_flow_analyzer_agent`: Request processing and flow analysis
  - `_api_analyzer_agent`: API endpoint and integration documentation
- **Execution Strategy**: 
  - Concurrent execution using `asyncio.gather(return_exceptions=True)`
  - Error isolation - individual agent failures don't stop others
  - Partial success handling via `validate_succession()`
- **Output Processing**: Path cleanup (`_cleanup_output()`) to remove absolute paths
- **Tools Registered**: `FileReadTool`, `ListFilesTool` with retry configuration

**DocumenterAgent** (`documenter.py`):
- **Purpose**: README generation with configurable section inclusion/exclusion
- **Configuration**: `DocumenterAgentConfig` with nested `ReadmeConfig` (9 section flags + `use_existing_readme`)
- **Model Support**: Both OpenAI and Gemini models with provider detection
- **Output Model**: `DocumenterResult` with `markdown_content` field
- **Template Variables**: Includes `available_ai_docs` list, repo path, and all readme config flags
- **Tools Registered**: `FileReadTool` only (reads existing analysis files)

**Shared Agent Features**:
- Retry configuration (2 retries per agent by default)
- OpenTelemetry instrumentation enabled
- Model settings: temperature 0.0 (deterministic), 8192 max tokens, 180s timeout
- Parallel tool calls enabled by default
- Usage tracking (total/request/response tokens, execution time)

### 5. **Tool System** (`src/agents/tools/`)

**FileReadTool** (`file_tool/file_reader.py`):
- **Purpose**: File content reading with line range support and error handling
- **Interface**: `_run(file_path: str, line_number: int = 0, line_count: int = 200) -> str`
- **Features**:
  - Line-based reading with configurable start and count
  - Formatted output with line numbers and total line count
  - OpenTelemetry span attributes for input/output
  - Error handling with `ModelRetry` exceptions
- **Error Cases**: File not found, permission denied, general read failures
- **Max Retries**: Configurable via `TOOL_FILE_READER_MAX_RETRIES` (default: 2)

**ListFilesTool** (`dir_tool/list_files.py`):
- **Purpose**: Directory traversal with comprehensive filtering and grouping
- **Interface**: `_run(directory: str, ignored_dirs: Optional[List[str]] = None, ignored_extensions: Optional[List[str]] = None) -> str`
- **Features**:
  - Recursive directory walking with file grouping by parent directory
  - Extensive default filtering (100+ ignored directories, 200+ ignored extensions)
  - Custom ignore list support
  - Alphabetically sorted output
- **Default Ignored Directories**: Version control (.git, .svn), build artifacts (node_modules, target, dist), IDE files (.idea, .vscode), caches (__pycache__, .pytest_cache)
- **Default Ignored Extensions**: Compiled files (.pyc, .class, .o), archives (.zip, .tar.gz), media files (.jpg, .png), logs (.log)
- **Max Retries**: Configurable via `TOOL_LIST_FILES_MAX_RETRIES` (default: 2)

### 6. **Utility Layer** (`src/utils/`)

**Logger** (`logger.py`):
- **Purpose**: Structured logging with file and console outputs
- **Pattern**: Singleton class with class-level `_logger` attribute
- **Features**:
  - Repository-specific log directories (`.logs/{repo_name}/{date}/`)
  - Separate log levels for file (INFO) and console (WARNING)
  - Structured data support with JSON serialization using ujson
  - Timestamp-based log file naming
  - Methods: `init()`, `info()`, `debug()`, `warning()`, `error()`, `get_logger()`
- **Format**: `%(asctime)s | %(levelname)s | %(message)s`

**PromptManager** (`prompt_manager.py`):
- **Purpose**: YAML-based prompt template management with Jinja2 rendering
- **Features**:
  - YAML file loading with nested key support (dot notation)
  - Jinja2 template compilation and caching
  - Section-based prompt loading
  - Template variable injection
- **Methods**: `render_prompt()`, `_load_prompt()`, `_render_template()`, `_traverse_path()`
- **Cache**: Dictionary-based template cache for performance

**Repository Utils** (`repo.py`):
- **Purpose**: Git repository version detection and metadata extraction
- **Function**: `get_repo_version(repo_path: Path) -> str`
- **Output Format**: `{branch}@{commit_hash}` (e.g., `main@a1b2c3d4`)
- **Error Handling**: Returns "unknown" for non-git directories or errors

**Dictionary Utils** (`dict.py`):
- **Purpose**: Recursive configuration merging utilities
- **Function**: `merge_dicts(dict1: dict, dict2: dict) -> dict`
- **Behavior**: Deep merge with dict2 values overriding dict1, recursive for nested dicts

**Retry Client** (`retry_client.py`):
- **Purpose**: HTTP client with exponential backoff retry logic
- **Function**: `create_retrying_client() -> AsyncClient`
- **Features**:
  - Retries on status codes: 429, 502, 503, 504
  - Respects `Retry-After` headers
  - Exponential backoff (1s → 2s → 4s → 8s → 16s)
  - Max 5 attempts, 60s per attempt, 300s total
  - Connection error handling
- **Implementation**: Uses `AsyncTenacityTransport` with `RetryConfig`

**Custom Models** (`custom_models/gemini_provider.py`):
- **Purpose**: Custom Gemini provider with configurable base URL
- **Class**: `CustomGeminiGLA` extends `GoogleGLAProvider`
- **Override**: `base_url` property to support custom endpoints

## Service Definitions

### **AnalyzerAgent Service**

**Input Contract**:
- `repo_path`: Path to repository for analysis
- `exclude_code_structure`: Boolean flag to skip structure analysis
- `exclude_data_flow`: Boolean flag to skip data flow analysis
- `exclude_dependencies`: Boolean flag to skip dependency analysis
- `exclude_request_flow`: Boolean flag to skip request flow analysis
- `exclude_api_analysis`: Boolean flag to skip API analysis

**Output Contract**:
- Up to 5 markdown files in `{repo_path}/.ai/docs/`:
  - `structure_analysis.md` - Architectural overview and component analysis
  - `dependency_analysis.md` - Internal and external dependency mapping
  - `data_flow_analysis.md` - Data transformation and persistence patterns
  - `request_flow_analysis.md` - Request processing and flow analysis
  - `api_analysis.md` - API endpoint and integration documentation

**Capabilities**:
- Concurrent execution of specialized analysis agents with error isolation
- Partial success handling (continues if some agents fail)
- File system traversal and code examination through tools
- Architectural pattern recognition and component relationship mapping
- Path normalization (removes absolute paths from output)

**Error Handling**:
- Individual agent failures logged but don't stop other agents
- Validation ensures at least one analysis file is generated
- Complete failure only if all agents fail

### **DocumenterAgent Service**

**Input Contract**:
- `repo_path`: Path to repository
- `readme`: `ReadmeConfig` object with section exclusion flags:
  - `exclude_project_overview`: Skip project overview section
  - `exclude_table_of_contents`: Skip TOC
  - `exclude_architecture`: Skip architecture section
  - `exclude_c4_model`: Skip C4 model diagrams
  - `exclude_repository_structure`: Skip directory structure
  - `exclude_dependencies_and_integration`: Skip dependencies section
  - `exclude_api_documentation`: Skip API documentation
  - `exclude_development_notes`: Skip development notes
  - `exclude_known_issues_and_limitations`: Skip known issues
  - `exclude_additional_documentation`: Skip additional docs links
  - `use_existing_readme`: Incorporate existing README content

**Output Contract**:
- `README.md` file in repository root with configurable sections

**Capabilities**:
- Multi-source analysis integration (reads existing analysis files from `.ai/docs/`)
- Configurable section inclusion/exclusion (9 different section types)
- Existing README preservation and integration option
- Structured markdown generation with consistent formatting
- C4 model diagram generation (context and container levels)
- Mermaid diagram support for architecture visualization

**Model Support**:
- OpenAI-compatible models
- Google Gemini models (with custom provider)

### **Cronjob Service**

**Input Contract**:
- `max_days_since_last_commit`: Filter projects by activity (default: 30 days)
- `working_path`: Temporary directory for cloning (default: `/tmp/cronjob/projects`)
- `group_project_id`: GitLab group ID to analyze (default: 3)
- GitLab OAuth token for authentication

**Output Contract**:
- Automated analysis execution for applicable projects
- Merge requests created in target repositories with:
  - Branch name: `ai-analysis-{YYYY-MM-DD}`
  - Commit message: `[AI] Analyzer-Agent: Create/Update AI Analysis [skip ci]`
  - MR title includes project name and date
  - MR description includes analyzer version

**Capabilities**:
- GitLab API integration for project discovery with subgroup support
- Automated repository cloning with cleanup
- Branch creation and merge request management
- Project filtering based on:
  - Archive status
  - Subgroup membership
  - Project ID exclusion list
  - Commit history (not already analyzed)
  - Recent activity
  - Existing branch/MR checks
- Error isolation (individual project failures don't stop batch)

**Workflow**:
1. Fetch projects from GitLab group
2. Filter applicable projects
3. Clone repository to working directory
4. Create analysis branch
5. Run analyzer with project-specific config
6. Commit and push changes
7. Create merge request
8. Cleanup working directory

## Interface Contracts

### **Handler Interface**

```python
class AbstractHandler(ABC):
    @abstractmethod
    async def handle(self):
        """Execute the handler's primary operation"""
        pass
```

**Implementations**:
- `AnalyzeHandler`: Runs multi-agent code analysis
- `ReadmeHandler`: Generates README documentation
- `JobAnalyzeHandler`: Automates GitLab project analysis

### **Configuration Contracts**

**BaseHandlerConfig**:
```python
class BaseHandlerConfig(BaseModel):
    repo_path: Path  # Required: repository path
    config: Optional[str]  # Optional: config file path
    
    @model_validator(mode="after")
    def resolve_config_path(self) -> "BaseHandlerConfig":
        """Auto-resolve config path if not specified"""
```

**AnalyzerAgentConfig**:
```python
class AnalyzerAgentConfig(BaseModel):
    repo_path: Path
    exclude_code_structure: bool = False
    exclude_data_flow: bool = False
    exclude_dependencies: bool = False
    exclude_request_flow: bool = False
    exclude_api_analysis: bool = False
```

**DocumenterAgentConfig**:
```python
class DocumenterAgentConfig(BaseModel):
    repo_path: Path
    readme: ReadmeConfig = Field(default_factory=ReadmeConfig)

class ReadmeConfig(BaseModel):
    exclude_project_overview: bool = False
    exclude_table_of_contents: bool = False
    exclude_architecture: bool = False
    exclude_c4_model: bool = False
    exclude_repository_structure: bool = False
    exclude_dependencies_and_integration: bool = False
    exclude_api_documentation: bool = False
    exclude_development_notes: bool = False
    exclude_known_issues_and_limitations: bool = False
    exclude_additional_documentation: bool = False
    use_existing_readme: bool = False
```

**JobAnalyzeHandlerConfig**:
```python
class JobAnalyzeHandlerConfig(BaseModel):
    max_days_since_last_commit: Optional[int] = 30
    working_path: Optional[Path] = Path("/tmp/cronjob/projects")
    group_project_id: Optional[int] = 3
```

### **Tool Interface** (pydantic-ai Tool)

**FileReadTool**:
```python
def _run(file_path: str, line_number: int = 0, line_count: int = 200) -> str:
    """
    Read a file and return its contents.
    
    Args:
        file_path: Path to the file to read
        line_number: Starting line number (default: 0)
        line_count: Number of lines to read (default: 200)
    
    Returns:
        Formatted string with file contents and metadata
    
    Raises:
        ModelRetry: On file access errors
    """
```

**ListFilesTool**:
```python
def _run(directory: str, 
         ignored_dirs: Optional[List[str]] = None,
         ignored_extensions: Optional[List[str]] = None) -> str:
    """
    List files in a directory recursively with filtering.
    
    Args:
        directory: Directory path to list
        ignored_dirs: Additional directories to ignore
        ignored_extensions: Additional extensions to ignore
    
    Returns:
        Formatted string with files grouped by directory
    """
```

### **Agent Output Contracts**

**AnalyzerResult**:
```python
# Output type: str (markdown content)
# Written to: {repo_path}/.ai/docs/{analysis_type}_analysis.md
```

**DocumenterResult**:
```python
class DocumenterResult(BaseModel):
    markdown_content: str  # The complete README markdown
```

## Design Patterns Identified

### 1. **Multi-Agent Coordination Pattern**

**Implementation**: `AnalyzerAgent` coordinates 5 specialized agents
- Concurrent execution with `asyncio.gather(return_exceptions=True)`
- Error isolation - individual failures don't cascade
- Graceful degradation with partial success handling
- Each agent has distinct system prompt and output file

**Benefits**:
- Parallel processing for improved performance
- Specialized expertise per analysis domain
- Resilient to individual agent failures

### 2. **Command Pattern with Dynamic CLI**

**Implementation**: Handler-based command execution
- `AbstractHandler` interface with `handle()` method
- Dynamic argument generation from Pydantic models using reflection
- Command routing in `main()` using match statement
- Configurable command parameters with type validation

**Key Functions**:
- `add_handler_args()`: Generates CLI arguments from Pydantic model fields
- `_add_field_arg()`: Recursively processes nested models and boolean flags
- `parse_args()`: Creates subparsers for each command

**Benefits**:
- Type-safe CLI with automatic validation
- Self-documenting arguments from Pydantic field descriptions
- Consistent interface across commands

### 3. **Template Method Pattern**

**Implementation**: Base handler with common initialization
- `BaseHandler` provides shared configuration logic
- `resolve_config_path()` validator in `BaseHandlerConfig`
- Specialized `handle()` implementations in concrete handlers
- Shared configuration validation and path resolution

**Benefits**:
- Code reuse for common handler operations
- Consistent configuration handling
- Easy to add new handlers

### 4. **Strategy Pattern**

**Implementation**: Multiple strategies for configuration and execution
- Configurable analysis exclusions with boolean flags
- Multiple LLM provider support (OpenAI/Gemini) with provider abstraction
- Flexible output formatting and section configuration
- Model selection based on configuration

**Examples**:
- `AnalyzerAgentConfig` exclusion flags determine which agents run
- `ReadmeConfig` section flags control documentation structure
- Provider selection in `DocumenterAgent._llm_model` property

### 5. **Factory Pattern**

**Implementation**: Dynamic object creation based on configuration
- Agent creation through property methods (`_structure_analyzer_agent`, etc.)
- Tool instantiation and registration with pydantic-ai
- Model provider selection with custom provider implementations
- Handler instantiation based on command

**Examples**:
```python
@property
def _structure_analyzer_agent(self) -> Agent:
    model, model_settings = self._llm_model
    return Agent(
        name="Structure Analyzer",
        model=model,
        model_settings=model_settings,
        tools=[FileReadTool().get_tool(), ListFilesTool().get_tool()],
        ...
    )
```

### 6. **Observer Pattern**

**Implementation**: OpenTelemetry tracing integration
- Span events for agent execution milestones
- Structured logging with contextual information
- Progress tracking and performance monitoring
- Automatic instrumentation of pydantic-ai and httpx

**Examples**:
- `trace.get_current_span().add_event()` for agent start
- `span.set_attributes()` for execution metadata
- Usage tracking (tokens, time) logged after completion

### 7. **Retry Pattern**

**Implementation**: Multiple levels of retry logic
- Exponential backoff for LLM requests via `create_retrying_client()`
- Configurable retry counts for agents and tools
- Circuit breaker-like behavior for failed operations
- Respects server `Retry-After` headers

**Configuration**:
- Agent retries: `ANALYZER_AGENT_RETRIES`, `DOCUMENTER_AGENT_RETRIES` (default: 2)
- Tool retries: `TOOL_FILE_READER_MAX_RETRIES`, `TOOL_LIST_FILES_MAX_RETRIES` (default: 2)
- HTTP retries: 5 attempts with exponential backoff (1s → 60s max)

### 8. **Singleton Pattern**

**Implementation**: Logger class with class-level state
- Single `_logger` instance shared across application
- `init()` method prevents re-initialization
- Class methods for logging operations
- Consistent logging configuration throughout lifecycle

### 9. **Dependency Injection Pattern**

**Implementation**: Configuration-based dependency injection
- Handlers receive configuration objects in constructor
- Agents instantiated with config objects
- Tools registered with agents during creation
- No global state except logger and config module

**Benefits**:
- Testable components
- Clear dependency boundaries
- Easy to mock for testing

### 10. **Builder Pattern (Implicit)**

**Implementation**: Configuration building through multi-source merging
- `load_config()` builds final configuration from multiple sources
- Precedence: defaults → file → CLI arguments
- Recursive merging for nested configurations
- Validation through Pydantic models

## Component Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Entry Point                          │
│                         (main.py)                               │
│  - Dynamic argument parsing from Pydantic models                │
│  - Command routing (analyze, document, cronjob)                 │
│  - Observability setup (Langfuse/OpenTelemetry)                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Configuration System                          │
│                      (config.py)                                │
│  - Multi-source loading (env, YAML, CLI)                        │
│  - Hierarchical merging with precedence                         │
│  - Pydantic validation                                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Handler Layer                              │
│                   (handlers/*.py)                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Analyze    │  │   Readme     │  │   Cronjob    │          │
│  │   Handler    │  │   Handler    │  │   Handler    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────┐
│   AnalyzerAgent     │  │  DocumenterAgent    │  │ GitLab API   │
│   (analyzer.py)     │  │  (documenter.py)    │  │ Integration  │
│                     │  │                     │  │              │
│  ┌───────────────┐  │  │  - README gen      │  │ - Project    │
│  │ 5 Sub-Agents: │  │  │  - Section config  │  │   discovery  │
│  │ - Structure   │  │  │  - Multi-source    │  │ - Clone/MR   │
│  │ - Dependencies│  │  │    analysis        │  │ - Automation │
│  │ - Data Flow   │  │  └─────────────────────┘  └──────────────┘
│  │ - Request Flow│  │
│  │ - API         │  │
│  └───────┬───────┘  │
└──────────┼──────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Tool System                              │
│                   (agents/tools/*.py)                           │
│  ┌──────────────────┐              ┌──────────────────┐         │
│  │  FileReadTool    │              │  ListFilesTool   │         │
│  │  - Line ranges   │              │  - Filtering     │         │
│  │  - Retry logic   │              │  - Grouping      │         │
│  └──────────────────┘              └──────────────────┘         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Utility Layer                              │
│                     (utils/*.py)                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Logger  │  │  Prompt  │  │  Retry   │  │   Repo   │        │
│  │          │  │  Manager │  │  Client  │  │   Utils  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

**Data Flow Diagram**:

```
CLI Arguments ──┐
                ├──> Configuration Loading ──> Handler Selection
YAML Config ────┤                                      │
                │                                      ▼
Env Variables ──┘                              Handler Execution
                                                       │
                                                       ▼
                                               Agent Instantiation
                                                       │
                                                       ▼
                                               Tool Registration
                                                       │
                                                       ▼
                                               LLM Interaction
                                                       │
                                                       ▼
                                               Tool Execution
                                                       │
                                                       ▼
                                               Result Generation
                                                       │
                                                       ▼
                                               File Output
                                                       │
                                                       ▼
                                               Logging/Tracing
```

**Dependency Relationships**:

- **main.py** → handlers, config, utils.Logger
- **handlers/** → agents, config, utils (Logger, repo)
- **agents/** → config, utils (Logger, PromptManager, retry_client), tools
- **tools/** → config, utils.Logger
- **utils/** → minimal internal