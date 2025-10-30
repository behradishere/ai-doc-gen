#!/usr/bin/env python3
"""
Test script to debug AI timeout issues with enhanced monitoring
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import (
    ANALYZER_LLM_API_KEY,
    ANALYZER_LLM_BASE_URL,
    ANALYZER_LLM_MODEL,
    ANALYZER_LLM_TIMEOUT
)
from utils.logger import Logger
from utils.retry_client import create_retrying_client
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings


class TimeoutDDDAnalyzer:
    """DDD Analyzer with enhanced timeout and progress monitoring"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.logger = Logger()
        
        # Reduced timeout for testing
        self.timeout = min(ANALYZER_LLM_TIMEOUT, 30)  # Max 30 seconds for testing
        
        # Initialize AI model with timeout (using proper initialization)
        retrying_http_client = create_retrying_client()
        
        self.model = OpenAIModel(
            model_name=ANALYZER_LLM_MODEL,
            provider=OpenAIProvider(
                base_url=ANALYZER_LLM_BASE_URL,
                api_key=ANALYZER_LLM_API_KEY,
                http_client=retrying_http_client,
            ),
        )
        
        self.settings = ModelSettings(
            temperature=0.3,
            max_tokens=1000,  # Smaller for testing
            timeout=self.timeout,
        )
        
        # Simple test prompt
        test_prompt = """You are a .NET DDD (Domain-Driven Design) expert. 
        Analyze the given aggregate and generate a brief application layer documentation.
        Keep it concise and under 500 characters for testing purposes."""
        
        # Create agent for application layer analysis
        self.app_agent = Agent(
            model=self.model,
            system_prompt=test_prompt
        )
    
    async def test_single_aggregate(self, aggregate_path: str) -> Optional[str]:
        """Test documentation generation for a single aggregate with timeout"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Testing aggregate: {aggregate_path}")
            
            # Create a simple test context
            context = f"Analyzing aggregate at: {aggregate_path}"
            
            # Test with asyncio timeout and model settings
            result = await asyncio.wait_for(
                self.app_agent.run(context, model_settings=self.settings),
                timeout=self.timeout
            )
            
            elapsed = time.time() - start_time
            self.logger.info(f"✅ Completed in {elapsed:.2f}s: {len(str(result.data))} chars")
            
            return str(result.data)
            
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            self.logger.error(f"❌ Timeout after {elapsed:.2f}s for {aggregate_path}")
            return None
            
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"❌ Error after {elapsed:.2f}s: {str(e)}")
            return None
    
    def find_test_aggregates(self, limit: int = 3) -> List[str]:
        """Find a few test aggregates"""
        aggregates = []
        
        try:
            for item in self.repo_path.rglob("*"):
                if item.is_dir() and "Domain" in str(item):
                    aggregates.append(str(item.relative_to(self.repo_path)))
                    if len(aggregates) >= limit:
                        break
                        
        except Exception as e:
            self.logger.error(f"Error finding aggregates: {e}")
            # Fallback test paths
            aggregates = ["test/aggregate1", "test/aggregate2", "test/aggregate3"]
        
        return aggregates


async def main():
    """Test AI with timeout monitoring"""
    if len(sys.argv) != 2:
        print("Usage: python test_timeout_ai.py /path/to/repo")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    
    print(f"🔍 Testing AI timeout handling for: {repo_path}")
    print(f"⏱️  Timeout setting: {ANALYZER_LLM_TIMEOUT}s")
    print(f"🤖 Model: {ANALYZER_LLM_MODEL}")
    print(f"🔗 Base URL: {ANALYZER_LLM_BASE_URL}")
    print("-" * 60)
    
    analyzer = TimeoutDDDAnalyzer(repo_path)
    
    # Find test aggregates
    test_aggregates = analyzer.find_test_aggregates(3)
    print(f"📁 Found {len(test_aggregates)} test aggregates:")
    for agg in test_aggregates:
        print(f"   - {agg}")
    print("-" * 60)
    
    # Test each aggregate
    successful = 0
    failed = 0
    
    for i, aggregate in enumerate(test_aggregates, 1):
        print(f"\n🚀 Test {i}/{len(test_aggregates)}: {aggregate}")
        
        result = await analyzer.test_single_aggregate(aggregate)
        
        if result:
            successful += 1
            print(f"✅ Success: {len(result)} characters generated")
            # Show first 200 chars
            preview = result[:200].replace('\n', ' ')
            print(f"📄 Preview: {preview}...")
        else:
            failed += 1
            print("❌ Failed")
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    print(f"\n" + "=" * 60)
    print(f"📊 Results: {successful} successful, {failed} failed")
    
    if failed > 0:
        print("❌ Issues detected - AI calls are timing out or failing")
        print("💡 Suggestions:")
        print("   - Check network connection")
        print("   - Verify OpenAI API key")
        print("   - Try reducing batch sizes")
        print("   - Increase timeout values")
    else:
        print("✅ All tests passed - AI system working correctly")


if __name__ == "__main__":
    asyncio.run(main())