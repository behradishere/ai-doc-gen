#!/usr/bin/env python3

"""
Test the AI system with improved file handling on a single bounded context
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.ddd_analyzer_agent import DDDAnalyzerAgent, DDDAnalyzerAgentConfig
from utils import Logger

async def test_improved_ai_system():
    # Initialize logger
    Logger.init(
        log_dir=Path("./debug_logs"),
        file_level="INFO", 
        console_level="INFO"
    )
    
    repo_path = Path("/Users/behradafshe/repo/Daya_Backend/Daya_Backend")
    
    print(f"🧪 Testing improved AI system with realistic file handling")
    print(f"📂 Repo path: {repo_path}")
    
    # Initialize DDD analyzer
    ddd_config = DDDAnalyzerAgentConfig(repo_path=repo_path)
    ddd_analyzer = DDDAnalyzerAgent(ddd_config)
    
    try:
        # Test with first bounded context only
        print("\n📁 Step 1: Discovering bounded contexts...")
        bounded_contexts = ddd_analyzer._discover_bounded_contexts()
        
        if bounded_contexts:
            first_context_name = "ssrs"  # Use ssrs as it worked before
            if first_context_name in bounded_contexts:
                first_context = bounded_contexts[first_context_name]
                
                print(f"\n🎯 Step 2: Testing context: {first_context_name}")
                print(f"📁 Context path: {first_context.path}")
                
                # Test aggregate discovery
                print(f"\n📦 Step 3: Discovering aggregates...")
                aggregates = await ddd_analyzer._discover_aggregates_in_context(first_context)
                
                if aggregates:
                    print(f"✅ Found {len(aggregates)} aggregates: {aggregates}")
                    
                    # Test with first aggregate that has a simple name
                    test_aggregate = "PrintFormat"  # Known to exist and simpler
                    if test_aggregate in aggregates:
                        print(f"\n📝 Step 4: Testing documentation generation for: {test_aggregate}")
                        
                        # Load template files
                        template_files = {
                            "Application.md": "# Application Layer Template",
                            "Domain.md": "# Domain Layer Template", 
                            "Infrastructure.md": "# Infrastructure Layer Template"
                        }
                        
                        try:
                            docs = await ddd_analyzer.generate_aggregate_documentation(
                                first_context_name, test_aggregate, template_files
                            )
                            
                            if docs:
                                print(f"\n✅ SUCCESS! Generated {len(docs)} documentation files:")
                                for doc_type, content in docs.items():
                                    print(f"  📄 {doc_type}: {len(content)} characters")
                                    if "File not found" not in content:
                                        print(f"      ✅ Contains actual analysis")
                                    else:
                                        print(f"      ⚠️ Contains file not found messages")
                                        
                                # Show preview of one doc
                                if "Application.md" in docs:
                                    preview = docs["Application.md"][:300].replace('\n', ' ')
                                    print(f"\n📄 Application.md preview: {preview}...")
                                    
                            else:
                                print(f"❌ No documentation generated")
                                
                        except Exception as e:
                            print(f"❌ Error generating documentation: {e}")
                    else:
                        print(f"⚠️ Test aggregate {test_aggregate} not found in {aggregates}")
                else:
                    print(f"⚠️ No aggregates found in {first_context_name}")
            else:
                print(f"❌ Context {first_context_name} not found in bounded contexts")
        else:
            print("❌ No bounded contexts found!")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_improved_ai_system())