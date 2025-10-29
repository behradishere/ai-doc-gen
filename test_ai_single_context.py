#!/usr/bin/env python3

"""
Test the AI-enhanced system with a single bounded context to debug issues
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.ddd_analyzer_agent import DDDAnalyzerAgent, DDDAnalyzerAgentConfig
from utils import Logger

async def test_single_context():
    # Initialize logger
    Logger.init(
        log_dir=Path("./debug_logs"),
        file_level="INFO", 
        console_level="INFO"
    )
    
    repo_path = Path("/Users/behradafshe/repo/Daya_Backend/Daya_Backend")
    
    print(f"🧪 Testing AI-enhanced analysis with single context")
    print(f"📂 Repo path: {repo_path}")
    
    # Initialize DDD analyzer
    ddd_config = DDDAnalyzerAgentConfig(repo_path=repo_path)
    ddd_analyzer = DDDAnalyzerAgent(ddd_config)
    
    try:
        # Test bounded context discovery
        print("\n📁 Step 1: Discovering bounded contexts...")
        bounded_contexts = ddd_analyzer._discover_bounded_contexts()
        
        if bounded_contexts:
            print(f"✅ Found {len(bounded_contexts)} bounded contexts")
            
            # Test with first bounded context only
            first_context_name = list(bounded_contexts.keys())[0]
            first_context = bounded_contexts[first_context_name]
            
            print(f"\n🎯 Step 2: Testing single context: {first_context_name}")
            print(f"📁 Context path: {first_context.path}")
            
            # Test aggregate discovery
            print("\n📦 Step 3: Discovering aggregates...")
            aggregates = await ddd_analyzer._discover_aggregates_in_context(first_context)
            
            if aggregates:
                print(f"✅ Found {len(aggregates)} aggregates in {first_context_name}")
                print(f"📦 Aggregates: {aggregates[:5]}{'...' if len(aggregates) > 5 else ''}")
                
                # Test documentation generation for first aggregate
                if aggregates:
                    first_aggregate = aggregates[0]
                    print(f"\n📝 Step 4: Testing documentation generation for: {first_aggregate}")
                    
                    try:
                        # Test documentation generation with basic template
                        template_files = {"Application.md": "Basic template"}
                        
                        docs = await ddd_analyzer.generate_aggregate_documentation(
                            first_context_name, first_aggregate, template_files
                        )
                        
                        if docs and 'Application.md' in docs:
                            app_doc = docs['Application.md']
                            if len(app_doc.strip()) > 100:
                                print(f"✅ Documentation generated ({len(app_doc)} chars)")
                                print(f"📄 Preview: {app_doc[:200]}...")
                            else:
                                print(f"⚠️ Documentation seems incomplete: {len(app_doc)} chars")
                        else:
                            print(f"⚠️ No documentation generated: {docs}")
                            
                    except Exception as e:
                        print(f"❌ Error generating documentation: {e}")
                        import traceback
                        traceback.print_exc()
                        
            else:
                print(f"⚠️ No aggregates found in {first_context_name}")
                
        else:
            print("❌ No bounded contexts found!")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_single_context())