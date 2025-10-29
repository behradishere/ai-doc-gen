#!/usr/bin/env python3

"""
Debug script to test the DDD analyzer without running the full pipeline
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.ddd_analyzer_agent import DDDAnalyzerAgent, DDDAnalyzerAgentConfig
from utils import Logger
import logging
import os

def configure_simple_logging():
    # Initialize the Logger properly
    logs_dir = Path("debug_logs")
    logs_dir.mkdir(exist_ok=True)
    Logger.init(logs_dir, file_level=logging.INFO, console_level=logging.INFO)

async def test_ddd_analysis():
    configure_simple_logging()
    
    dotnet_path = Path("/Users/behradafshe/repo/Daya_Backend/Daya_Backend")
    
    print(f"🔍 Testing DDD Analysis on: {dotnet_path}")
    
    # Check if path exists
    if not dotnet_path.exists():
        print(f"❌ Path does not exist: {dotnet_path}")
        return
    
    # Check if Application folder exists
    app_path = dotnet_path / "Application"
    if not app_path.exists():
        print(f"❌ Application folder not found: {app_path}")
        return
    
    print(f"✅ Found Application folder: {app_path}")
    
    # List some bounded contexts
    print("\n📁 Bounded contexts found:")
    for item in app_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            skip_folders = {'Common', 'Shared', 'Base', 'Core', 'Extensions', 'Interfaces', 'Abstractions', 'Constants'}
            if item.name not in skip_folders:
                print(f"   - {item.name}")
    
    # Create config and analyzer
    config = DDDAnalyzerAgentConfig(repo_path=dotnet_path)
    analyzer = DDDAnalyzerAgent(config)
    
    print("\n🤖 Starting DDD structure analysis...")
    try:
        bounded_contexts = await analyzer.analyze_ddd_structure()
        
        print(f"\n✅ Analysis completed! Found {len(bounded_contexts)} bounded contexts:")
        
        for bc_name, bc_info in bounded_contexts.items():
            print(f"\n📦 {bc_name}:")
            print(f"   Path: {bc_info.path}")
            print(f"   Aggregates ({len(bc_info.aggregates)}):")
            for agg in bc_info.aggregates[:5]:  # Show first 5
                print(f"     - {agg}")
            if len(bc_info.aggregates) > 5:
                print(f"     ... and {len(bc_info.aggregates) - 5} more")
    
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ddd_analysis())