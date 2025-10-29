import asyncio
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re

from opentelemetry import trace
from pydantic import BaseModel, Field
from pydantic_ai import Agent, UnexpectedModelBehavior
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

import config
from utils import Logger, PromptManager, create_retrying_client

from .tools import FileReadTool, ListFilesTool


class DDDAnalyzerAgentConfig(BaseModel):
    repo_path: Path = Field(..., description="The path to the .NET ERP repository")


class BoundedContext(BaseModel):
    name: str
    path: Path
    aggregates: List[str] = []


class DDDAnalyzerAgent:
    """
    DDD-focused analyzer agent that specializes in .NET ERP projects
    following Domain-Driven Design patterns.
    """
    
    def __init__(self, cfg: DDDAnalyzerAgentConfig) -> None:
        self._config = cfg
        self._prompt_manager = PromptManager(
            file_path=Path(__file__).parent / "prompts" / "ddd_analyzer.yaml"
        )
        
    async def analyze_ddd_structure(self) -> Dict[str, BoundedContext]:
        """
        Analyze the .NET project to identify bounded contexts and aggregates
        following DDD patterns.
        """
        Logger.info("Starting DDD structure analysis")
        
        bounded_contexts = self._discover_bounded_contexts()
        
        # Enhance each bounded context with aggregate information
        for bc_name, bc_info in bounded_contexts.items():
            aggregates = await self._discover_aggregates_in_context(bc_info)
            bc_info.aggregates = aggregates
            
        Logger.info(f"Discovered {len(bounded_contexts)} bounded contexts")
        return bounded_contexts
    
    def _discover_bounded_contexts(self) -> Dict[str, BoundedContext]:
        """
        Discover bounded contexts by analyzing the Application layer structure.
        """
        contexts = {}
        application_path = self._config.repo_path / "Application"
        
        if not application_path.exists():
            Logger.warning("Application folder not found")
            return contexts
            
        # Look for bounded context folders in Application directory
        for item in application_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Skip common non-BC folders
                skip_folders = {
                    'Common', 'Shared', 'Base', 'Core', 'Extensions', 
                    'Interfaces', 'Abstractions', 'Constants'
                }
                
                if item.name not in skip_folders:
                    contexts[item.name] = BoundedContext(
                        name=item.name,
                        path=item
                    )
                    Logger.debug(f"Discovered bounded context: {item.name}")
        
        return contexts
    
    async def _discover_aggregates_in_context(self, context: BoundedContext) -> List[str]:
        """
        Discover aggregates within a bounded context by analyzing folder structure
        and namespace patterns.
        """
        aggregates = set()
        
        # Strategy 1: Look for Definitions folders
        definitions_path = context.path / "Definitions"
        if definitions_path.exists():
            for item in definitions_path.iterdir():
                if item.is_dir():
                    aggregates.add(item.name)
        
        # Strategy 2: Analyze Commands and Queries folders
        for folder in context.path.rglob("*"):
            if folder.is_dir():
                folder_name = folder.name
                
                # Skip command/query action folders
                if folder_name in ['Commands', 'Queries', 'Handlers']:
                    continue
                    
                # Skip action-named folders
                action_prefixes = ['Create', 'Update', 'Delete', 'Get', 'Add', 'Remove']
                if any(folder_name.startswith(prefix) for prefix in action_prefixes):
                    continue
                
                # If this folder contains Commands or Queries subfolders,
                # it's likely an aggregate
                if any((folder / subfolder).exists() for subfolder in ['Commands', 'Queries']):
                    aggregates.add(folder_name)
        
        # Strategy 3: Analyze C# files for namespace patterns
        cs_files = list(context.path.rglob("*.cs"))
        namespace_aggregates = await self._extract_aggregates_from_namespaces(cs_files, context.name)
        aggregates.update(namespace_aggregates)
        
        # Clean up aggregate names
        cleaned_aggregates = []
        for agg in aggregates:
            # Remove plural 's' if present
            if agg.endswith('s') and len(agg) > 1:
                agg = agg[:-1]
            
            # Skip obviously non-aggregate names
            skip_names = {
                'command', 'query', 'handler', 'validator', 'dto', 'model',
                'service', 'repository', 'controller', 'common', 'base'
            }
            
            if agg.lower() not in skip_names and len(agg) > 2:
                cleaned_aggregates.append(agg)
        
        Logger.debug(f"Found {len(cleaned_aggregates)} aggregates in {context.name}: {cleaned_aggregates}")
        return sorted(list(set(cleaned_aggregates)))
    
    async def _extract_aggregates_from_namespaces(self, cs_files: List[Path], context_name: str) -> List[str]:
        """
        Extract potential aggregate names from C# file namespaces.
        """
        aggregates = set()
        
        for cs_file in cs_files:
            try:
                content = cs_file.read_text(encoding='utf-8', errors='ignore')[:2048]
                
                # Find namespace declaration
                namespace_match = re.search(r'namespace\s+([A-Za-z0-9_.]+)', content)
                if namespace_match:
                    namespace = namespace_match.group(1)
                    parts = namespace.split('.')
                    
                    # Look for patterns like Application.HR.ContractType
                    if 'Application' in parts:
                        app_index = parts.index('Application')
                        if len(parts) > app_index + 2:  # Need at least Application.BC.Aggregate
                            potential_bc = parts[app_index + 1]
                            if potential_bc == context_name:
                                # Next part might be aggregate or "Definitions"
                                if len(parts) > app_index + 3 and parts[app_index + 2] == 'Definitions':
                                    if len(parts) > app_index + 3:
                                        aggregates.add(parts[app_index + 3])
                                else:
                                    aggregates.add(parts[app_index + 2])
                                    
            except Exception as e:
                Logger.debug(f"Error reading {cs_file}: {e}")
                continue
        
        return list(aggregates)
    
    async def generate_aggregate_documentation(
        self, 
        context_name: str, 
        aggregate_name: str,
        template_files: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Generate documentation for a specific aggregate using AI analysis
        and template files.
        """
        Logger.info(f"Generating documentation for {context_name}/{aggregate_name}")
        
        # Collect relevant files for this aggregate
        context_path = self._config.repo_path / "Application" / context_name
        relevant_files = await self._collect_aggregate_files(context_path, aggregate_name)
        
        # Generate each layer documentation
        docs = {}
        layer_agents = {
            'Application.md': self._application_layer_agent,
            'Domain.md': self._domain_layer_agent,
            'Infrastructure.md': self._infrastructure_layer_agent,
            'Quality.md': self._quality_layer_agent,
            'WebUi.md': self._webui_layer_agent,
            'ChangeLog.md': self._changelog_layer_agent
        }
        
        for layer_file, agent_property in layer_agents.items():
            try:
                agent = agent_property
                template_content = template_files.get(layer_file, "")
                
                user_prompt = self._render_layer_prompt(
                    layer_file, context_name, aggregate_name, 
                    relevant_files, template_content
                )
                
                async with agent:
                    result: AgentRunResult = await agent.run(
                        user_prompt=user_prompt,
                        output_type=str,
                    )
                
                docs[layer_file] = self._cleanup_output(result.output)
                Logger.debug(f"Generated {layer_file} for {context_name}/{aggregate_name}")
                
            except Exception as e:
                Logger.error(f"Error generating {layer_file}: {e}")
                docs[layer_file] = f"# {layer_file.replace('.md', '')} Layer – {aggregate_name}\n\nError generating documentation: {e}"
        
        return docs
    
    async def _collect_aggregate_files(self, context_path: Path, aggregate_name: str) -> List[Path]:
        """
        Collect all files relevant to a specific aggregate.
        """
        relevant_files = []
        
        # Search patterns for aggregate-related files
        search_patterns = [
            f"**/*{aggregate_name}*.cs",
            f"**/Definitions/{aggregate_name}/**/*.cs",
            f"**/{aggregate_name}/**/*.cs",
        ]
        
        for pattern in search_patterns:
            for file_path in context_path.rglob(pattern):
                if file_path.is_file() and file_path not in relevant_files:
                    relevant_files.append(file_path)
        
        # Also look in Domain and Infrastructure folders
        project_root = self._config.repo_path
        for layer in ['Domain', 'Infrastructure']:
            layer_path = project_root / layer
            if layer_path.exists():
                for pattern in search_patterns:
                    for file_path in layer_path.rglob(pattern):
                        if file_path.is_file() and file_path not in relevant_files:
                            relevant_files.append(file_path)
        
        Logger.debug(f"Found {len(relevant_files)} files for {aggregate_name}")
        return relevant_files
    
    def _render_layer_prompt(
        self, 
        layer_file: str, 
        context_name: str, 
        aggregate_name: str,
        relevant_files: List[Path],
        template_content: str
    ) -> str:
        """
        Render the prompt for generating specific layer documentation.
        """
        file_contents = {}
        for file_path in relevant_files[:10]:  # Limit to prevent token overflow
            try:
                content = file_path.read_text(encoding='utf-8')[:2000]  # Limit content size
                rel_path = file_path.relative_to(self._config.repo_path)
                file_contents[str(rel_path)] = content
            except Exception as e:
                Logger.debug(f"Error reading {file_path}: {e}")
        
        template_vars = {
            'repo_path': str(self._config.repo_path),
            'context_name': context_name,
            'aggregate_name': aggregate_name,
            'layer_file': layer_file,
            'relevant_files': file_contents,
            'template_content': template_content
        }
        
        return self._prompt_manager.render_prompt(
            f"agents.ddd_analyzer.layer_prompts.{layer_file.replace('.md', '').lower()}", 
            **template_vars
        )
    
    @property
    def _llm_model(self) -> Tuple[Model, ModelSettings]:
        retrying_http_client = create_retrying_client()

        model = OpenAIModel(
            model_name=config.ANALYZER_LLM_MODEL,
            provider=OpenAIProvider(
                base_url=config.ANALYZER_LLM_BASE_URL,
                api_key=config.ANALYZER_LLM_API_KEY,
                http_client=retrying_http_client,
            ),
        )

        settings = ModelSettings(
            temperature=config.ANALYZER_LLM_TEMPERATURE,
            max_tokens=config.ANALYZER_LLM_MAX_TOKENS,
            timeout=config.ANALYZER_LLM_TIMEOUT,
            parallel_tool_calls=config.ANALYZER_PARALLEL_TOOL_CALLS,
        )

        return model, settings
    
    @property
    def _application_layer_agent(self) -> Agent:
        model, model_settings = self._llm_model
        
        return Agent(
            name="Application Layer Analyzer",
            model=model,
            model_settings=model_settings,
            output_type=str,
            retries=config.ANALYZER_AGENT_RETRIES,
            system_prompt=self._render_prompt("agents.ddd_analyzer.system_prompts.application"),
            tools=[
                FileReadTool().get_tool(),
                ListFilesTool().get_tool(),
            ],
            instrument=True,
        )
    
    @property
    def _domain_layer_agent(self) -> Agent:
        model, model_settings = self._llm_model
        
        return Agent(
            name="Domain Layer Analyzer",
            model=model,
            model_settings=model_settings,
            output_type=str,
            retries=config.ANALYZER_AGENT_RETRIES,
            system_prompt=self._render_prompt("agents.ddd_analyzer.system_prompts.domain"),
            tools=[
                FileReadTool().get_tool(),
                ListFilesTool().get_tool(),
            ],
            instrument=True,
        )
    
    @property
    def _infrastructure_layer_agent(self) -> Agent:
        model, model_settings = self._llm_model
        
        return Agent(
            name="Infrastructure Layer Analyzer",
            model=model,
            model_settings=model_settings,
            output_type=str,
            retries=config.ANALYZER_AGENT_RETRIES,
            system_prompt=self._render_prompt("agents.ddd_analyzer.system_prompts.infrastructure"),
            tools=[
                FileReadTool().get_tool(),
                ListFilesTool().get_tool(),
            ],
            instrument=True,
        )
    
    @property
    def _quality_layer_agent(self) -> Agent:
        model, model_settings = self._llm_model
        
        return Agent(
            name="Quality Layer Analyzer",
            model=model,
            model_settings=model_settings,
            output_type=str,
            retries=config.ANALYZER_AGENT_RETRIES,
            system_prompt=self._render_prompt("agents.ddd_analyzer.system_prompts.quality"),
            tools=[
                FileReadTool().get_tool(),
                ListFilesTool().get_tool(),
            ],
            instrument=True,
        )
    
    @property
    def _webui_layer_agent(self) -> Agent:
        model, model_settings = self._llm_model
        
        return Agent(
            name="WebUI Layer Analyzer",
            model=model,
            model_settings=model_settings,
            output_type=str,
            retries=config.ANALYZER_AGENT_RETRIES,
            system_prompt=self._render_prompt("agents.ddd_analyzer.system_prompts.webui"),
            tools=[
                FileReadTool().get_tool(),
                ListFilesTool().get_tool(),
            ],
            instrument=True,
        )
    
    @property
    def _changelog_layer_agent(self) -> Agent:
        model, model_settings = self._llm_model
        
        return Agent(
            name="ChangeLog Layer Analyzer",
            model=model,
            model_settings=model_settings,
            output_type=str,
            retries=config.ANALYZER_AGENT_RETRIES,
            system_prompt=self._render_prompt("agents.ddd_analyzer.system_prompts.changelog"),
            tools=[
                FileReadTool().get_tool(),
                ListFilesTool().get_tool(),
            ],
            instrument=True,
        )
    
    def _render_prompt(self, prompt_name: str, **kwargs) -> str:
        template_vars = {
            'repo_path': str(self._config.repo_path),
            **kwargs
        }
        
        return self._prompt_manager.render_prompt(prompt_name, **template_vars)
    
    def _cleanup_output(self, output: str) -> str:
        # Cleanup absolute paths
        output = output.replace(str(self._config.repo_path), ".")
        
        return output