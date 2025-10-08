Now I have a comprehensive understanding of the codebase. Let me create the data flow analysis document:

# Data Flow Analysis

## Data Models Overview

The AI Documentation Generator uses **Pydantic models** as the primary data modeling approach throughout the application. All configuration, agent inputs/outputs, and structured data are represented using Pydantic's BaseModel classes, providing automatic validation, serialization, and type safety.

### Core Configuration Models

**BaseHandlerConfig** (`src/handlers/base_handler.py`)
- **Purpose**: Base configuration for all handlers with repository path validation
- **Fields**:
  - `repo_path: Path` - Target repository path (required, validated for existence)
  - `config: Optional[str]` - Configuration file path (auto-resolved to `.ai/config.yaml` if not specified)
- **Validation**: Post-initialization validator ensures repository exists and resolves default config paths
- **Inheritance**: Extended by all handler-specific configurations

**AnalyzerAgentConfig** (`src/agents/analyzer.py`)
- **Purpose**: Configuration for code analysis agent with exclusion flags
- **Fields**:
  - `repo_path: Path` - Repository to analyze
  - `exclude_code_structure: bool` - Skip structure analysis (default: False)
  - `exclude_data_flow: bool` - Skip data flow analysis (default: False)
  - `exclude_dependencies: bool` - Skip dependency analysis (default: False)
  - `exclude_request_flow: bool` - Skip request flow analysis (default: False)
  - `exclude_api_analysis: bool` - Skip API analysis (default: False)
- **Composition**: Combined with BaseHandlerConfig to form AnalyzeHandlerConfig

**ReadmeConfig** (`src/agents/documenter.py`)
- **Purpose**: Fine-grained control over README section generation
- **Fields**: 10 boolean flags for excluding specific sections:
  - `exclude_project_overview`, `exclude_table_of_contents`, `exclude_architecture`
  - `exclude_c4_model`, `exclude_repository_structure`, `exclude_dependencies_and_integration`
  - `exclude_api_documentation`, `exclude_development_notes`, `exclude_known_issues_and_limitations`
  - `exclude_additional_documentation`, `use_existing_readme`
- **Default**: All sections included by default (all flags False)

**DocumenterAgentConfig** (`src/agents/documenter.py`)
- **Purpose**: Configuration for documentation generation agent
- **Fields**:
  - `repo_path: Path` - Repository path
  - `readme: ReadmeConfig` - Nested configuration for README sections (factory default)
- **Composition**: Nested model structure with ReadmeConfig

**JobAnalyzeHandlerConfig** (`src/handlers/cronjob.py`)
- **Purpose**: Configuration for automated GitLab project analysis
- **Fields**:
  - `max_days_since_last_commit: Optional[int]` - Activity filter (default: 30 days)
  - `working_path: Optional[Path]` - Temporary clone directory (default: `/tmp/cronjob/projects`)
  - `group_project_id: Optional[int]` - GitLab group ID (default: 3)
- **Usage**: Controls batch processing behavior for cronjob operations

### Agent Output Models

**DocumenterResult** (`src/agents/documenter.py`)
- **Purpose**: Structured output from documentation generation agent
- **Fields**:
  - `markdown_content: str` - Generated README markdown content
- **Validation**: Pydantic ensures field presence and type correctness
- **Usage**: Returned by DocumenterAgent.run() and written to README.md

**AnalyzerResult** (implicit)
- **Type**: `str` (raw markdown content)
- **Format**: Unstructured markdown text conforming to predefined templates
- **Files Generated**:
  - `structure_analysis.md` - Architectural overview
  - `dependency_analysis.md` - Dependency mapping
  - `data_flow_analysis.md` - Data flow documentation
  - `request_flow_analysis.md` - Request processing flow
  - `api_analysis.md` - API documentation
- **Validation**: File existence checked post-execution via `validate_succession()`

### Environment Configuration Data

**Environment Variables** (`src/config.py`)
- **Loading**: Via `python-dotenv` from `.env` files
- **Type Conversion**: Custom `str_to_bool()` function for boolean values
- **Categories**:
  - **Analyzer LLM**: Model, base URL, API key, timeout, tokens, temperature, parallel calls, retries
  - **Documenter LLM**: Same structure as analyzer
  - **Langfuse**: Public/secret keys, host, enable flag
  - **GitLab**: API URL, user credentials, OAuth token
  - **General**: Environment name, log levels
  - **Tools**: Retry counts for file reader and list files tools
  - **HTTP**: Retry configuration (attempts, multiplier, wait times)
- **Validation**: Required variables raise exceptions if missing; optional have defaults

## Data Transformation Map

### Configuration Loading Pipeline

**Multi-Source Configuration Merging** (`src/config.py`)

```
Environment Variables (.env)
    ↓
YAML Configuration File (.ai/config.yaml)
    ↓
CLI Arguments (argparse)
    ↓
Pydantic Model Validation
    ↓
Handler Configuration Object
```

**Transformation Functions**:

1. **load_config_from_file()** - Extracts configuration from YAML files
   - Input: `args` object with repo_path/config attributes, optional `file_key` for nested extraction
   - Process: Resolves config path → Reads YAML → Navigates nested keys via dot notation
   - Output: Dictionary with configuration values or empty dict if not found

2. **load_config_as_dict()** - Extracts CLI arguments matching Pydantic model fields
   - Input: `args` object, `handler_config` Pydantic model class
   - Process: Iterates model fields → Extracts matching args → Handles nested BaseModel recursively
   - Output: Dictionary with CLI-provided values (None values excluded)
   - Special Handling: Path fields converted to Path objects

3. **load_config()** - Main configuration loading with precedence
   - Input: `args`, `handler_config` type, optional `file_key`
   - Process: 
     - Loads file config via `load_config_from_file()`
     - Loads CLI config via `load_config_as_dict()`
     - Merges dictionaries via `merge_dicts()` (CLI overrides file)
     - Instantiates Pydantic model with merged config
   - Output: Validated Pydantic configuration object
   - Precedence: Pydantic defaults < File config < CLI args

4. **merge_dicts()** (`src/utils/dict.py`) - Recursive dictionary merging
   - Input: Two dictionaries (base and override)
   - Process: Recursively merges nested dictionaries, overrides non-dict values
   - Output: Merged dictionary (mutates first argument)

### CLI Argument Generation

**Dynamic Argument Parser** (`src/main.py`)

```
Pydantic Model Fields
    ↓
Field Introspection (model_fields)
    ↓
Argument Type Detection (bool vs other)
    ↓
argparse Argument Creation
    ↓
CLI Parser with Subcommands
```

**Transformation Logic**:
- **_add_field_arg()**: Converts Pydantic field to argparse argument
  - Boolean fields → `store_true` action with None default
  - Nested BaseModel → Recursive field extraction
  - Other types → Standard argument with None default
  - Help text includes field description and defaults
- **add_handler_args()**: Creates argument group for handler configuration
- **parse_args()**: Builds complete parser with subcommands (analyze, document, cronjob)

### Prompt Template Rendering

**Template Processing** (`src/utils/prompt_manager.py`)

```
YAML Prompt File
    ↓
YAML Parsing (yaml.safe_load)
    ↓
Nested Key Navigation (dot notation)
    ↓
Jinja2 Template Compilation
    ↓
Variable Substitution
    ↓
Rendered Prompt String
```

**PromptManager Class**:
- **Initialization**: Loads YAML file, optionally navigates to section
- **_traverse_path()**: Navigates nested dictionaries via dot notation (e.g., "agents.structure_analyzer.system_prompt")
- **render_prompt()**: Renders Jinja2 template with provided variables
- **Caching**: Template objects cached in `_template_cache` dictionary for performance
- **Variables**: Typically includes `repo_path`, `available_ai_docs`, and config flags

### Agent Output Transformation

**Analysis Result Processing** (`src/agents/analyzer.py`)

```
LLM Raw Output (AgentRunResult)
    ↓
Extract output string (result.output)
    ↓
Cleanup absolute paths (_cleanup_output)
    ↓
Write to markdown file
    ↓
File system persistence
```

**_cleanup_output()**: Replaces absolute repository paths with relative "." notation for portability

**Documentation Result Processing** (`src/agents/documenter.py`)

```
LLM Raw Output (AgentRunResult)
    ↓
Extract DocumenterResult object (result.output)
    ↓
Access markdown_content field
    ↓
Write to README.md
    ↓
File system persistence
```

### GitLab Data Transformation

**Project Processing Pipeline** (`src/handlers/cronjob.py`)

```
GitLab API Response (Project objects)
    ↓
Applicability Filtering (_is_applicable_project)
    ↓
Repository Cloning (git clone)
    ↓
Configuration Loading (load_config_from_file)
    ↓
Config Merging (merge_dicts)
    ↓
Analysis Execution (AnalyzeHandler)
    ↓
Git Operations (add, commit, push)
    ↓
Merge Request Creation
```

**Data Transformations**:
- **Project Filtering**: GitLab Project objects → Boolean applicability decision
- **Config Merging**: Project-specific YAML + Base config → AnalyzeHandlerConfig
- **Commit Message**: Template string + version → Git commit message
- **MR Description**: Template + metadata → Merge request description

## Storage Interactions

### File System Operations

**Analysis Output Storage** (`src/agents/analyzer.py`)
- **Location**: `{repo_path}/.ai/docs/`
- **Files Created**:
  - `structure_analysis.md` - Code structure documentation
  - `dependency_analysis.md` - Dependency mapping
  - `data_flow_analysis.md` - Data flow analysis
  - `request_flow_analysis.md` - Request flow documentation
  - `api_analysis.md` - API documentation
- **Write Pattern**: 
  - Check file existence → Create parent directories if needed → Write content
  - Uses Python's built-in `open()` with write mode
  - No atomic writes or locking mechanisms
- **Permissions**: Inherits from parent directory, no explicit permission setting

**Documentation Output Storage** (`src/agents/documenter.py`)
- **Location**: `{repo_path}/README.md`
- **Write Pattern**: Direct file write with parent directory creation
- **Overwrite Behavior**: Completely replaces existing README.md
- **Preservation**: Optional `use_existing_readme` flag reads existing content for context

**Log File Storage** (`src/utils/logger.py`)
- **Location**: `.logs/{repo_name}/{YYYY_MM_DD}/{timestamp}.log`
- **Structure**: Hierarchical directory structure by repository and date
- **Format**: Plain text with timestamp, level, and message
- **Rotation**: Implicit by date-based directory structure
- **Handlers**: Dual output to file and console with separate log levels

**Configuration File Reading** (`src/config.py`)
- **Locations Checked**:
  1. `{repo_path}/.ai/config.yaml`
  2. `{repo_path}/.ai/config.yml`
  3. Custom path via `--config` argument
- **Format**: YAML with nested structure
- **Parsing**: `yaml.safe_load()` for security
- **Error Handling**: Returns empty dict if file not found

**Prompt Template Storage** (`src/utils/prompt_manager.py`)
- **Location**: `src/agents/prompts/analyzer.yaml`, `src/agents/prompts/documenter.yaml`
- **Format**: YAML with nested structure for multiple agents
- **Loading**: One-time load at PromptManager initialization
- **Caching**: Jinja2 templates cached in memory after first render

### Git Repository Interactions

**Repository Cloning** (`src/handlers/cronjob.py`)
- **Method**: `Repo.clone_from()` via GitPython
- **Location**: `{working_path}/{project_name}-{project_id}`
- **Branch**: Clones default branch, then creates new branch
- **Cleanup**: `shutil.rmtree()` in finally block ensures cleanup
- **Configuration**: Sets git user.name and user.email for commits

**Git Operations** (`src/handlers/cronjob.py`)
- **Add**: `repo.git.add(".")` - Stages all changes
- **Commit**: `repo.git.commit("-m", message)` - Creates commit with message
- **Push**: `repo.git.push("origin", branch_name, "-f")` - Force pushes to remote
- **Branch Creation**: `repo.git.checkout("-b", branch_name)` - Creates and switches to new branch

**Repository Metadata** (`src/utils/repo.py`)
- **get_repo_version()**: Extracts branch name and commit hash
- **Commands**: Uses subprocess to run git commands
  - `git rev-parse --is-inside-work-tree` - Validates git repository
  - `git rev-parse --abbrev-ref HEAD` - Gets branch name
  - `git rev-parse --short=8 HEAD` - Gets short commit hash
- **Output Format**: `{branch}@{commit}` (e.g., "main@a1b2c3d4")
- **Error Handling**: Returns "unknown" on any failure

### Tool File Operations

**FileReadTool** (`src/agents/tools/file_tool/file_reader.py`)
- **Operation**: Read file content with line range support
- **Parameters**:
  - `file_path: str` - Path to file
  - `line_number: int` - Starting line (default: 0)
  - `line_count: int` - Number of lines to read (default: 200)
- **Output Format**: Wrapped with metadata (line range, total lines)
- **Error Handling**: 
  - File not found → `ModelRetry` exception
  - Permission denied → `ModelRetry` exception
  - Other errors → `ModelRetry` with error message
- **Retry**: Configurable via `TOOL_FILE_READER_MAX_RETRIES` (default: 2)

**ListFilesTool** (`src/agents/tools/dir_tool/list_files.py`)
- **Operation**: Recursive directory listing with filtering
- **Filtering**:
  - **Ignored Directories**: 100+ patterns (version control, build artifacts, dependencies, caches)
  - **Ignored Extensions**: 100+ patterns (compiled files, archives, media, logs)
- **Output Format**: Files grouped by directory with relative paths
- **Traversal**: `os.walk()` with directory filtering
- **Sorting**: Alphabetical sorting of directories and files
- **Retry**: Configurable via `TOOL_LIST_FILES_MAX_RETRIES` (default: 2)

### No Database Usage

The application **does not use any database systems**. All data persistence is file-based:
- Configuration: YAML files
- Analysis results: Markdown files
- Logs: Text files
- State: Ephemeral in-memory during execution

## Validation Mechanisms

### Pydantic Model Validation

**Automatic Field Validation**
- **Type Checking**: All fields validated against declared types at instantiation
- **Required Fields**: Fields without defaults raise ValidationError if missing
- **Path Validation**: Path fields automatically converted from strings
- **Nested Models**: Recursive validation for nested Pydantic models

**Custom Validators**

**BaseHandlerConfig.resolve_config_path()** (`src/handlers/base_handler.py`)
- **Type**: Post-initialization validator (`@model_validator(mode="after")`)
- **Validation**:
  1. Checks if `repo_path` exists on filesystem
  2. Raises ValueError if repository path doesn't exist
  3. Auto-resolves config path if not explicitly set
  4. Checks for `.ai/config.yaml` then `.ai/config.yml`
- **Timing**: Runs after all fields are set but before model is returned

### Configuration Validation

**Environment Variable Validation** (`src/config.py`)
- **Required Variables**: Raise KeyError if missing (e.g., `ANALYZER_LLM_MODEL`)
- **Type Conversion**: `str_to_bool()` validates boolean strings
  - Valid True: "true", "1", "yes", "y" (case-insensitive)
  - Valid False: "false", "0", "no", "n" (case-insensitive)
  - Invalid: Raises ValueError with message
- **Integer Conversion**: `int()` with potential ValueError on invalid input
- **Float Conversion**: `float()` with potential ValueError on invalid input

**YAML Configuration Validation** (`src/config.py`)
- **Parsing**: `yaml.safe_load()` raises YAMLError on malformed YAML
- **Key Navigation**: `load_config_from_file()` returns empty dict if keys not found
- **No Schema Validation**: YAML structure not validated until Pydantic instantiation

### Agent Execution Validation

**Analysis Completion Validation** (`src/agents/analyzer.py`)
- **Method**: `validate_succession(analysis_files: List[Path])`
- **Logic**:
  - Checks existence of all expected analysis files
  - **Complete Success**: All files exist → Info log
  - **Complete Failure**: No files exist → Error log + ValueError raised
  - **Partial Success**: Some files exist → Warning log, continues execution
- **Timing**: Called after all agents complete (including failures)
- **Purpose**: Ensures at least some analysis succeeded before proceeding

**Documentation Validation** (`src/agents/documenter.py`)
- **Method**: `validate_succession()` (defined but not called in current code)
- **Logic**: Checks if README.md exists, raises ValueError if not
- **Status**: Validation method exists but not invoked in run flow

### Tool Input Validation

**FileReadTool Validation** (`src/agents/tools/file_tool/file_reader.py`)
- **File Existence**: Checks `os.path.exists()` before reading
- **Error Handling**: Raises `ModelRetry` for:
  - File not found
  - Permission denied
  - Any other read errors
- **Retry Behavior**: pydantic-ai automatically retries on `ModelRetry` exceptions

**ListFilesTool Validation** (`src/agents/tools/dir_tool/list_files.py`)
- **Path Normalization**: Strips trailing slashes from directory paths
- **Directory Filtering**: Skips ignored directories during traversal
- **Extension Filtering**: Skips files with ignored extensions
- **No Explicit Validation**: Assumes directory exists (os.walk handles non-existent paths)

### GitLab Integration Validation

**Project Applicability Validation** (`src/handlers/cronjob.py`)
- **Method**: `_is_applicable_project(project: Project) -> bool`
- **Checks**:
  1. **Not Archived**: `project.archived == False`
  2. **Not in Ignored Subgroups**: Checks namespace path against `IGNORED_SUBGROUPS`
  3. **Not in Ignored Projects**: Checks project ID against `IGNORED_PROJECTS` list
  4. **Not Already Analyzed**: Last commit message doesn't contain analysis marker
  5. **Recent Activity**: Last commit within `max_days_since_last_commit`
  6. **No Existing Branch**: Today's analysis branch doesn't exist
  7. **No Open MR**: No open merge request from analyzer agent
- **Return**: Boolean indicating if project should be processed

### LLM Response Validation

**Structured Output Validation** (`src/agents/documenter.py`)
- **Output Type**: `DocumenterResult` Pydantic model
- **Validation**: pydantic-ai validates LLM response against model schema
- **Error Handling**: `UnexpectedModelBehavior` exception if validation fails
- **Retry**: Automatic retry on validation failure (up to configured retries)

**Unstructured Output** (`src/agents/analyzer.py`)
- **Output Type**: `str` (no validation)
- **Format**: Markdown text conforming to template structure
- **Validation**: None - relies on LLM following instructions
- **Quality Check**: File existence validation post-execution

## State Management Analysis

### Stateless Architecture

The AI Documentation Generator follows a **stateless, ephemeral execution model** with no persistent state between runs. Each execution is independent and self-contained.

### Execution State

**In-Memory State During Execution**
- **Handler Instances**: Created per command execution, destroyed after completion
- **Agent Instances**: Created per handler execution, destroyed after completion
- **Configuration Objects**: Loaded at startup, immutable during execution
- **LLM Conversation Context**: Maintained by pydantic-ai during agent run, discarded after
- **File Handles**: Opened and closed within function scope
- **HTTP Clients**: Created with retry logic, closed after use

**No State Persistence Between Runs**
- No session management
- No user state tracking
- No execution history database
- No cached analysis results
- Each run starts fresh with clean state

### Concurrent Execution State

**Multi-Agent Concurrency** (`src/agents/analyzer.py`)
- **Pattern**: `asyncio.gather(*tasks, return_exceptions=True)`
- **Isolation**: Each agent runs in separate async task
- **Shared State**: Read-only access to configuration and repository files
- **No Synchronization**: Agents write to different files, no locking needed
- **Error Isolation**: Individual agent failures don't affect others
- **Result Collection**: Results gathered after all agents complete

**Task State Management**
```python
tasks = []  # List of coroutines
results = await asyncio.gather(*tasks, return_exceptions=True)
# Results contain either output or exception for each task
```

### Configuration State

**Immutable Configuration**
- **Loading**: Configuration loaded once at handler initialization
- **Lifecycle**: Configuration object passed to agents, never modified
- **Scope**: Configuration scoped to single execution
- **Thread Safety**: Immutable objects are inherently thread-safe

**Environment Variables**
- **Loading**: Loaded once at module import via `load_dotenv()`
- **Scope**: Global module-level constants
- **Mutability**: Never modified after initial load
- **Access**: Direct access via `config.VARIABLE_NAME`

### Logging State

**Logger Singleton** (`src/utils/logger.py`)
- **Pattern**: Class-level `_logger` attribute (singleton-like)
- **Initialization**: `Logger.init()` called once per execution
- **State**: Logger instance and handlers maintained for execution duration
- **Thread Safety**: Python logging module is thread-safe
- **Cleanup**: Implicit cleanup at process termination

**Log File State**
- **Creation**: New log file per execution with timestamp
- **Appending**: Log entries appended to file during execution
- **Rotation**: No explicit rotation, new file per run
- **Persistence**: Log files persist after execution completes

### Git Repository State

**Temporary Repository State** (`src/handlers/cronjob.py`)
- **Cloning**: Fresh clone for each project analysis
- **Location**: `{working_path}/{project_name}-{project_id}`
- **Modifications**: Analysis files added, committed, pushed
- **Cleanup**: Repository deleted after processing (in finally block)
- **Isolation**: Each project processed in separate directory

**Branch State**
- **Creation**: New branch created per analysis run
- **Naming**: `ai-analysis-{YYYY-MM-DD}` (date-based)
- **Lifecycle**: Created → Modified → Pushed → Deleted locally
- **Remote State**: Branch persists on GitLab after push

### HTTP Client State

**Retry Client State** (`src/utils/retry_client.py`)
- **Creation**: New AsyncClient per agent
- **Configuration**: Retry logic configured at creation
- **State**: Connection pool maintained during agent execution
- **Cleanup**: Async context manager ensures proper cleanup
- **Isolation**: Each agent has independent HTTP client

**LLM Provider State**
- **Connection**: Stateless HTTP requests to LLM API
- **Context**: Conversation context maintained by pydantic-ai during run
- **Persistence**: No state persisted between runs
- **Rate Limiting**: Handled by retry logic, no state tracking

### Cache State

**Template Cache** (`src/utils/prompt_manager.py`)
- **Type**: In-memory dictionary cache
- **Scope**: Per PromptManager instance
- **Lifecycle**: Created at initialization, destroyed at end of execution
- **Key**: Template string
- **Value**: Compiled Jinja2 Template object
- **Eviction**: No eviction policy, cache grows unbounded (limited by template count)

**No Other Caching**
- No HTTP response caching
- No analysis result caching
- No configuration caching between runs
- No file content caching

### OpenTelemetry Tracing State

**Span State** (`src/handlers/analyze.py`, `src/handlers/readme.py`)
- **Creation**: Spans created for each handler and agent execution
- **Context**: Span context propagated through execution
- **Attributes**: Metadata attached to spans (repo_path, version, config)
- **Lifecycle**: Span opened → Operations traced → Span closed
- **Export**: Spans exported to Langfuse if enabled

**Instrumentation State**
- **Setup**: `logfire.configure()` called once at startup
- **Scope**: Global instrumentation for pydantic-ai and httpx
- **Persistence**: Traces sent to external service, not stored locally

## Serialization Processes

### Configuration Serialization

**YAML Deserialization** (`src/config.py`)
- **Format**: YAML to Python dictionary
- **Library**: `yaml.safe_load()` from PyYAML
- **Process**:
  1. Read YAML file as text
  2. Parse YAML to nested dictionaries
  3. Navigate nested structure via dot notation
  4. Extract relevant configuration section
- **Type Conversion**: YAML types mapped to Python types (str, int, bool, list, dict)
- **No Serialization**: Configuration never serialized back to YAML

**Environment Variable Deserialization** (`src/config.py`)
- **Format**: String to typed values
- **Process**:
  - Strings: Direct assignment
  - Booleans: Custom `str_to_bool()` function
  - Integers: `int()` conversion
  - Floats: `float()` conversion
- **No Serialization**: Environment variables never written back

**Pydantic Model Serialization**
- **Deserialization**: Dictionary to Pydantic model via `**kwargs` unpacking
- **Validation**: Automatic type conversion and validation during instantiation
- **Serialization**: `model_dump()` method available but not used in codebase
- **JSON Support**: Pydantic provides JSON serialization but not utilized

### Prompt Template Serialization

**YAML to Template** (`src/utils/prompt_manager.py`)
- **Format**: YAML string to Jinja2 Template object
- **Process**:
  1. Load YAML file to dictionary
  2. Extract prompt string via dot notation
  3. Compile string to Jinja2 Template
  4. Cache compiled template
- **Rendering**: Template + variables → Rendered string
- **No Reverse**: Templates never serialized back to YAML

**Template Variable Injection**
- **Format**: Python dictionary to template context
- **Process**: `template.render(**kwargs)` injects variables
- **Types**: All Python types supported (str, int, bool, list, dict)
- **Output**: Rendered string with variables substituted

### LLM Communication Serialization

**Request Serialization** (via pydantic-ai)
- **Format**: Python objects to JSON for HTTP requests
- **Process**:
  1. Agent configuration → OpenAI-compatible JSON
  2. System prompt → JSON string field
  3. User prompt → JSON string field
  4. Tool definitions → JSON schema
  5. Model settings → JSON parameters
- **Library**: pydantic-ai handles serialization internally
- **Protocol**: OpenAI Chat Completions API format

**Response Deserialization** (via pydantic-ai)
- **Format**: JSON to Python objects
- **Process**:
  1. HTTP response → JSON parsing
  2. JSON → pydantic-ai internal structures
  3. Structured output → Pydantic model validation
  4. Unstructured output → String extraction
- **Error Handling**: JSON parsing errors caught and retried
- **Validation**: Pydantic validates structured outputs

**Tool Call Serialization**
- **Request**: Tool parameters serialized to JSON by pydantic-ai
- **Response**: Tool return values serialized to JSON for LLM
- **Format**: OpenAI function calling format
- **Example**:
  ```json
  {
    "name": "Read-File",
    "arguments": {
      "file_path": "/path/to/file",
      "line_number": 0,
      "line_count": 200
    }
  }
  ```

### File Output Serialization

**Markdown File Writing**
- **Format**: Python string to UTF-8 text file
- **Process**:
  1. LLM output → String extraction
  2. Path cleanup (absolute → relative)
  3. String → File write
- **Encoding**: Default UTF-8 (implicit)
- **No Parsing**: Markdown written as plain text, no parsing

**Log File Serialization** (`src/utils/logger.py`)
- **Format**: Structured data to formatted text
- **Process**:
  1. Log message + data dictionary
  2. Format data as JSON string via `_format_data()`
  3. Combine message and JSON
  4. Write to log file with timestamp and level
- **JSON Serialization**: `ujson.dumps()` for data dictionaries
- **Format**: `{timestamp} | {level} | {message} | {json_data}`

### Git Data Serialization

**Commit Message Serialization** (`src/handlers/cronjob.py`)
- **Format**: Python string to Git commit message
- **Process**:
  1. Template string + variables
  2. String formatting
  3. Git commit command with message
- **Encoding**: UTF-8 (Git default)
- **Structure**: Title + body with metadata

**Merge Request Serialization** (`src/handlers/cronjob.py`)
- **Format**: Python dictionary to GitLab API JSON
- **Process**:
  1. MR parameters → Dictionary
  2. python-gitlab library serializes to JSON
  3. HTTP POST to GitLab API
- **Fields**: source_branch, target_branch, title, description
- **Library**: python-gitlab handles serialization

### HTTP Retry Serialization

**Retry State Serialization** (`src/utils/retry_client.py`)
- **Format**: HTTP response to retry decision
- **Process**:
  1. HTTP response → Status code extraction
  2. Status code → Boolean retry decision
  3. Retry-After header → Wait time
- **No Persistence**: Retry state ephemeral, not serialized

### OpenTelemetry Serialization

**Span Serialization** (via logfire)
- **Format**: Span data to OTLP (OpenTelemetry Protocol)
- **Process**:
  1. Span attributes → Key-value pairs
  2. Span events → Structured events
  3. OTLP serialization → Protobuf or JSON
  4. HTTP export to Langfuse
- **Library**: logfire and OpenTelemetry SDK handle serialization
- **Protocol**: OTLP over HTTP

## Data Lifecycle Diagrams

### Configuration Data Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                     Configuration Lifecycle                      │
└─────────────────────────────────────────────────────────────────┘

[.env File] ──────────────┐
                          │
[.ai/config.yaml] ────────┼──→ [load_config()]
                          │         │
[CLI Arguments] ──────────┘         │
                                    ↓
                          [merge_dicts()] ← Precedence: CLI > File > Env
                                    │
                                    ↓
                          [Pydantic Validation]
                                    │
                                    ↓
                          [Handler Config Object]
                                    │
                                    ↓
                          [Agent Initialization]
                                    │
                                    ↓
                          [Agent Execution] ← Read-only access
                                    │
                                    ↓
                          [Execution Complete]
                                    │
                                    ↓
                          [Config