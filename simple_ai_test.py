#!/usr/bin/env python3
"""
Simple AI timeout test script
"""

import asyncio
import sys
import time
from pathlib import Path

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


async def test_ai_call():
    """Test a simple AI call with timeout"""
    
    print(f"🤖 Testing AI call with model: {ANALYZER_LLM_MODEL}")
    print(f"⏱️  Timeout: {ANALYZER_LLM_TIMEOUT}s")
    print(f"🔗 URL: {ANALYZER_LLM_BASE_URL}")
    
    # Create model
    retrying_http_client = create_retrying_client()
    
    model = OpenAIModel(
        model_name=ANALYZER_LLM_MODEL,
        provider=OpenAIProvider(
            base_url=ANALYZER_LLM_BASE_URL,
            api_key=ANALYZER_LLM_API_KEY,
            http_client=retrying_http_client,
        ),
    )
    
    # Test with short timeout
    settings = ModelSettings(
        temperature=0.3,
        max_tokens=200,
        timeout=30,  # 30 second timeout
    )
    
    # Create agent
    agent = Agent(
        model=model,
        system_prompt="You are a helpful assistant. Respond briefly in under 100 words."
    )
    
    # Test call
    start_time = time.time()
    
    try:
        print("🚀 Making AI call...")
        
        result = await asyncio.wait_for(
            agent.run("Hello, can you confirm you're working?", model_settings=settings),
            timeout=30
        )
        
        elapsed = time.time() - start_time
        print(f"✅ Success in {elapsed:.2f}s")
        print(f"📄 Response: {str(result)}")
        
        return True
        
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        print(f"❌ Timeout after {elapsed:.2f}s")
        return False
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Error after {elapsed:.2f}s: {e}")
        return False


async def main():
    """Main test function"""
    
    print("=" * 60)
    print("🧪 AI TIMEOUT TEST")
    print("=" * 60)
    
    success = await test_ai_call()
    
    print("=" * 60)
    if success:
        print("✅ AI system is working - no timeout issues detected")
        print("💡 The hanging issue is likely in the complex document generation")
    else:
        print("❌ AI system has timeout or connection issues")
        print("💡 Check network, API key, or OpenAI service status")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())