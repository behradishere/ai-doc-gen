Now I have a comprehensive understanding of the system. Let me create the Request Flow Analysis document:

# Request Flow Analysis

## Entry Points Overview

The AI Documentation Generator is a **CLI-based application** rather than a traditional web service, so "requests" in this context refer to command-line invocations that trigger analysis and documentation workflows. The system has three primary entry points:

### 1. Main Entry Point (`src/main.py`)
The application entry point is the `main()` function which orchestrates the entire request lifecycle:

- **CLI Argument Parsing**: Uses `argparse` with dynamic argument generation from Pydantic models via reflection
- **Command Routing**: Matches commands (`analyze`, `document`, `cronjob`) to their respective handler functions
- **Observability Setup**: Configures Langfuse/OpenTelemetry integration if enabled via `configure_langfuse()`
- **Logging Initialization**: Sets up repository-specific logging directories before handler execution
- **Error Handling**: Catches `SystemExit` exceptions and returns appropriate exit codes

### 2. Command Entry Points
Three distinct command entry points handle different request types:

**Analyze Command** (`analyze()` function):
- **Purpose**: Performs comprehensive code analysis using multiple AI agents
- **Entry**: `ai-doc-gen analyze --repo-path <path> [options]`
- **Configuration Loading**: Loads `AnalyzeHandlerConfig` with hierarchical merging (file → CLI args)
- **Handler Instantiation**: Creates `AnalyzeHandler` with merged configuration
- **Execution**: Awaits `handler.handle()` for async agent orchestration

**Document Command** (`document()` function):
- **Purpose**: Generates comprehensive README documentation from analysis results
- **Entry**: `ai-doc-gen document --repo-path <path> [options]`
- **Configuration Loading**: Loads `ReadmeHandlerConfig` with section exclusion flags
- **Handler Instantiation**: Creates `ReadmeHandler` with documentation configuration
- **Execution**: Awaits `handler.handle()` for async documentation generation

**Cronjob Command** (`cronjob_analyze()` function):
- **Purpose**: Automated GitLab project discovery, analysis, and merge request creation
- **Entry**: `ai-doc-gen cronjob analyze [options]`
- **Configuration Loading**: Loads `JobAnalyzeHandlerConfig` with GitLab integration settings
- **GitLab Client Setup**: Initializes authenticated GitLab client with OAuth token
- **Handler Instantiation**: Creates `JobAnalyzeHandler` with GitLab client and configuration
- **Execution**: Awaits `handler.handle()` for automated project processing

### 3. Programmatic Entry Points
The system also supports direct programmatic access through:

- **Agent Classes**: Direct instantiation of `AnalyzerAgent` and `DocumenterAgent`
- **Handler Classes**: Direct use of `AnalyzeHandler`, `ReadmeHandler`, `JobAnalyzeHandler`
- **Tool Classes**: Direct access to `FileReadTool` and `ListFilesTool` for file operations

## Request Routing Map

The request routing follows a **command pattern** with dynamic CLI argument generation:

### CLI Argument Routing Flow
```
User Command
    ↓
argparse.ArgumentParser.parse_args()
    ↓
Dynamic Argument Generation (add_handler_args())
    ├── Reflects Pydantic model fields
    ├── Generates --flag-name arguments
    ├── Handles boolean flags with store_true
    └── Sets required/optional based on field definitions
    ↓
Command Matching (match statement)
    ├── "analyze" → analyze(args)
    ├── "document" → document(args)
    └── "cronjob" → cronjob_analyze(args)
```

### Configuration Resolution Routing
```
CLI Arguments (args)
    ↓
load_config(args, HandlerConfig, file_key)
    ├── load_config_from_file() → YAML parsing
    │   ├── Checks repo_path/.ai/config.yaml
    │   ├── Checks repo_path/.ai/config.yml
    │   └── Extracts nested keys via dot notation
    ├── load_config_as_dict() → CLI argument extraction
    │   ├── Reflects Pydantic model fields
    │   ├── Extracts matching args attributes
    │   └── Handles nested BaseModel recursively
    └── merge_dicts() → Hierarchical merging
        └── Precedence: defaults → file → CLI args
    ↓
Pydantic Model Instantiation
    ├── Field validation
    ├── Type conversion
    └── Custom validators (@model_validator)
```

### Handler Routing
```
Configuration Object
    ↓
Handler Instantiation
    ├── AnalyzeHandler(config) → AnalyzerAgent
    ├── ReadmeHandler(config) → DocumenterAgent
    └── JobAnalyzeHandler(config, gitlab_client) → Project Discovery
    ↓
handler.handle() Execution
    ├── OpenTelemetry span creation
    ├── Agent execution with tools
    └── Result persistence
```

### Agent Routing (AnalyzerAgent)
```
AnalyzerAgent.run()
    ↓
Concurrent Agent Execution (asyncio.gather)
    ├── Structure Analyzer (if not excluded)
    ├── Dependency Analyzer (if not excluded)
    ├── Data Flow Analyzer (if not excluded)
    ├── Request Flow Analyzer (if not excluded)
    └── API Analyzer (if not excluded)
    ↓
Individual Agent Execution (_run_agent)
    ├── Prompt rendering via PromptManager
    ├── Agent.run() with LLM interaction
    ├── Tool execution (FileReadTool, ListFilesTool)
    └── Result file writing
    ↓
Validation (validate_succession)
    ├── Check all expected files exist
    ├── Log partial success warnings
    └── Raise error only on complete failure
```

### Tool Routing
```
Agent Tool Call
    ↓
pydantic-ai Tool Execution
    ├── FileReadTool._run(file_path, line_number, line_count)
    │   ├── File existence check
    │   ├── Permission validation
    │   ├── Line-based reading (default 200 lines)
    │   └── ModelRetry on errors
    └── ListFilesTool._run(directory)
        ├── os.walk() directory traversal
        ├── Filtering (100+ ignored dirs/extensions)
        ├── Grouping by directory
        └── Sorted output generation
    ↓
Result Return to Agent
```

## Middleware Pipeline

While this is not a traditional web application with HTTP middleware, the system implements several **preprocessing and validation layers** that function similarly:

### 1. Configuration Middleware Layer
**Location**: `src/config.py` - `load_config()` function

**Processing Order**:
1. **Environment Variable Loading** (`load_dotenv()`)
   - Loads `.env` file into environment
   - Type conversion via helper functions (`str_to_bool()`)
   - Validation of required variables

2. **File Configuration Loading** (`load_config_from_file()`)
   - YAML file parsing with `yaml.safe_load()`
   - Nested key traversal via dot notation
   - Default path resolution (`.ai/config.yaml`)

3. **CLI Argument Extraction** (`load_config_as_dict()`)
   - Pydantic model field reflection
   - Argument value extraction from `args` namespace
   - Recursive handling of nested models

4. **Configuration Merging** (`merge_dicts()`)
   - Recursive dictionary merging
   - Precedence: defaults → file → CLI
   - None value filtering (explicit vs. unset)

5. **Pydantic Validation**
   - Type checking and conversion
   - Field requirement validation
   - Custom validators (`@model_validator`)
   - Path existence checks

### 2. Logging Middleware Layer
**Location**: `src/main.py` - `configure_logging()` function

**Processing Order**:
1. **Repository Name Extraction**
   - Derives log directory from repo path
   - Creates timestamped subdirectories

2. **Logger Initialization** (`Logger.init()`)
   - Creates log directory structure
   - Sets up file handler (INFO level)
   - Sets up console handler (WARNING level)
   - Configures structured logging format

3. **Log Propagation Setup**
   - Enables propagation to root logger
   - Integrates with OpenTelemetry/Logfire

### 3. Observability Middleware Layer
**Location**: `src/main.py` - `configure_langfuse()` function

**Processing Order** (if `ENABLE_LANGFUSE=true`):
1. **Authentication Setup**
   - Base64 encodes Langfuse credentials
   - Sets OTEL_EXPORTER_OTLP_HEADERS environment variable

2. **Logfire Configuration**
   - Service name: "ai-doc-gen"
   - Environment-based configuration
   - Disables direct Logfire sending (uses OTLP)

3. **Instrumentation Setup**
   - `logfire.instrument_pydantic_ai()` - Traces agent execution
   - `logfire.instrument_httpx()` - Traces HTTP requests
   - Automatic span creation for all operations

### 4. Handler Validation Layer
**Location**: `src/handlers/base_handler.py` - `BaseHandlerConfig.resolve_config_path()`

**Processing Order**:
1. **Repository Path Validation**
   - Checks path existence
   - Raises ValueError if not found

2. **Config Path Resolution**
   - Checks for `.ai/config.yaml`
   - Falls back to `.ai/config.yml`
   - Sets config attribute if found

### 5. Agent Execution Layer
**Location**: `src/agents/analyzer.py` and `src/agents/documenter.py`

**Processing Order**:
1. **Prompt Template Loading** (`PromptManager`)
   - YAML file parsing
   - Jinja2 template compilation
   - Template caching for performance

2. **LLM Model Setup**
   - HTTP client creation with retry logic
   - Provider selection (OpenAI/Gemini)
   - Model settings configuration (temperature, tokens, timeout)

3. **Tool Registration**
   - FileReadTool instantiation
   - ListFilesTool instantiation
   - Tool attachment to agent

4. **Agent Instantiation**
   - System prompt rendering
   - Model and settings attachment
   - Retry configuration
   - OpenTelemetry instrumentation

### 6. HTTP Retry Middleware Layer
**Location**: `src/utils/retry_client.py` - `create_retrying_client()`

**Processing Order**:
1. **Status Code Validation** (`should_retry_status()`)
   - Checks for retryable errors (429, 502, 503, 504)
   - Raises HTTPStatusError for retry

2. **Retry Logic** (`AsyncTenacityTransport`)
   - Exception type checking (HTTPStatusError, ConnectionError)
   - Retry-After header parsing
   - Exponential backoff fallback (1s → 2s → 4s → 8s → 16s)
   - Maximum 5 attempts
   - Maximum 60s per attempt, 300s total

3. **Error Propagation**
   - Re-raises last exception after all retries
   - Preserves original error context

### 7. Tool Execution Layer
**Location**: `src/agents/tools/`

**Processing Order**:
1. **Tool Call Logging**
   - Debug log with input parameters
   - OpenTelemetry span attribute setting

2. **Input Validation**
   - File/directory existence checks
   - Permission validation
   - Path normalization

3. **Execution with Retry**
   - Configured max retries (default: 2)
   - ModelRetry exception on failures
   - Automatic retry by pydantic-ai

4. **Output Formatting**
   - Structured output generation
   - OpenTelemetry span attribute setting
   - Result return to agent

## Controller/Handler Analysis

The system uses a **handler-based architecture** rather than traditional controllers. Each handler encapsulates the business logic for a specific command:

### Base Handler Architecture
**Location**: `src/handlers/base_handler.py`

**Abstract Base Classes**:
- `AbstractHandler`: Defines the handler interface with abstract `handle()` method
- `BaseHandler`: Extends AbstractHandler with configuration management

**Responsibilities**:
- Configuration storage and access
- Abstract method enforcement
- Common initialization logic

### AnalyzeHandler
**Location**: `src/handlers/analyze.py`

**Configuration**: `AnalyzeHandlerConfig` (extends `BaseHandlerConfig` + `AnalyzerAgentConfig`)
- `repo_path`: Path to repository
- `exclude_code_structure`: Skip structure analysis
- `exclude_data_flow`: Skip data flow analysis
- `exclude_dependencies`: Skip dependency analysis
- `exclude_request_flow`: Skip request flow analysis
- `exclude_api_analysis`: Skip API analysis

**Initialization**:
1. Calls `super().__init__(config)` for base setup
2. Instantiates `AnalyzerAgent(config)` with configuration

**Handle Method Flow**:
1. **Logging**: Logs "Starting analyze handler"
2. **Tracing**: Creates OpenTelemetry span "Analyzer Agent"
3. **Span Attributes**: Sets repo_path, repo_version, exclusion flags
4. **Agent Execution**: Awaits `self.agent.run()`
5. **Result Return**: Returns agent result

**Error Handling**: Exceptions propagate to main() for logging

### ReadmeHandler
**Location**: `src/handlers/readme.py`

**Configuration**: `ReadmeHandlerConfig` (extends `BaseHandlerConfig` + `DocumenterAgentConfig`)
- `repo_path`: Path to repository
- `readme`: Nested `ReadmeConfig` with section exclusion flags
  - `exclude_project_overview`
  - `exclude_table_of_contents`
  - `exclude_architecture`
  - `exclude_c4_model`
  - `exclude_repository_structure`
  - `exclude_dependencies_and_integration`
  - `exclude_api_documentation`
  - `exclude_development_notes`
  - `exclude_known_issues_and_limitations`
  - `exclude_additional_documentation`
  - `use_existing_readme`

**Initialization**:
1. Calls `super().__init__(config)` for base setup
2. Instantiates `DocumenterAgent(config)` with configuration

**Handle Method Flow**:
1. **Logging**: Logs "Starting readme handler"
2. **Tracing**: Creates OpenTelemetry span "Readme Handler"
3. **Span Attributes**: Sets repo_path, repo_version
4. **Agent Execution**: Awaits `self.agent.run()`
5. **Result Return**: Returns agent result

**Error Handling**: Exceptions propagate to main() for logging

### JobAnalyzeHandler (Cronjob)
**Location**: `src/handlers/cronjob.py`

**Configuration**: `JobAnalyzeHandlerConfig`
- `max_days_since_last_commit`: Activity filter (default: 30 days)
- `working_path`: Temporary clone directory (default: `/tmp/cronjob/projects`)
- `group_project_id`: GitLab group ID (default: 3)

**Dependencies**:
- `gitlab_client`: Authenticated GitLab API client

**Initialization**:
1. Stores configuration and GitLab client
2. Creates working directory with `mkdir(parents=True, exist_ok=True)`

**Handle Method Flow**:
1. **Logging**: Logs "Starting cronjob handler"
2. **Group Retrieval**: Gets GitLab group via `gitlab_client.groups.get()`
3. **Project Iteration**: Iterates through group projects with subgroups
4. **Per-Project Processing**:
   - Logs project check
   - Calls `_is_applicable_project()` for filtering
   - Calls `_handle_project()` if applicable
   - Catches and logs exceptions per project (continues on error)

**Project Applicability Checks** (`_is_applicable_project()`):
1. **Archived Check**: Skips archived projects
2. **Subgroup Filter**: Checks against `IGNORED_SUBGROUPS` list
3. **Project ID Filter**: Checks against `IGNORED_PROJECTS` list
4. **Commit Message Check**: Skips if last commit contains analysis title
5. **Activity Check**: Skips if last commit older than `max_days_since_last_commit`
6. **Branch Existence Check**: Skips if today's analysis branch exists
7. **MR Existence Check**: Skips if similar open MR exists

**Project Handling Flow** (`_handle_project()`):
1. **Clone**: `_clone_project()` - Clones repo and creates analysis branch
2. **Analyze**: `_analyze_project()` - Runs AnalyzeHandler on cloned repo
3. **Create MR**: `_create_merge_request()` - Commits and creates GitLab MR
4. **Cleanup**: `_cleanup_project()` - Removes temporary directory (in finally block)

**Clone Process** (`_clone_project()`):
1. Constructs Git URL from project
2. Removes existing project directory if present
3. Clones repository to working path
4. Configures Git user name and email
5. Creates new branch with date-based naming: `ai-analyzer-{YYYY-MM-DD}`
6. Returns Repo object

**Analysis Process** (`_analyze_project()`):
1. Creates `SimpleNamespace` args object with repo path
2. Loads project-specific config from `.ai/config.yaml`
3. Merges with base config (project config takes precedence)
4. Instantiates `AnalyzeHandler` with merged config
5. Awaits `analyzer.handle()`

**MR Creation Process** (`_create_merge_request()`):
1. Stages all changes with `git add .`
2. Commits with standardized message: `[AI] Analyzer-Agent: Create/Update AI Analysis [skip ci]`
3. Includes version in commit message
4. Force pushes to origin
5. Creates merge request via GitLab API with:
   - Source branch: analysis branch
   - Target branch: default branch
   - Title with project name and date
   - Description with version and automation note
   - Skip CI flag

**Cleanup Process** (`_cleanup_project()`):
1. Removes temporary project directory
2. Uses `shutil.rmtree()` with `ignore_errors=True`
3. Logs cleanup completion

**Error Handling**:
- Per-project try-catch with logging
- Continues processing other projects on error
- Finally block ensures cleanup

## Authentication & Authorization Flow

The system has **no internal authentication** for local CLI usage, but integrates with external services that require authentication:

### 1. LLM Service Authentication

**Analyzer LLM Authentication**:
- **Method**: Bearer token authentication
- **Configuration**: 
  - `ANALYZER_LLM_API_KEY` environment variable
  - Passed to OpenAI/Gemini provider
- **Flow**:
  ```
  Agent Initialization
      ↓
  OpenAIProvider(api_key=ANALYZER_LLM_API_KEY)
      ↓
  HTTP Request Headers
      Authorization: Bearer {ANALYZER_LLM_API_KEY}
      ↓
  LLM API Endpoint
  ```
- **Error Handling**: 401/403 errors logged and propagated
- **Retry Logic**: Automatic retry on transient failures (not auth failures)

**Documenter LLM Authentication**:
- **Method**: Bearer token authentication (OpenAI) or API key (Gemini)
- **Configuration**:
  - `DOCUMENTER_LLM_API_KEY` environment variable
  - Provider-specific handling
- **Flow**: Same as Analyzer LLM

### 2. GitLab API Authentication

**OAuth Token Authentication**:
- **Method**: OAuth 2.0 token authentication
- **Configuration**:
  - `GITLAB_OAUTH_TOKEN` environment variable
  - `GITLAB_API_URL` for GitLab instance URL
- **Flow**:
  ```
  Cronjob Handler Initialization
      ↓
  Gitlab(url=GITLAB_API_URL, oauth_token=GITLAB_OAUTH_TOKEN)
      ↓
  GitLab API Requests
      Authorization: Bearer {GITLAB_OAUTH_TOKEN}
      ↓
  GitLab API Endpoints
  ```
- **Permissions Required**:
  - Read access to group projects
  - Write access to repositories (branch creation)
  - Merge request creation permissions
- **Error Handling**: GitLab library handles auth errors with exceptions

**Git Operations Authentication**:
- **Method**: HTTP URL with embedded credentials
- **Flow**:
  ```
  Repository Clone
      ↓
  project.http_url_to_repo (includes OAuth token)
      ↓
  Git Clone/Push Operations
      ↓
  GitLab Repository
  ```
- **User Configuration**:
  - `GITLAB_USER_NAME`: Display name for commits
  - `GITLAB_USER_EMAIL`: Email for commits
  - `GITLAB_USER_USERNAME`: Username for MR filtering

### 3. Observability Service Authentication

**Langfuse Authentication** (Optional):
- **Method**: Basic authentication with base64-encoded credentials
- **Configuration**:
  - `LANGFUSE_PUBLIC_KEY` environment variable
  - `LANGFUSE_SECRET_KEY` environment variable
  - `LANGFUSE_HOST` for Langfuse instance URL
- **Flow**:
  ```
  configure_langfuse()
      ↓
  base64.b64encode(f"{PUBLIC_KEY}:{SECRET_KEY}")
      ↓
  OTEL_EXPORTER_OTLP_HEADERS environment variable
      Authorization: Basic {base64_credentials}
      ↓
  OpenTelemetry Exporter
      ↓
  Langfuse API
  ```
- **Error Handling**: Optional service - failures don't affect core functionality
- **Instrumentation**: Automatic via logfire integration

### 4. File System Authorization

**Local File Access**:
- **Method**: Operating system file permissions
- **Validation**:
  - Repository path existence check in `BaseHandlerConfig.resolve_config_path()`
  - Permission checks in `FileReadTool._run()`
- **Error Handling**:
  ```python
  try:
      with open(file_path, "r") as file:
          # Read file
  except PermissionError:
      raise ModelRetry(message="Permission denied when trying to read file")
  ```
- **Required Permissions**:
  - Read access to repository files
  - Write access to `.ai/docs/` directory
  - Write access to `README.md` file
  - Write access to `.logs/` directory

### 5. Configuration Security

**Sensitive Data Handling**:
- **Environment Variables**: All sensitive data stored in environment variables
- **No Hardcoding**: No API keys or tokens in code
- **`.env` File**: Local development uses `.env` file (gitignored)
- **Configuration Files**: YAML configs contain no sensitive data

**Security Best Practices**:
- API keys loaded via `os.environ[]` (fails if not set)
- OAuth tokens never logged
- Credentials not included in OpenTelemetry spans
- `.env.sample` provides template without actual values

## Error Handling Pathways

The system implements **multi-layered error handling** with graceful degradation:

### 1. CLI Entry Point Error Handling
**Location**: `src/main.py` - `main()` function

**Error Types**:
- **SystemExit**: Caught from argparse for invalid arguments
  ```python
  try:
      args = parse_args()
  except SystemExit as e:
      return e.code
  ```
- **No Command**: Returns exit code 1 with error message
  ```python
  if not args.command:
      print("Error: Please specify a command (analyze, document, cronjob)")
      return 1
  ```
- **Unhandled Exceptions**: Propagate to Python runtime for stack trace

### 2. Configuration Error Handling
**Location**: `src/config.py`

**Error Types**:
- **Missing Environment Variables**: Raises `KeyError` with variable name
  ```python
  ANALYZER_LLM_MODEL = os.environ["ANALYZER_LLM_MODEL"]  # Fails if not set
  ```
- **Invalid Boolean Values**: Raises `ValueError` in `str_to_bool()`
  ```python
  def str_to_bool(value: str) -> bool:
      if value.lower() in ["true", "1", "yes", "y"]:
          return True
      elif value.lower() in ["false", "0", "no", "n"]:
          return False
      else:
          raise ValueError(f"Invalid boolean value: {value}")
  ```
- **YAML Parsing Errors**: Raises `yaml.YAMLError` with file path
- **Missing Config Keys**: Returns empty dict (graceful degradation)
  ```python
  try:
      for key in file_key.split("."):
          config = config[key]
  except KeyError:
      config = {}
  ```

**Pydantic Validation Errors**:
- **Invalid Types**: Raises `ValidationError` with field details
- **Missing Required Fields**: Raises `ValidationError` with field name
- **Custom Validators**: Raises `ValueError` with custom message
  ```python
  @model_validator(mode="after")
  def resolve_config_path(self) -> "BaseHandlerConfig":
      if not self.repo_path.exists():
          raise ValueError(f"repo_path {self.repo_path} does not exist")
  ```

### 3. Handler Error Handling
**Location**: `src/handlers/`

**AnalyzeHandler**:
- **Agent Errors**: Propagate to main() for logging
- **Tracing Errors**: Logged but don't stop execution
- **Validation Errors**: Raised by `validate_succession()`
  ```python
  if len(missing_files) == len(analysis_files):
      Logger.error("Complete analysis failure: no analysis files were generated")
      raise ValueError("Complete analysis failure: no analysis files were generated")
  ```

**ReadmeHandler**:
- **Agent Errors**: Propagate to main() for logging
- **File Write Errors**: Propagate as exceptions

**JobAnalyzeHandler**:
- **Per-Project Error Isolation**: Try-catch around each project
  ```python
  for group_project in git_group.projects.list(iterator=True, include_subgroups=True):
      try:
          # Process project
      except Exception as err:
          Logger.error(f"Error handling project {group_project.name}", exc_info=True)
          # Continue to next project
  ```
- **Cleanup Guarantee**: Finally block ensures cleanup
  ```python
  try:
      # Clone, analyze, create MR
  finally:
      self._cleanup_project(project=project, repo=repo)
  ```

### 4. Agent Error Handling
**Location**: `src/agents/analyzer.py` and `src/agents/documenter.py`

**Concurrent Execution Error Isolation**:
```python
results = await asyncio.gather(*tasks, return_exceptions=True)

for i, result in enumerate(results):
    if isinstance(result, Exception):
        Logger.error(f"Agent #{i} failed: {result}", exc_info=True)
    else:
        Logger.info(f"Agent #{i} completed successfully")
```

**Partial Success Handling**:
- **All Success**: Logs success message
- **Partial Success**: Logs warning with missing files, continues
- **Complete Failure**: Raises ValueError
  ```python
  if len(missing_files) == len(analysis_files):
      Logger.error("Complete analysis failure: no analysis files were generated")
      raise ValueError("Complete analysis failure: no analysis files were generated")
  
  if missing_files:
      Logger.warning(f"Partial analysis success: {successful_count}/{len(analysis_files)} files generated")
      # Continue without raising error
  ```

**LLM Interaction Errors**:
- **UnexpectedModelBehavior**: Logged and re-raised
  ```python
  except UnexpectedModelBehavior as e:
      Logger.info(f"Unexpected model behavior: {e}")
      raise e
  ```
- **Generic Exceptions**: Logged and re-raised
  ```python
  except Exception as e:
      Logger.info(f"Error running agent: {e}")
      raise e
  ```

**Retry Logic**:
- **Agent-Level Retries**: Configured via `retries=config.ANALYZER_AGENT_RETRIES` (default: 2)
- **Automatic Retry**: pydantic-ai handles retry logic internally
- **Exponential Backoff**: Built into pydantic-ai retry mechanism

### 5. Tool Error Handling
**Location**: `src/agents/tools/`

**FileReadTool Errors**:
```python
if not os.path.exists(file_path):
    raise ModelRetry(message="File not found")

try:
    with open(file_path, "r") as file:
        # Read file
except PermissionError:
    raise ModelRetry(message="Permission denied when trying to read file")
except Exception as e:
    raise ModelRetry(message=f"Failed to read file {file_path}. {str(e)}")
```

**ModelRetry Behavior**:
- **Purpose**: Signals pydantic-ai to retry the tool call
- **Max Retries**: Configured via `max_retries=config.TOOL_FILE_READER_MAX_RETRIES` (default: 2)
- **Retry Strategy**: Automatic by pydantic-ai framework
- **Final Failure**: Propagates to agent as exception

**ListFilesTool Errors**:
- **Directory Not Found**: Returns "No files found" message (graceful)
- **Permission Errors**: Propagate as exceptions
- **Walk Errors**: Handled by os.walk() internally

### 6. HTTP Client Error Handling
**Location**: `src/utils/retry_client.py`

**Retryable Errors**:
- **429 Too Many Requests**: Rate limiting
- **502 Bad Gateway**: Server temporarily unavailable
- **503 Service Unavailable**: Server overloaded
- **504 Gateway Timeout**: Server timeout
- **ConnectionError**: Network issues

**Retry Strategy**:
```python
config=RetryConfig(
    retry=retry_if_exception_type((HTTPStatusError, ConnectionError)),
    wait=wait_retry_after(
        fallback_strategy=wait_exponential(multiplier=1, max=60),
        max_wait=300,
    ),
    stop=stop_after_attempt(5),
    reraise=True,
)
```

**Wait Strategy**:
1. **Retry-After Header**: Respects server-specified wait time
2. **Exponential Backoff**: 1s → 2s → 4s → 8s → 16s (if no header)
3. **Maximum Wait**: 60s per attempt, 300s total
4. **Final Failure**: Re-raises last exception

### 7. Logging Error Handling
**Location**: `src/utils/logger.py`

**Initialization Errors**:
```python
if cls._logger is not None:
    cls._logger.warning("Logger already initialized")
    return
```

**Usage Errors**:
```python
if cls._logger is None:
    raise ValueError("Logger not initialized")
```

**Structured Data Formatting**:
```python
@classmethod
def _format_data(cls, message: str, data: Optional[Union[Dict[str, Any], str]] = None) -> str:
    if data is None:
        return message
    
    if isinstance(data, str):
        return f"{message} | {data}"
    
    try:
        return f"{message} | {json.dumps(data)}"
    except Exception:
        return f"{message} | {str(data)}"
```

### 8. Prompt Manager Error Handling
**Location**: `src/utils/prompt_manager.py`

**File Errors**:
```python
if not file_path.exists():
    raise FileNotFoundError(f"Prompt file not found: {file_path}")
```

**YAML Parsing Errors**:
```python
try:
    with open(file_path, "r", encoding="utf-8") as f:
        self._prompt_data = yaml.safe_load(f)
except yaml.YAMLError as e:
    raise yaml.YAMLError(f"Failed to parse YAML file {file_path}: {e}")
```

**Path Traversal Errors**:
```python
try:
    for key in path.split("."):
        current = current[key]
except (KeyError, TypeError):
    raise ValueError(f"Path '{path}' not found in prompts data")
```

**Template Rendering Errors**:
```python
if not isinstance(prompt_value,