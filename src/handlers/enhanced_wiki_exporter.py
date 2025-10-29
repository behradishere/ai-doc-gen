from datetime import datetime
from pathlib import Path
from typing import Dict

from pydantic import Field

from utils import Logger
from .base_handler import BaseHandler, BaseHandlerConfig
from agents.ddd_analyzer_agent import DDDAnalyzerAgent, DDDAnalyzerAgentConfig


class EnhancedWikiExporterConfig(BaseHandlerConfig):
    output_path: Path = Field(default=Path("Docs"), description="Output path for generated Wiki (Docs/) folder")
    template_path: Path = Field(default=Path("temp"), description="Path to template files")


class EnhancedWikiExporterHandler(BaseHandler):
    """
    Enhanced wiki exporter that uses DDD analysis to generate proper 
    bounded context and aggregate documentation structure.
    """
    
    def __init__(self, config: EnhancedWikiExporterConfig):
        super().__init__(config)
        self.config: EnhancedWikiExporterConfig = config

    async def handle(self) -> None:
        Logger.info("Starting enhanced wiki exporter handler")

        repo_path: Path = self.config.repo_path
        out_root: Path = (self.config.repo_path / self.config.output_path).resolve()

        Logger.info(f"Exporting wiki to {out_root}")
        Logger.info(f"Analyzing .NET project at {repo_path}")

        # Initialize DDD analyzer
        ddd_config = DDDAnalyzerAgentConfig(
            repo_path=repo_path
        )
        ddd_analyzer = DDDAnalyzerAgent(ddd_config)

        # Load template files
        template_files = self._load_template_files()

        # Create BoundedContext folder
        bc_folder = "BoundedContext"
        bc_root = out_root / bc_folder
        bc_root.mkdir(parents=True, exist_ok=True)
        
        # Create .order file for BoundedContext
        order_file = bc_root / ".order"
        if not order_file.exists():
            order_file.write_text("")

        # Analyze DDD structure
        Logger.info("Analyzing DDD structure...")
        bounded_contexts = await ddd_analyzer.analyze_ddd_structure()

        if not bounded_contexts:
            Logger.warning("No bounded contexts found!")
            return

        # Create bounded context order file
        bc_names = sorted(bounded_contexts.keys())
        (bc_root / ".order").write_text("\n".join(bc_names))

        # Generate documentation for each bounded context and aggregate
        for bc_name, bc_info in bounded_contexts.items():
            Logger.info(f"Processing bounded context: {bc_name}")
            
            bc_dir = bc_root / bc_name
            bc_dir.mkdir(parents=True, exist_ok=True)
            
            # Create .order file for bounded context aggregates
            if bc_info.aggregates:
                (bc_dir / ".order").write_text("\n".join(sorted(bc_info.aggregates)))
            
            # Clean up any existing .md files at BC level
            for existing in list(bc_dir.iterdir()):
                if existing.is_file() and existing.suffix.lower() == '.md':
                    try:
                        existing.unlink()
                        Logger.debug(f"Removed existing file: {existing}")
                    except Exception as e:
                        Logger.warning(f"Could not remove {existing}: {e}")

            # Process each aggregate
            for aggregate_name in bc_info.aggregates:
                Logger.info(f"Processing aggregate: {bc_name}/{aggregate_name}")
                
                agg_dir = bc_dir / aggregate_name
                agg_dir.mkdir(parents=True, exist_ok=True)
                
                # Create .order file for aggregate layers
                layer_files = ["Application", "ChangeLog", "Domain", "Infrastructure", "Quality", "WebUi"]
                (agg_dir / ".order").write_text("\n".join(layer_files))
                
                # Generate documentation for each layer
                try:
                    docs = await ddd_analyzer.generate_aggregate_documentation(
                        bc_name, 
                        aggregate_name,
                        template_files
                    )
                    
                    # Write generated documentation files
                    for layer_file, content in docs.items():
                        target_path = agg_dir / layer_file
                        target_path.write_text(content, encoding='utf-8')
                        Logger.debug(f"Generated {target_path}")
                    
                    Logger.info(f"Successfully generated documentation for {bc_name}/{aggregate_name}")
                    
                except Exception as e:
                    Logger.error(f"Error generating documentation for {bc_name}/{aggregate_name}: {e}", exc_info=True)
                    
                    # Create minimal fallback documentation
                    self._create_fallback_documentation(agg_dir, bc_name, aggregate_name, template_files)

        Logger.info(f"Enhanced wiki export completed to {out_root}")
        Logger.info(f"Generated documentation for {len(bounded_contexts)} bounded contexts")

    def _load_template_files(self) -> Dict[str, str]:
        """
        Load template files from the temp directory.
        """
        template_files = {}
        # Use template path relative to the current working directory (where the tool is run from)
        # This allows templates to be in the ai-doc-gen repo, not the target .NET repo
        current_dir = Path.cwd()
        template_path = current_dir / self.config.template_path
        
        if not template_path.exists():
            Logger.warning(f"Template path not found: {template_path}")
            return template_files
        
        template_file_names = [
            "Application.md", "ChangeLog.md", "Domain.md", 
            "Infrastructure.md", "Quality.md", "WebUi.md"
        ]
        
        for file_name in template_file_names:
            file_path = template_path / file_name
            if file_path.exists():
                try:
                    template_files[file_name] = file_path.read_text(encoding='utf-8')
                    Logger.debug(f"Loaded template: {file_name}")
                except Exception as e:
                    Logger.warning(f"Error loading template {file_name}: {e}")
                    template_files[file_name] = ""
            else:
                Logger.warning(f"Template file not found: {file_path}")
                template_files[file_name] = ""
        
        Logger.info(f"Loaded {len(template_files)} template files")
        return template_files

    def _create_fallback_documentation(
        self, 
        agg_dir: Path, 
        bc_name: str, 
        aggregate_name: str,
        template_files: Dict[str, str]
    ):
        """
        Create basic fallback documentation when AI generation fails.
        """
        Logger.info(f"Creating fallback documentation for {bc_name}/{aggregate_name}")
        
        fallback_docs = {
            "Application.md": f"""# Application Layer – {aggregate_name}

## Commands

### Create{aggregate_name}Command
- **Purpose**: Creates a new {aggregate_name.lower()}.
- **Validation**: Validates input parameters.
- **Handler**: Handles the creation logic.

### Update{aggregate_name}Command
- **Purpose**: Updates an existing {aggregate_name.lower()}.
- **Validation**: Validates input parameters and existence.
- **Handler**: Handles the update logic.

### Delete{aggregate_name}Command
- **Purpose**: Deletes an existing {aggregate_name.lower()}.
- **Validation**: Validates existence and constraints.
- **Handler**: Handles the deletion logic.

## Queries

### Get{aggregate_name}Query
- **Purpose**: Retrieves {aggregate_name.lower()} information.
- **Handler**: Handles the query logic.
- **Return Type**: {aggregate_name}Dto
""",
            
            "Domain.md": f"""# Domain Model – {aggregate_name}

The **{aggregate_name}** entity represents {aggregate_name.lower()} in the {bc_name} bounded context.

### Table And Schema
```csharp
[Table("{aggregate_name}s", Schema = "{bc_name}")]
```

### Entity Definition:
```csharp
public class {aggregate_name}
{{
    public int {aggregate_name}Id {{ get; set; }}
    // Additional properties would be defined here
}}
```

### RELATIONS
```csharp
// Related entities would be listed here
```
""",
            
            "Infrastructure.md": f"""# Infrastructure: {aggregate_name} Configuration

**Namespace:** `Infrastructure.Persistence.Configurations.{bc_name}`  
**File:** `{aggregate_name}Configuration.cs`  
**Database Table:** `[{bc_name}].[{aggregate_name}s]`  
**Entity:** `Domain.Entity.{bc_name}.{aggregate_name}`  

---

| Property | Configuration | Notes |
|-----------|----------------|-------|
| `{aggregate_name}Id` | `HasKey()` | Defines the primary key. |

## Repository Implementation
- **Interface**: I{aggregate_name}Repository
- **Implementation**: {aggregate_name}Repository
""",
            
            "Quality.md": f"""# Quality & Testing – {aggregate_name}

### Unit Tests
- **Create{aggregate_name}Command**: Validates input and creation logic.
- **Update{aggregate_name}Command**: Validates update logic and constraints.
- **Delete{aggregate_name}Command**: Validates deletion logic and references.

### Performance Tests
- Verify list queries perform optimally when paging large datasets.

### Observability
- Log every failure in command validation and database exceptions.

For detailed test cases, see the **Test Cases** section.
""",
            
            "WebUi.md": f"""# {aggregate_name}Controller

**Namespace:** `WebUi.Areas.{bc_name}.Controllers`  
**Inherits:** `{bc_name}BaseController`  
**Purpose:** Manage CRUD operations for {bc_name} {aggregate_name} using MediatR.

---

## Create {aggregate_name}

**Method:** `POST`  
**Route:** `/{aggregate_name}/{aggregate_name}_Create`

Creates a new {aggregate_name.lower()}.

## Update {aggregate_name}

**Method:** `PUT`  
**Route:** `/{aggregate_name}/{aggregate_name}_Edit/{{id}}`

Updates an existing {aggregate_name.lower()}.

## List {aggregate_name}

**Method:** `GET`  
**Route:** `/{aggregate_name}/{aggregate_name}_List`

Retrieves a list of {aggregate_name.lower()}s.
""",
            
            "ChangeLog.md": f"""# Change History – {aggregate_name}

## Latest Version
- **Version**: 1.0.0
- **Date**: {datetime.now().strftime('%Y-%m-%d')}
- **Changes**:
  * Initial implementation of {aggregate_name} aggregate
  * Basic CRUD operations implemented
  * Domain rules and validations added

## Previous Versions
No previous versions available.

## Migration Notes
No migration notes for initial version.
"""
        }
        
        # Use template content if available, otherwise use fallback
        for file_name, fallback_content in fallback_docs.items():
            target_path = agg_dir / file_name
            
            # Try to use template content with basic substitutions
            if file_name in template_files and template_files[file_name]:
                try:
                    content = template_files[file_name]
                    # Basic template variable substitution
                    content = content.replace("ContractType", aggregate_name)
                    content = content.replace("HR", bc_name)
                    content = content.replace("Hr", bc_name)
                    target_path.write_text(content, encoding='utf-8')
                except Exception:
                    target_path.write_text(fallback_content, encoding='utf-8')
            else:
                target_path.write_text(fallback_content, encoding='utf-8')
            
            Logger.debug(f"Created fallback {target_path}")