#!/usr/bin/env python3

"""
Simple debug script to test bounded context detection without AI calls
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_bounded_context_detection():
    dotnet_path = Path("/Users/behradafshe/repo/Daya_Backend/Daya_Backend")
    
    print(f"🔍 Testing Bounded Context Detection on: {dotnet_path}")
    
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
    
    # Discover bounded contexts manually (same logic as the agent)
    contexts = {}
    skip_folders = {
        'Common', 'Shared', 'Base', 'Core', 'Extensions', 
        'Interfaces', 'Abstractions', 'Constants'
    }
    
    print("\n📁 Bounded contexts found:")
    for item in app_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            if item.name not in skip_folders:
                contexts[item.name] = item
                print(f"   - {item.name}")
    
    print(f"\n✅ Total bounded contexts: {len(contexts)}")
    
    # Test aggregate detection for a few bounded contexts
    print("\n🔍 Testing aggregate detection in first 3 bounded contexts:")
    
    for i, (bc_name, bc_path) in enumerate(list(contexts.items())[:3]):
        print(f"\n📦 {bc_name} ({bc_path}):")
        
        aggregates = set()
        
        # Strategy 1: Look for Definitions folders
        definitions_path = bc_path / "Definitions"
        if definitions_path.exists():
            print(f"   Found Definitions folder")
            for item in definitions_path.iterdir():
                if item.is_dir():
                    aggregates.add(item.name)
                    print(f"     - {item.name} (from Definitions)")
        
        # Strategy 2: Look for folders containing Commands or Queries
        for folder in bc_path.rglob("*"):
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
                    print(f"     - {folder_name} (contains Commands/Queries)")
        
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
        
        print(f"   Final aggregates ({len(cleaned_aggregates)}): {sorted(cleaned_aggregates)}")

if __name__ == "__main__":
    test_bounded_context_detection()