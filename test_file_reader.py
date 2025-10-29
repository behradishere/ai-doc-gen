#!/usr/bin/env python3

"""
Test the file reader tool with different path scenarios
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.tools.file_tool.file_reader import FileReadTool

def test_file_reader():
    repo_path = Path("/Users/behradafshe/repo/Daya_Backend/Daya_Backend")
    
    print(f"🧪 Testing FileReadTool with repo_path: {repo_path}")
    
    # Create file reader with repo path
    file_reader = FileReadTool(repo_path=repo_path)
    
    # Test 1: Try to read a file that should exist
    test_files = [
        "Application/Sale/Commands/CreateSellDocCommand.cs",
        "Domain/Sale/Aggregates/SellDoc.cs",
        "Application/Hr/Commands/CreateEmployeeCommand.cs",
        "Domain/Hr/Aggregates/Employee.cs"
    ]
    
    for test_file in test_files:
        print(f"\n📁 Testing file: {test_file}")
        try:
            result = file_reader._run(test_file, line_count=10)
            print(f"✅ Success! File found and read ({len(result)} chars)")
            print(f"📝 First few lines:\n{result[:200]}...")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test 2: Try absolute path
    abs_test_file = repo_path / "Application"
    if abs_test_file.exists():
        print(f"\n📁 Testing absolute path: {abs_test_file}")
        # Find first .cs file
        for cs_file in abs_test_file.rglob("*.cs"):
            try:
                result = file_reader._run(str(cs_file), line_count=5)
                print(f"✅ Success! Absolute path worked ({len(result)} chars)")
                break
            except Exception as e:
                print(f"❌ Error with absolute path: {e}")

if __name__ == "__main__":
    test_file_reader()