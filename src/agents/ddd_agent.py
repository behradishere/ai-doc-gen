# src/agents/ddd_agent.py
import os
from pathlib import Path
import yaml
from jinja2 import Template
from pydantic_ai import Agent
from opentelemetry import trace
from utils import Logger
import config  # Assuming global config module

class DDDAgent(Agent):
    def __init__(self, repo_path: str):
        # Use .env values
        super().__init__(
            model=os.getenv('ANALYZER_LLM_MODEL', 'gpt-4o-mini'),
            base_url=os.getenv('ANALYZER_LLM_BASE_URL', 'https://api.openai.com/v1'),
            api_key=os.getenv('ANALYZER_LLM_API_KEY'),
            max_tokens=int(os.getenv('ANALYZER_LLM_MAX_TOKENS', 8192)),
            temperature=float(os.getenv('ANALYZER_LLM_TEMPERATURE', 0.0)),
            retries=int(os.getenv('ANALYZER_AGENT_RETRIES', 2)),
            timeout=int(os.getenv('ANALYZER_LLM_TIMEOUT', 180))
        )
        self.repo_path = repo_path
        self._load_prompts()

    def _load_prompts(self):
        # Load from a new YAML like analyzer.yaml - create ddd_analyzer.yaml with system/user prompts
        yaml_path = Path(__file__).parent.parent / 'config' / 'ddd_analyzer.yaml'  # Adjust path
        with open(yaml_path, 'r') as f:
            prompts = yaml.safe_load(f)
        self.system_prompt = prompts['agents']['ddd_analyzer']['system_prompt']
        user_prompt_template = prompts['agents']['ddd_analyzer']['user_prompt']
        self.user_prompt_template = Template(user_prompt_template)

    async def analyze(self, files_content: dict, bounded_context: str = None):
        trace.get_current_span().set_attribute("input", str(files_content))
        user_prompt = self.user_prompt_template.render(repo_path=self.repo_path)
        if bounded_context:
            user_prompt += f"\nFocus on bounded context: {bounded_context}."
        # LLM call (adapted from analyzer.py's style)
        response = await self.run(self.system_prompt, user_prompt)  # Assuming Agent has async run
        Logger.debug("DDD Analysis Response", data=response)
        trace.get_current_span().set_attribute("output", response)
        return response  # Markdown or dict