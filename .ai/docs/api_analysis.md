Perfect! Now I have comprehensive information. Let me create the complete API documentation:

# API Documentation

## APIs Served by This Project

### Overview
The AI Documentation Generator is a **command-line application** that does not expose traditional HTTP REST APIs. Instead, it provides functionality through CLI commands and programmatic Python interfaces. The application operates as a local tool or automated service for analyzing codebases and generating documentation.

### Command-Line Interface (CLI)

#### 1. Analyze Command
**Command**: `ai-doc-gen analyze`

**Description**: Performs comprehensive code analysis on a repository using multiple specialized AI agents that run concurrently to analyze different aspects of the codebase.

**Request Parameters**:
- `--repo-path` (required, string): Path to the repository to analyze
- `--config` (optional, string): Path to custom configuration file (defaults to `.ai/config.yaml` in repo)
- `--exclude-code-structure` (optional, boolean): Skip code structure analysis
- `--exclude-data-flow` (optional, boolean): Skip data flow analysis
- `--exclude-dependencies` (optional, boolean): Skip dependency analysis
- `--exclude-request-flow` (optional, boolean): Skip request flow analysis
- `--exclude-api-analysis` (optional, boolean): Skip API analysis

**Response**: Creates up to 5 markdown analysis files in `{repo_path}/.ai/docs/`:
- `structure_analysis.md` - Architectural overview, components, design patterns
- `dependency_analysis.md` - Internal and external dependency mapping
- `data_flow_analysis.md` - Data transformation and persistence patterns
- `request_flow_analysis.md` - Request processing and flow analysis
- `api_analysis.md` - API endpoint and integration documentation

**Success Criteria**:
- Complete success: All requested analysis files generated
- Partial success: Some analysis files generated (logged as warning, continues execution)
- Complete failure: No analysis files generated (raises ValueError)

**Authentication**: None required for local usage

**Examples**:
```bash
# Basic analysis with all agents
ai-doc-gen analyze --repo-path /path/to/project

# Selective analysis (exclude specific agents)
ai-doc-gen analyze --repo-path /path/to/project \
  --exclude-data-flow \
  --exclude-api-analysis

# Use custom configuration file
ai-doc-gen analyze --repo-path /path/to/project \
  --config /path/to/custom-config.yaml

# Analyze current directory
ai-doc-gen analyze --repo-path .
```

**Error Handling**:
- Invalid repository path: Validation error with clear message
- Missing configuration: Falls back to defaults
- Agent failures: Continues with partial results, logs errors
- File write errors: Logged with full context

---

#### 2. Document Command
**Command**: `ai-doc-gen document`

**Description**: Generates comprehensive README documentation from analysis results using AI to synthesize information from all analysis files into a cohesive, well-structured README.md.

**Request Parameters**:
- `--repo-path` (required, string): Path to the repository
- `--config` (optional, string): Path to configuration file
- `--exclude-project-overview` (optional, boolean): Skip project overview section
- `--exclude-table-of-contents` (optional, boolean): Skip table of contents
- `--exclude-architecture` (optional, boolean): Skip architecture section
- `--exclude-c4-model` (optional, boolean): Skip C4 model diagrams
- `--exclude-repository-structure` (optional, boolean): Skip directory structure
- `--exclude-dependencies-and-integration` (optional, boolean): Skip dependencies section
- `--exclude-api-documentation` (optional, boolean): Skip API documentation
- `--exclude-development-notes` (optional, boolean): Skip development notes
- `--exclude-known-issues-and-limitations` (optional, boolean): Skip known issues
- `--exclude-additional-documentation` (optional, boolean): Skip additional docs links
- `--use-existing-readme` (optional, boolean): Incorporate existing README content

**Response**: Creates/updates `README.md` in repository root with structured markdown documentation

**Authentication**: None required

**Examples**:
```bash
# Generate full README with all sections
ai-doc-gen document --repo-path /path/to/project

# Generate minimal README
ai-doc-gen document --repo-path /path/to/project \
  --exclude-c4-model \
  --exclude-development-notes \
  --exclude-known-issues-and-limitations

# Preserve and incorporate existing README
ai-doc-gen document --repo-path /path/to/project \
  --use-existing-readme

# Generate README with custom sections
ai-doc-gen document --repo-path . \
  --exclude-table-of-contents \
  --exclude-additional-documentation
```

**Error Handling**:
- Missing analysis files: Uses available files, logs warnings
- Invalid repository path: Validation error
- Write permission errors: Logged with context
- LLM failures: Retries up to 2 times with exponential backoff

---

#### 3. Cronjob Analyze Command
**Command**: `ai-doc-gen cronjob analyze`

**Description**: Automated analysis for GitLab projects with merge request creation. Discovers projects in a GitLab group, filters applicable projects, clones them, runs analysis, and creates merge requests with results.

**Request Parameters**:
- `--max-days-since-last-commit` (optional, integer): Filter projects by activity (default: 30)
- `--working-path` (optional, path): Temporary directory for cloning (default: `/tmp/cronjob/projects`)
- `--group-project-id` (optional, integer): GitLab group ID to analyze (default: 3)

**Response**: Creates merge requests with analysis results in target repositories

**Authentication**: Requires GitLab OAuth token (`GITLAB_OAUTH_TOKEN` environment variable)

**Workflow**:
1. Fetch projects from GitLab group (including subgroups)
2. Filter applicable projects based on:
   - Not archived
   - Not in ignored subgroups
   - Not in ignored projects list
   - Last commit not from AI analyzer
   - Activity within specified days
   - No existing branch for today
   - No open MR from analyzer
3. For each applicable project:
   - Clone repository
   - Create dated branch (`ai-analysis-YYYY-MM-DD`)
   - Run analysis with project-specific config
   - Commit results with standardized message
   - Push to GitLab
   - Create merge request
   - Cleanup temporary files

**Examples**:
```bash
# Analyze recent projects (last 14 days)
ai-doc-gen cronjob analyze --max-days-since-last-commit 14

# Analyze specific group with custom working directory
ai-doc-gen cronjob analyze \
  --group-project-id 5 \
  --working-path /tmp/analysis

# Use default settings (30 days, group 3)
ai-doc-gen cronjob analyze
```

**Error Handling**:
- Individual project failures: Logged but don't stop batch processing
- GitLab API errors: Logged with project context
- Repository cleanup: Guaranteed via try-finally blocks
- Network failures: Retries with exponential backoff

---

### Programmatic Python Interface

#### Agent Classes

**AnalyzerAgent**
```python
from agents.analyzer import AnalyzerAgent, AnalyzerAgentConfig
from pathlib import Path

# Configure analyzer
config = AnalyzerAgentConfig(
    repo_path=Path("/path/to/repo"),
    exclude_code_structure=False,
    exclude_data_flow=False,
    exclude_dependencies=False,
    exclude_request_flow=False,
    exclude_api_analysis=False
)

# Create and run agent
agent = AnalyzerAgent(config)
await agent.run()
```

**DocumenterAgent**
```python
from agents.documenter import DocumenterAgent, DocumenterAgentConfig, ReadmeConfig
from pathlib import Path

# Configure documenter
config = DocumenterAgentConfig(
    repo_path=Path("/path/to/repo"),
    readme=ReadmeConfig(
        exclude_project_overview=False,
        exclude_architecture=False,
        use_existing_readme=True
    )
)

# Create and run agent
agent = DocumenterAgent(config)
await agent.run()
```

**Handler Classes**
```python
from handlers.analyze import AnalyzeHandler, AnalyzeHandlerConfig
from handlers.readme import ReadmeHandler, ReadmeHandlerConfig
from pathlib import Path

# Analyze handler
analyze_config = AnalyzeHandlerConfig(repo_path=Path("."))
analyze_handler = AnalyzeHandler(analyze_config)
await analyze_handler.handle()

# README handler
readme_config = ReadmeHandlerConfig(repo_path=Path("."))
readme_handler = ReadmeHandler(readme_config)
await readme_handler.handle()
```

---

### Authentication & Security

#### Local CLI Usage
- **Authentication**: None required
- **Permissions**: Read/write access to target repositories
- **Security**: Operates with user's file system permissions

#### GitLab Integration
- **Method**: OAuth token authentication
- **Configuration**: `GITLAB_OAUTH_TOKEN` environment variable
- **Required Scopes**:
  - `api` - Full API access
  - `read_repository` - Read repository contents
  - `write_repository` - Create branches, commits, merge requests
- **User Configuration**:
  - `GITLAB_USER_NAME` - Display name for commits/MRs
  - `GITLAB_USER_USERNAME` - GitLab username
  - `GITLAB_USER_EMAIL` - Email for Git commits
- **Base URL**: Configurable via `GITLAB_API_URL` (default: https://git.divar.cloud)

#### LLM Services Authentication
- **Analyzer LLM**:
  - API Key: `ANALYZER_LLM_API_KEY`
  - Base URL: `ANALYZER_LLM_BASE_URL`
  - Model: `ANALYZER_LLM_MODEL`
- **Documenter LLM**:
  - API Key: `DOCUMENTER_LLM_API_KEY`
  - Base URL: `DOCUMENTER_LLM_BASE_URL`
  - Model: `DOCUMENTER_LLM_MODEL`
- **Authentication Method**: Bearer token in HTTP headers
- **Security**: API keys stored in environment variables, never hardcoded

#### Observability Authentication
- **Langfuse** (optional):
  - Public Key: `LANGFUSE_PUBLIC_KEY`
  - Secret Key: `LANGFUSE_SECRET_KEY`
  - Host: `LANGFUSE_HOST`
  - Method: Basic authentication with base64-encoded credentials
  - Header: `Authorization: Basic {base64(public_key:secret_key)}`

---

### Rate Limiting & Constraints

#### LLM API Limits
- **Request Timeout**: 180 seconds (configurable via `ANALYZER_LLM_TIMEOUT`, `DOCUMENTER_LLM_TIMEOUT`)
- **Max Tokens**: 8192 per response (configurable via `ANALYZER_LLM_MAX_TOKENS`, `DOCUMENTER_LLM_MAX_TOKENS`)
- **Temperature**: 0.0 (deterministic, configurable)
- **Rate Limiting**: Subject to LLM provider limits
- **Retry Strategy**: 2 retries per agent (configurable via `ANALYZER_AGENT_RETRIES`, `DOCUMENTER_AGENT_RETRIES`)

#### HTTP Client Constraints
- **Max Retry Attempts**: 5 (configurable via `HTTP_RETRY_MAX_ATTEMPTS`)
- **Backoff Strategy**: Exponential with multiplier of 1 (1s → 2s → 4s → 8s → 16s)
- **Max Wait Per Attempt**: 60 seconds (configurable via `HTTP_RETRY_MAX_WAIT_PER_ATTEMPT`)
- **Max Total Wait**: 300 seconds (configurable via `HTTP_RETRY_MAX_TOTAL_WAIT`)
- **Retry Conditions**: HTTP 429, 502, 503, 504, ConnectionError
- **Retry-After Header**: Respected when provided by server

#### Tool Execution Limits
- **File Reader Retries**: 2 (configurable via `TOOL_FILE_READER_MAX_RETRIES`)
- **List Files Retries**: 2 (configurable via `TOOL_LIST_FILES_MAX_RETRIES`)
- **File Read Chunk Size**: 200 lines (default, configurable per call)
- **Parallel Tool Calls**: Enabled by default (configurable via `ANALYZER_PARALLEL_TOOL_CALLS`, `DOCUMENTER_PARALLEL_TOOL_CALLS`)

#### GitLab API Constraints
- **Rate Limiting**: Standard GitLab API rate limits apply
- **Concurrent Operations**: Sequential project processing (one at a time)
- **Branch Naming**: `ai-analysis-{YYYY-MM-DD}` format
- **Commit Message**: `[AI] Analyzer-Agent: Create/Update AI Analysis [skip ci]`
- **MR Validation**: Checks for existing open MRs before creation

#### File System Constraints
- **Ignored Directories**: 100+ patterns (node_modules, .git, __pycache__, etc.)
- **Ignored Extensions**: 100+ patterns (.pyc, .log, .zip, etc.)
- **Working Directory**: Configurable, defaults to `/tmp/cronjob/projects` for cronjobs
- **Cleanup**: Automatic cleanup after cronjob execution

#### Concurrent Processing
- **Analyzer Agents**: Up to 5 concurrent agents (structure, dependencies, data flow, request flow, API)
- **Error Isolation**: Individual agent failures don't affect others
- **Partial Success**: Continues with available results if some agents fail

---

## External API Dependencies

### LLM Services (Primary Dependencies)

#### 1. Analyzer LLM Service
**Service Name**: Code Analysis LLM Provider (OpenAI-compatible)

**Purpose**: Powers 5 specialized AI agents for comprehensive code analysis:
- Structure Analyzer - Architectural patterns and components
- Dependency Analyzer - Internal and external dependencies
- Data Flow Analyzer - Data transformation and persistence
- Request Flow Analyzer - Request handling and routing
- API Analyzer - API endpoints and integrations

**Base URL**: Configurable via `ANALYZER_LLM_BASE_URL`

**Configuration**:
```yaml
Model: ANALYZER_LLM_MODEL (e.g., claude-sonnet-4-20250514)
API Key: ANALYZER_LLM_API_KEY
Temperature: 0.0 (deterministic)
Max Tokens: 8192
Timeout: 180 seconds
Parallel Tool Calls: true
```

**Endpoints Used**:
- `POST /v1/chat/completions` - OpenAI-compatible chat completions API

**Request Format**:
```json
{
  "model": "claude-sonnet-4-20250514",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "temperature": 0.0,
  "max_tokens": 8192,
  "tools": [...]
}
```

**Response Format**:
```json
{
  "id": "...",
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "..."
    }
  }],
  "usage": {
    "prompt_tokens": 1234,
    "completion_tokens": 5678,
    "total_tokens": 6912
  }
}
```

**Authentication Method**: Bearer token authentication
```
Authorization: Bearer {ANALYZER_LLM_API_KEY}
```

**Error Handling**:
- **Retry Strategy**: 2 automatic retries per agent
- **Backoff**: Exponential with jitter (1s → 2s → 4s)
- **Timeout Handling**: 180-second timeout per request
- **Graceful Degradation**: Continues if some agents fail
- **Error Logging**: Comprehensive logging with agent context

**Retry/Circuit Breaker Configuration**:
```yaml
Agent Level:
  - Max Retries: 2 (ANALYZER_AGENT_RETRIES)
  - Retry on: UnexpectedModelBehavior, Exception

HTTP Level:
  - Max Attempts: 5 (HTTP_RETRY_MAX_ATTEMPTS)
  - Backoff: Exponential (multiplier=1)
  - Max Wait Per Attempt: 60s
  - Total Timeout: 300s
  - Retry Status Codes: 429, 502, 503, 504
  - Respects Retry-After headers
```

**Usage Tracking**:
- Total tokens logged per agent run
- Request/response token breakdown
- Execution time tracking (minutes and seconds)
- Message count tracking

---

#### 2. Documenter LLM Service
**Service Name**: Documentation Generation LLM Provider

**Purpose**: Generates comprehensive README documentation from analysis results, synthesizing information into cohesive, well-structured markdown with proper formatting, diagrams, and navigation.

**Base URL**: Configurable via `DOCUMENTER_LLM_BASE_URL`

**Configuration**:
```yaml
Model: DOCUMENTER_LLM_MODEL
API Key: DOCUMENTER_LLM_API_KEY
Temperature: 0.0 (deterministic)
Max Tokens: 8192
Timeout: 180 seconds
Parallel Tool Calls: true
```

**Endpoints Used**:
- **OpenAI-compatible**: `POST /v1/chat/completions`
- **Gemini API**: `POST /v1beta/models/{model}:generateContent`

**Multi-Provider Support**:
```python
# OpenAI-compatible providers
if "gemini" not in model_name:
    model = OpenAIModel(
        model_name=model_name,
        provider=OpenAIProvider(
            base_url=base_url,
            api_key=api_key,
            http_client=retrying_http_client
        )
    )
# Gemini provider
else:
    model = GeminiModel(
        model_name=model_name,
        provider=CustomGeminiGLA(
            api_key=api_key,
            base_url=base_url,
            http_client=retrying_http_client
        )
    )
```

**Authentication Method**: API key authentication
- OpenAI: Bearer token in Authorization header
- Gemini: API key in request URL or header

**Error Handling**:
- 2 retries with timeout handling
- Structured output validation via Pydantic
- Comprehensive error logging

**Integration Pattern**:
- Supports both OpenAI and Gemini providers
- Custom provider implementation for Gemini with base URL override
- Automatic provider selection based on model name
- Shared retry client with exponential backoff

---

### GitLab API Integration

#### GitLab REST API
**Service Name**: GitLab Repository Management

**Purpose**: Repository operations, branch management, merge request automation for cronjob-based analysis

**Base URL**: `GITLAB_API_URL` (default: https://git.divar.cloud)

**Endpoints Used**:

1. **List Group Projects**
   - `GET /api/v4/groups/{id}/projects`
   - Query Parameters: `include_subgroups=true`, `iterator=true`
   - Purpose: Discover all projects in a group and subgroups

2. **Get Project Details**
   - `GET /api/v4/projects/{id}`
   - Purpose: Fetch project metadata and configuration

3. **List Branches**
   - `GET /api/v4/projects/{id}/repository/branches`
   - Query Parameters: `search={branch_name}`
   - Purpose: Check if analysis branch already exists

4. **Get Branch Details**
   - `GET /api/v4/projects/{id}/repository/branches/{branch}`
   - Purpose: Get default branch information and last commit

5. **Create Branch**
   - `POST /api/v4/projects/{id}/repository/branches`
   - Body: `{"branch": "ai-analysis-2024-01-15", "ref": "main"}`
   - Purpose: Create new branch for analysis results

6. **List Merge Requests**
   - `GET /api/v4/projects/{id}/merge_requests`
   - Query Parameters: `state=opened`, `author_username={username}`, `search={title}`
   - Purpose: Check for existing open MRs to avoid duplicates

7. **Create Merge Request**
   - `POST /api/v4/projects/{id}/merge_requests`
   - Body:
     ```json
     {
       "source_branch": "ai-analysis-2024-01-15",
       "target_branch": "main",
       "title": "[AI] Analyzer-Agent: Create/Update AI Analysis for project - 2024-01-15 [skip ci]",
       "description": "This merge request contains Updated AI analysis results.\n\nAnalyzer Version: `1.2.0`\n\n**Note:** This merge request is automatically created by the AI Analyzer Agent."
     }
     ```

**Authentication Method**: OAuth token
```
Authorization: Bearer {GITLAB_OAUTH_TOKEN}
```

**Error Handling**:
- Built-in python-gitlab library error handling
- Comprehensive logging with project context
- Individual project failures don't stop batch processing
- Cleanup guaranteed via try-finally blocks

**Retry/Circuit Breaker Configuration**:
- Uses python-gitlab client defaults
- No custom retry logic at GitLab API level
- HTTP retry logic applies to underlying requests

**Integration Pattern**:
```python
# Initialize client
gitlab_client = Gitlab(
    url=config.GITLAB_API_URL,
    oauth_token=config.GITLAB_OAUTH_TOKEN
)

# Fetch projects
git_group = gitlab_client.groups.get(id=group_project_id)
for group_project in git_group.projects.list(iterator=True, include_subgroups=True):
    project = gitlab_client.projects.get(id=group_project.get_id())
    
    # Check applicability
    if _is_applicable_project(project):
        # Process project
        await _handle_project(project)
```

**Project Filtering Logic**:
```python
def _is_applicable_project(project: Project) -> bool:
    # Skip archived projects
    if project.archived:
        return False
    
    # Skip ignored subgroups
    for subgroup in IGNORED_SUBGROUPS:
        if subgroup in project.namespace.get("full_path", "").lower().split("/"):
            return False
    
    # Skip ignored projects
    if int(project.get_id()) in IGNORED_PROJECTS:
        return False
    
    # Skip if last commit was from analyzer
    default_branch = project.branches.get(project.default_branch)
    if COMMIT_MESSAGE_TITLE in default_branch.commit.get("message", ""):
        return False
    
    # Skip if too old
    if commited_at := default_branch.commit.get("committed_date"):
        last_commit_date = datetime.fromisoformat(commited_at).replace(tzinfo=None)
        days_since_last_commit = (datetime.now() - last_commit_date).days
        if days_since_last_commit > max_days_since_last_commit:
            return False
    
    # Skip if today's branch exists
    branch_name = _get_branch_name(project)
    if project.branches.list(search=branch_name):
        return False
    
    # Skip if similar MR exists
    if project.mergerequests.list(
        state="opened",
        author_username=config.GITLAB_USER_USERNAME,
        search=COMMIT_MESSAGE_TITLE
    ):
        return False
    
    return True
```

**Git Operations** (via GitPython):
```python
# Clone repository
repo = Repo.clone_from(
    url=project.http_url_to_repo,
    to_path=working_path / f"{project.name}-{project.id}",
    branch=project.default_branch
)

# Configure Git user
repo.git.config("user.name", config.GITLAB_USER_NAME)
repo.git.config("user.email", config.GITLAB_USER_EMAIL)

# Create and checkout branch
branch_name = f"ai-analysis-{datetime.now().strftime('%Y-%m-%d')}"
repo.git.checkout("-b", branch_name)

# Commit and push
repo.git.add(".")
commit_message = f"{COMMIT_MESSAGE_TITLE} [skip ci]\n\nAnalyzer Version: {config.VERSION}"
repo.git.commit("-m", commit_message)
repo.git.push("origin", repo.active_branch.name, "-f")
```

---

### Observability Services

#### 1. Langfuse Integration
**Service Name**: LLM Observability Platform

**Purpose**: Monitoring LLM usage, costs, performance metrics, trace analysis, and debugging AI agent behavior

**Base URL**: Configurable via `LANGFUSE_HOST`

**Configuration**:
```yaml
Public Key: LANGFUSE_PUBLIC_KEY
Secret Key: LANGFUSE_SECRET_KEY
Environment: ENVIRONMENT (development/staging/production)
Enabled: ENABLE_LANGFUSE (default: false)
```

**Endpoints Used**: OpenTelemetry-compatible OTLP endpoints
- Automatic instrumentation via logfire
- No direct API calls required

**Authentication Method**: Basic authentication with base64-encoded credentials
```python
langfuse_auth = base64.b64encode(
    f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}".encode()
).decode()

os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {langfuse_auth}"
```

**Error Handling**:
- Optional service - failures don't affect core functionality
- Graceful degradation if unavailable
- Logging of observability setup errors

**Integration Pattern**:
```python
def configure_langfuse():
    # Encode credentials
    langfuse_auth = base64.b64encode(
        f"{config.LANGFUSE_PUBLIC_KEY}:{config.LANGFUSE_SECRET_KEY}".encode()
    ).decode()
    
    # Set OTLP headers
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {langfuse_auth}"
    
    # Configure logfire
    logfire.configure(
        service_name="ai-doc-gen",
        send_to_logfire=False,
        environment=config.ENVIRONMENT
    )
    
    # Instrument libraries
    logfire.instrument_pydantic_ai()
    logfire.instrument_httpx(capture_all=True)
```

**Instrumentation Coverage**:
- **pydantic-ai**: Automatic tracing of agent runs, tool calls, LLM requests
- **httpx**: HTTP request/response tracing with full capture
- **Custom Spans**: Manual span creation for handlers and major operations

**Trace Attributes**:
```python
span.set_attributes({
    "repo_path": str(repo_path),
    "repo_version": get_repo_version(repo_path),
    "exclude_code_structure": exclude_code_structure,
    "exclude_data_flow": exclude_data_flow,
    "input": str(repo_path),
    "agent_name": agent.name,
    "total_tokens": result.usage().total_tokens,
    "request_tokens": result.usage().request_tokens,
    "response_tokens": result.usage().response_tokens
})
```

---

#### 2. OpenTelemetry Tracing
**Service Name**: Distributed Tracing

**Purpose**: Performance monitoring, debugging, and distributed tracing across agent executions

**Configuration**:
```yaml
SDK Disabled: OTEL_SDK_DISABLED (default: false)
OTLP Endpoint: OTEL_EXPORTER_OTLP_ENDPOINT
OTLP Headers: OTEL_EXPORTER_OTLP_HEADERS
```

**Integration Pattern**:
```python
from opentelemetry import trace

# Get tracer
tracer = trace.get_tracer("analyzer")

# Create spans
with tracer.start_as_current_span("Analyzer Agent") as span:
    span.set_attributes({...})
    span.add_event(name="Running Structure Analyzer", attributes={...})
    result = await agent.run()
    span.set_attribute("result", result.output)
```

**Span Hierarchy**:
```
Analyzer Agent (root span)
├── Structure Analyzer Agent
│   ├── Tool: List-Files
│   ├── Tool: Read-File
│   └── LLM Request
├── Dependency Analyzer Agent
│   ├── Tool: List-Files
│   ├── Tool: Read-File
│   └── LLM Request
├── Data Flow Analyzer Agent
├── Request Flow Analyzer Agent
└── API Analyzer Agent
```

---

### Integration Patterns

#### 1. Retry Pattern with Exponential Backoff
**Implementation**: Custom HTTP client with tenacity-based retry logic

```python
def create_retrying_client() -> AsyncClient:
    transport = AsyncTenacityTransport(
        config=RetryConfig(
            # Retry on HTTP errors and connection issues
            retry=retry_if_exception_type((HTTPStatusError, ConnectionError)),
            
            # Wait strategy: Retry-After header or exponential backoff
            wait=wait_retry_after(
                fallback_strategy=wait_exponential(multiplier=1, max=60),
                max_wait=300
            ),
            
            # Stop after 5 attempts
            stop=stop_after_attempt(5),
            
            # Reraise last exception
            reraise=True
        ),
        validate_response=should_retry_status
    )
    return AsyncClient(transport=transport)
```

**Usage**: Shared across all LLM providers for resilient HTTP communication

---

#### 2. Concurrent Agent Execution Pattern
**Implementation**: Asyncio-based concurrent execution with error isolation

```python
async def run(self):
    tasks = []
    
    # Create tasks for each enabled agent
    if not self._config.exclude_code_structure:
        tasks.append(self._run_agent(
            agent=self._structure_analyzer_agent,
            user_prompt=self._render_prompt("agents.structure_analyzer.user_prompt"),
            file_path=self._config.repo_path / ".ai" / "docs" / "structure_analysis.md"
        ))
    
    # ... more agents ...
    
    # Run all agents concurrently with error isolation
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Log results
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            Logger.error(f"Agent #{i} failed: {result}", exc_info=True)
        else:
            Logger.info(f"Agent #{i} completed successfully")
```

**Benefits**:
- Parallel execution for faster analysis
- Individual agent failures don't stop others
- Partial success handling

---

#### 3. Configuration Hierarchy Pattern
**Implementation**: Multi-source configuration with precedence

```python
def load_config(args, handler_config: Type[T], file_key: str = "") -> T:
    # 1. Load from YAML file
    file_config = load_config_from_file(args, file_key)
    
    # 2. Load from CLI arguments
    cli_config = load_config_as_dict(args, handler_config)
    
    # 3. Merge with precedence: defaults → file → CLI
    config = merge_dicts(file_config, cli_config)
    
    # 4. Validate and instantiate
    return handler_config(**config)
```

**Precedence Order**:
1. Pydantic model defaults (lowest priority)
2. YAML configuration file
3. CLI arguments (highest priority)

---

#### 4. Tool-Based Agent Pattern
**Implementation**: Pydantic-AI tool registration with retry logic

```python
class FileReadTool:
    def get_tool(self):
        return Tool(
            self._run,
            name="Read-File",
            takes_ctx=False,
            max_retries=config.TOOL_FILE_READER_MAX_RETRIES
        )
    
    def _run(self, file_path: str, line_number: int = 0, line_count: int = 200) -> str:
        # Implementation with ModelRetry for errors
        if not os.path.exists(file_path):
            raise ModelRetry(message="File not found")
        # ... read file ...
```

**Agent Registration**:
```python
agent = Agent(
    name="Structure Analyzer",
    model=model,
    tools=[
        FileReadTool().get_tool(),
        ListFilesTool().get_tool()
    ]
)
```

---

#### 5. Graceful Degradation Pattern
**Implementation**: Partial success handling with validation

```python
def validate_succession(self, analysis_files: List[Path]):
    missing