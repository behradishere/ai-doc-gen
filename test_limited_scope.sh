#!/bin/bash

# Quick test script for enhanced wiki exporter with limited scope
# This processes only the first few bounded contexts to avoid long API calls

echo "🚀 Testing Enhanced Wiki Exporter (Limited Scope)"
echo "================================================="

DOTNET_PROJECT_PATH="/Users/behradafshe/repo/Daya_Backend/Daya_Backend"

echo "📂 .NET Project Path: $DOTNET_PROJECT_PATH"

# Check if the .NET project exists
if [ ! -d "$DOTNET_PROJECT_PATH" ]; then
    echo "❌ Error: .NET project not found at $DOTNET_PROJECT_PATH"
    exit 1
fi

# Check if Application folder exists
if [ ! -d "$DOTNET_PROJECT_PATH/Application" ]; then
    echo "❌ Error: Application folder not found at $DOTNET_PROJECT_PATH/Application"
    exit 1
fi

echo "✅ .NET project structure found"

# Create a temporary limited version of the .NET project for testing
TEMP_TEST_DIR="/tmp/daya_backend_test"
rm -rf "$TEMP_TEST_DIR"
mkdir -p "$TEMP_TEST_DIR/Application"

echo "📋 Creating limited test environment..."

# Copy only the first 3 bounded contexts for testing
BOUNDED_CONTEXTS=("Acc" "Hr" "Buy")

for BC in "${BOUNDED_CONTEXTS[@]}"; do
    if [ -d "$DOTNET_PROJECT_PATH/Application/$BC" ]; then
        echo "   Copying $BC..."
        cp -r "$DOTNET_PROJECT_PATH/Application/$BC" "$TEMP_TEST_DIR/Application/"
    else
        echo "   ⚠️  $BC not found, skipping..."
    fi
done

# Also copy Domain and Infrastructure if they exist
if [ -d "$DOTNET_PROJECT_PATH/Domain" ]; then
    echo "   Copying Domain layer..."
    cp -r "$DOTNET_PROJECT_PATH/Domain" "$TEMP_TEST_DIR/"
fi

if [ -d "$DOTNET_PROJECT_PATH/Infrastructure" ]; then
    echo "   Copying Infrastructure layer..."
    cp -r "$DOTNET_PROJECT_PATH/Infrastructure" "$TEMP_TEST_DIR/"
fi

echo "✅ Limited test environment created at: $TEMP_TEST_DIR"
echo ""
echo "📊 Test scope:"
echo "   - Bounded contexts: ${BOUNDED_CONTEXTS[*]}"
echo "   - This should process ~5-15 aggregates instead of 100+"
echo ""

# Run the enhanced wiki exporter on the limited test data
echo "🔄 Running enhanced wiki exporter (limited scope)..."
cd /Users/behradafshe/repo/ai-doc-gen/ai-doc-gen

uv run src/main.py export-enhanced-wiki \
    --repo-path "$TEMP_TEST_DIR" \
    --output-path "TestDocs" \
    --template-path "temp"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Enhanced wiki export completed successfully!"
    echo "📁 Generated documentation in: $TEMP_TEST_DIR/TestDocs/"
    echo ""
    echo "📋 Check the results:"
    if [ -d "$TEMP_TEST_DIR/TestDocs/BoundedContext" ]; then
        echo "   Generated bounded contexts:"
        ls "$TEMP_TEST_DIR/TestDocs/BoundedContext/"
        echo ""
        echo "   Sample aggregate (if any):"
        find "$TEMP_TEST_DIR/TestDocs/BoundedContext" -name "*.md" | head -5
    fi
    echo ""
    echo "🔗 You can now copy successful patterns to process the full project"
else
    echo "❌ Enhanced wiki export failed"
    echo "Check the error messages above"
fi

echo ""
echo "🗑️  Cleaning up test environment..."
rm -rf "$TEMP_TEST_DIR"
echo "✅ Cleanup completed"