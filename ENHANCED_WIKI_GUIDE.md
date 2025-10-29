# Enhanced Wiki Exporter - Usage Guide

## Overview
The Enhanced Wiki Exporter is a new AI-powered tool that generates comprehensive documentation for .NET ERP projects following Domain-Driven Design (DDD) patterns. It creates properly structured documentation for each bounded context and aggregate.

## Features
- 🧠 **AI-Powered Analysis**: Uses specialized AI agents to analyze your .NET code
- 📁 **DDD Structure**: Automatically detects bounded contexts and aggregates
- 📝 **Template-Based**: Uses your existing template files for consistent formatting
- 🎯 **Azure DevOps Ready**: Generates `.order` files for proper wiki navigation
- 🔄 **Fallback Support**: Creates basic documentation even when AI analysis fails

## Quick Start

### 1. Prerequisites
- Python 3.13+ with `uv` package manager
- OpenAI-compatible API key configured in `.env`
- .NET ERP project with Application/Domain/Infrastructure structure

### 2. Configuration
The tool is already configured in `.ai/config.yaml`:

```yaml
enhanced_wiki_exporter:
  output_path: "Docs"          # Where to create documentation
  template_path: "temp"        # Location of template files
```

### 3. Usage
Simply run the command pointing to your .NET project:

```bash
cd /Users/behradafshe/repo/ai-doc-gen/ai-doc-gen

# Generate documentation for your .NET ERP project
uv run src/main.py export-enhanced-wiki --repo-path /Users/behradafshe/repo/Daya_Backend/Daya_Backend
```

### 4. Output Structure
The tool creates documentation following this structure:

```
Docs/
└── BoundedContext/
    ├── .order                    # Azure DevOps ordering file
    ├── Acc/                      # Accounting bounded context
    │   ├── .order
    │   ├── AccountHeading/       # Aggregate folder
    │   │   ├── .order
    │   │   ├── Application.md    # Commands, queries, validators
    │   │   ├── Domain.md         # Entities, business rules
    │   │   ├── Infrastructure.md # Repositories, configurations
    │   │   ├── Quality.md        # Tests, performance
    │   │   ├── WebUi.md         # Controllers, APIs
    │   │   └── ChangeLog.md     # Version history
    │   └── VoucherGroup/        # Another aggregate
    │       └── ... (same 7 files)
    ├── Buy/                     # Purchasing bounded context
    │   ├── PurchaseOrder/
    │   ├── PriceFactor/
    │   └── ...
    └── Hr/                      # Human Resources bounded context
        ├── ContractType/
        ├── Degree/
        └── ...
```

## How It Works

### 1. Bounded Context Discovery
The tool analyzes your `Application/` folder to identify bounded contexts:
- Looks for top-level folders like `Acc`, `Buy`, `Hr`, etc.
- Excludes common non-BC folders (`Common`, `Shared`, `Base`)
- Creates a bounded context for each valid folder

### 2. Aggregate Detection
For each bounded context, it finds aggregates using multiple strategies:
- **Definitions Pattern**: Looks in `Application/{BC}/Definitions/` folders
- **Command/Query Pattern**: Finds folders containing Commands/Queries subfolders
- **Namespace Analysis**: Analyzes C# file namespaces for aggregate patterns

### 3. AI-Powered Documentation
Each aggregate gets 6 specialized AI agents:
- **Application Layer Agent**: Analyzes commands, queries, and validators
- **Domain Layer Agent**: Documents entities, business rules, and relationships
- **Infrastructure Layer Agent**: Covers repositories and database configurations
- **Quality Layer Agent**: Documents tests and performance considerations
- **WebUI Layer Agent**: Analyzes controllers and API endpoints
- **ChangeLog Agent**: Creates version history documentation

### 4. Template Integration
Uses your template files from the `temp/` folder as guides for:
- Content structure and formatting
- Code examples and patterns
- Consistent documentation style

## Command Options

```bash
uv run src/main.py export-enhanced-wiki [OPTIONS]

Required:
  --repo-path PATH          Path to your .NET ERP project root

Optional:
  --output-path PATH        Output directory (default: "Docs")
  --template-path PATH      Template files directory (default: "temp")
  --config PATH            Custom config file path
```

## Examples

### Basic Usage
```bash
# Generate docs for your ERP project
uv run src/main.py export-enhanced-wiki --repo-path /path/to/your/dotnet/project
```

### Custom Output Location
```bash
# Generate docs to a different folder
uv run src/main.py export-enhanced-wiki \
    --repo-path /path/to/your/dotnet/project \
    --output-path "Documentation"
```

### Using Custom Templates
```bash
# Use templates from a different folder
uv run src/main.py export-enhanced-wiki \
    --repo-path /path/to/your/dotnet/project \
    --template-path "my-templates"
```

## Troubleshooting

### Common Issues

1. **No bounded contexts found**
   - Ensure your project has an `Application/` folder
   - Check that bounded context folders exist (like `Application/Acc/`, `Application/Buy/`)

2. **No aggregates found**
   - Verify your project follows DDD patterns with Commands/Queries folders
   - Check that aggregate folders contain C# files with proper namespaces

3. **AI generation fails**
   - Verify your OpenAI API key is configured in `.env`
   - Check network connectivity
   - The tool will create fallback documentation automatically

4. **Template files not found**
   - Ensure the `temp/` folder contains template files
   - Check file names match: `Application.md`, `Domain.md`, etc.

### Logging
Check the logs in `.logs/` folder for detailed information about the analysis process.

## Integration with Azure DevOps

The generated documentation is ready for Azure DevOps wikis:
- `.order` files control page ordering
- Markdown files follow Azure DevOps wiki conventions
- Folder structure matches the expected hierarchy

Simply copy the generated `Docs/` folder to your Azure DevOps wiki repository.

## Next Steps

1. **Run the tool** on your ERP project
2. **Review generated docs** and verify accuracy
3. **Adjust templates** in `temp/` folder if needed
4. **Iterate** and refine based on your team's needs
5. **Integrate** with your CI/CD pipeline for automated documentation updates