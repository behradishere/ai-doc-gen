#!/bin/bash

# Test script for the enhanced wiki exporter
# This script demonstrates how to use the new enhanced wiki exporter with your .NET ERP project

echo "🚀 Testing Enhanced Wiki Exporter"
echo "================================="

# Set the path to your .NET project
DOTNET_PROJECT_PATH="/Users/behradafshe/repo/Daya_Backend/Daya_Backend"

echo "📂 .NET Project Path: $DOTNET_PROJECT_PATH"

# Check if the .NET project exists
if [ ! -d "$DOTNET_PROJECT_PATH" ]; then
    echo "❌ Error: .NET project not found at $DOTNET_PROJECT_PATH"
    echo "Please update the DOTNET_PROJECT_PATH variable in this script"
    exit 1
fi

# Check if Application folder exists in the .NET project
if [ ! -d "$DOTNET_PROJECT_PATH/Application" ]; then
    echo "❌ Error: Application folder not found at $DOTNET_PROJECT_PATH/Application"
    echo "Please ensure this is the correct path to your .NET ERP project"
    exit 1
fi

echo "✅ .NET project structure found"

# Run the enhanced wiki exporter
echo "🔄 Running enhanced wiki exporter..."
cd /Users/behradafshe/repo/ai-doc-gen/ai-doc-gen

uv run src/main.py export-enhanced-wiki \
    --repo-path "$DOTNET_PROJECT_PATH" \
    --output-path "Docs" \
    --template-path "temp"

if [ $? -eq 0 ]; then
    echo "✅ Enhanced wiki export completed successfully!"
    echo "📁 Generated documentation should be in: $DOTNET_PROJECT_PATH/Docs/"
    echo ""
    echo "📋 Expected structure:"
    echo "   Docs/"
    echo "   └── BoundedContext/"
    echo "       ├── Acc/"
    echo "       │   ├── AccountHeading/"
    echo "       │   │   ├── Application.md"
    echo "       │   │   ├── Domain.md"
    echo "       │   │   ├── Infrastructure.md"
    echo "       │   │   ├── Quality.md"
    echo "       │   │   ├── WebUi.md"
    echo "       │   │   └── ChangeLog.md"
    echo "       │   └── ..."
    echo "       ├── Buy/"
    echo "       ├── Chq/"
    echo "       └── ..."
else
    echo "❌ Enhanced wiki export failed"
    echo "Please check the error messages above"
fi