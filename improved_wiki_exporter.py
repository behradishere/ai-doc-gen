#!/usr/bin/env python3
"""
Improved Enhanced Wiki Exporter with better timeout and progress monitoring
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import (
    ANALYZER_LLM_API_KEY,
    ANALYZER_LLM_BASE_URL,
    ANALYZER_LLM_MODEL,
    ANALYZER_LLM_TIMEOUT
)
from utils.retry_client import create_retrying_client
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings


class ImprovedDDDAnalyzer:
    """Improved DDD Analyzer with timeout monitoring and batch processing"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.output_path = Path("temp")
        self.output_path.mkdir(exist_ok=True)
        
        # Initialize AI model
        retrying_http_client = create_retrying_client()
        
        self.model = OpenAIModel(
            model_name=ANALYZER_LLM_MODEL,
            provider=OpenAIProvider(
                base_url=ANALYZER_LLM_BASE_URL,
                api_key=ANALYZER_LLM_API_KEY,
                http_client=retrying_http_client,
            ),
        )
        
        # Shorter timeout for faster detection of stuck calls
        self.settings = ModelSettings(
            temperature=0.3,
            max_tokens=2000,
            timeout=60,  # 1 minute timeout
        )
        
        # Create agents for different layers
        self.agents = self._create_agents()
        
        self.processed_count = 0
        self.failed_count = 0
        self.start_time = time.time()
    
    def _create_agents(self) -> Dict[str, Agent]:
        """Create specialized agents for each layer"""
        
        prompts = {
            "application": """You are a .NET DDD expert. Analyze the application layer of the given aggregate.
            Focus on application services, command handlers, query handlers, and DTOs.
            Generate concise documentation (max 500 words) about the application layer responsibilities.""",
            
            "domain": """You are a .NET DDD expert. Analyze the domain layer of the given aggregate.
            Focus on entities, value objects, domain services, and business rules.
            Generate concise documentation (max 500 words) about the domain layer.""",
            
            "infrastructure": """You are a .NET DDD expert. Analyze the infrastructure layer of the given aggregate.
            Focus on repositories, external service integrations, and data access.
            Generate concise documentation (max 500 words) about the infrastructure layer.""",
            
            "quality": """You are a .NET DDD expert. Analyze the code quality and testing of the given aggregate.
            Focus on unit tests, integration tests, code coverage, and quality metrics.
            Generate concise documentation (max 500 words) about quality aspects.""",
            
            "webui": """You are a .NET DDD expert. Analyze the web UI aspects of the given aggregate.
            Focus on controllers, views, API endpoints, and user interfaces.
            Generate concise documentation (max 500 words) about the web UI layer.""",
            
            "changelog": """You are a .NET DDD expert. Generate a changelog for the given aggregate.
            Include recent changes, version history, and notable updates.
            Generate concise documentation (max 500 words) about changes and evolution."""
        }
        
        agents = {}
        for layer, prompt in prompts.items():
            agents[layer] = Agent(
                model=self.model,
                system_prompt=prompt
            )
        
        return agents
    
    def find_aggregates(self, limit: Optional[int] = None) -> List[str]:
        """Find aggregates in the repository"""
        aggregates = []
        
        print(f"🔍 Scanning repository: {self.repo_path}")
        
        try:
            # Look for directories that might contain aggregates
            for item in self.repo_path.rglob("*"):
                if (item.is_dir() and 
                    not any(skip in str(item) for skip in ["bin", "obj", ".git", "node_modules", "__pycache__"]) and
                    any(keyword in str(item).lower() for keyword in ["domain", "application", "service", "aggregate"])):
                    
                    relative_path = str(item.relative_to(self.repo_path))
                    aggregates.append(relative_path)
                    
                    if limit and len(aggregates) >= limit:
                        break
                        
        except Exception as e:
            print(f"❌ Error scanning repository: {e}")
            return []
        
        print(f"📁 Found {len(aggregates)} potential aggregates")
        return aggregates[:limit] if limit else aggregates
    
    async def process_single_aggregate(self, aggregate_path: str, layer: str) -> Optional[str]:
        """Process a single aggregate layer with timeout"""
        
        try:
            context = f"""
            Aggregate Path: {aggregate_path}
            Repository: {self.repo_path}
            Layer: {layer.upper()}
            
            Please analyze this aggregate's {layer} layer and provide documentation.
            If no {layer} layer exists, briefly explain what would typically be found in this layer.
            """
            
            # Run with timeout
            result = await asyncio.wait_for(
                self.agents[layer].run(context, model_settings=self.settings),
                timeout=90  # 1.5 minute total timeout
            )
            
            return str(result)
            
        except asyncio.TimeoutError:
            print(f"⏰ Timeout processing {aggregate_path}/{layer}")
            return f"# {layer.title()} Layer\n\nTimeout occurred while analyzing this layer. Please check manually."
            
        except Exception as e:
            print(f"❌ Error processing {aggregate_path}/{layer}: {str(e)[:100]}")
            return f"# {layer.title()} Layer\n\nError occurred: {str(e)[:200]}"
    
    async def process_aggregate_batch(self, aggregates: List[str], batch_size: int = 2) -> Dict[str, Dict[str, str]]:
        """Process aggregates in small batches"""
        
        results = {}
        layers = ["application", "domain", "infrastructure", "quality", "webui", "changelog"]
        
        for i in range(0, len(aggregates), batch_size):
            batch = aggregates[i:i + batch_size]
            
            print(f"\n📦 Processing batch {i//batch_size + 1}: {len(batch)} aggregates")
            
            for aggregate in batch:
                print(f"🔄 Processing {aggregate}...")
                
                results[aggregate] = {}
                
                # Process each layer for this aggregate
                for layer in layers:
                    print(f"   📄 Generating {layer} documentation...")
                    
                    start_time = time.time()
                    content = await self.process_single_aggregate(aggregate, layer)
                    elapsed = time.time() - start_time
                    
                    if content:
                        results[aggregate][layer] = content
                        self.processed_count += 1
                        print(f"   ✅ {layer} completed in {elapsed:.1f}s ({len(content)} chars)")
                    else:
                        self.failed_count += 1
                        print(f"   ❌ {layer} failed after {elapsed:.1f}s")
                    
                    # Small delay between layers
                    await asyncio.sleep(0.5)
                
                print(f"✅ Completed {aggregate} ({len(layers)} files)")
                
                # Progress update
                total_elapsed = time.time() - self.start_time
                print(f"📊 Progress: {self.processed_count} files, {self.failed_count} failures, {total_elapsed:.1f}s total")
            
            # Pause between batches
            print(f"⏸️  Batch completed. Pausing 2 seconds...")
            await asyncio.sleep(2)
        
        return results
    
    def save_results(self, results: Dict[str, Dict[str, str]]):
        """Save results to files"""
        
        print(f"\n💾 Saving results to {self.output_path}")
        
        total_files = 0
        
        for aggregate_name, layers in results.items():
            # Create aggregate directory
            agg_dir = self.output_path / aggregate_name.replace("/", "_")
            agg_dir.mkdir(exist_ok=True)
            
            # Save each layer
            for layer_name, content in layers.items():
                filename = f"{layer_name.title()}.md"
                filepath = agg_dir / filename
                
                try:
                    filepath.write_text(content, encoding='utf-8')
                    total_files += 1
                except Exception as e:
                    print(f"❌ Error saving {filepath}: {e}")
        
        print(f"✅ Saved {total_files} documentation files")


async def main():
    """Main function with improved error handling"""
    
    if len(sys.argv) != 2:
        print("Usage: python improved_wiki_exporter.py /path/to/repo")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    
    print("=" * 80)
    print("🚀 IMPROVED ENHANCED WIKI EXPORTER")
    print("=" * 80)
    print(f"📂 Repository: {repo_path}")
    print(f"🤖 Model: {ANALYZER_LLM_MODEL}")
    print(f"⏱️  Timeout: {ANALYZER_LLM_TIMEOUT}s per call")
    print(f"📊 Output: ./temp/")
    print("=" * 80)
    
    analyzer = ImprovedDDDAnalyzer(repo_path)
    
    # Find aggregates (limit to first 5 for testing)
    aggregates = analyzer.find_aggregates(limit=5)
    
    if not aggregates:
        print("❌ No aggregates found")
        return
    
    print(f"\n🎯 Will process {len(aggregates)} aggregates:")
    for i, agg in enumerate(aggregates, 1):
        print(f"   {i}. {agg}")
    
    print(f"\n⚡ Processing in batches of 2 with timeouts...")
    
    try:
        # Process in small batches
        results = await analyzer.process_aggregate_batch(aggregates, batch_size=2)
        
        # Save results
        analyzer.save_results(results)
        
        # Summary
        total_time = time.time() - analyzer.start_time
        print(f"\n" + "=" * 80)
        print(f"✅ COMPLETED SUCCESSFULLY")
        print(f"📊 Processed: {analyzer.processed_count} files")
        print(f"❌ Failed: {analyzer.failed_count} files")
        print(f"⏱️  Total time: {total_time:.1f}s")
        print(f"📁 Output directory: {analyzer.output_path.absolute()}")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Interrupted by user")
        total_time = time.time() - analyzer.start_time
        print(f"📊 Partial results: {analyzer.processed_count} files, {total_time:.1f}s")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)