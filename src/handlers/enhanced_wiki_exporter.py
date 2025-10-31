from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import asyncio
import time

from pydantic import Field

import config
from utils import Logger
from .base_handler import BaseHandler, BaseHandlerConfig
from agents.ddd_analyzer_agent import DDDAnalyzerAgent, DDDAnalyzerAgentConfig


class EnhancedWikiExporterConfig(BaseHandlerConfig):
    output_path: Path = Field(default=Path("Docs"), description="Output path for generated Wiki (Docs/) folder")
    template_path: Path = Field(default=Path(".ai/temp"), description="Path to template files for AI guidance")


class EnhancedWikiExporterHandler(BaseHandler):
    """
    Enhanced wiki exporter that uses DDD analysis to generate proper 
    bounded context and aggregate documentation structure.
    """
    
    def __init__(self, config: EnhancedWikiExporterConfig):
        super().__init__(config)
        self.config: EnhancedWikiExporterConfig = config

    async def handle(self) -> None:
        """
        Two-phase documentation generation:
        Phase 1: Scan repository and create directory structure with empty .md files
        Phase 2: Fill each .md file with AI-generated content using templates
        """
        start_time = time.time()
        
        print("=" * 80)
        print("🚀 ENHANCED WIKI EXPORTER - Two-Phase Generation")
        print("=" * 80)
        
        Logger.info("Starting enhanced wiki exporter handler")

        repo_path: Path = self.config.repo_path
        out_root: Path = (repo_path / self.config.output_path).resolve()

        print(f"📂 Repository: {repo_path}")
        print(f"📁 Output: {out_root}")
        print(f"📋 Template: {self.config.template_path}")
        print("=" * 80)
        
        Logger.info(f"Exporting wiki to {out_root}")
        Logger.info(f"Analyzing .NET project at {repo_path}")

        # Initialize DDD analyzer
        ddd_config = DDDAnalyzerAgentConfig(
            repo_path=repo_path
        )
        ddd_analyzer = DDDAnalyzerAgent(ddd_config)

        # Load template files for AI guidance
        template_files = self._load_template_files()

        # ============================================================
        # PHASE 1: Structure Creation (No AI)
        # ============================================================
        print("\n" + "=" * 80)
        print("📦 PHASE 1: Creating Directory Structure (No AI)")
        print("=" * 80)
        Logger.info("Phase 1: Creating directory structure")
        
        # Analyze DDD structure (no AI, just file system scan)
        print("🔍 Scanning repository for bounded contexts and aggregates...")
        Logger.info("Analyzing DDD structure...")
        
        bounded_contexts = await ddd_analyzer.analyze_ddd_structure()

        if not bounded_contexts:
            Logger.warning("No bounded contexts found!")
            print("❌ No bounded contexts found!")
            return

        total_aggregates = sum(len(bc.aggregates) for bc in bounded_contexts.values())
        total_files = total_aggregates * 6  # 6 layer files per aggregate
        
        print(f"✅ Found {len(bounded_contexts)} bounded contexts")
        print(f"✅ Found {total_aggregates} aggregates")
        print(f"📝 Will generate {total_files} documentation files")
        
        Logger.info(f"Found {len(bounded_contexts)} bounded contexts with {total_aggregates} aggregates")

        # Create directory structure
        print("\n📁 Creating directory structure...")
        file_paths = self._create_directory_structure(out_root, bounded_contexts)
        
        print(f"✅ Created {len(file_paths)} empty documentation files")
        Logger.info(f"Created {len(file_paths)} empty files in directory structure")

        # ============================================================
        # PHASE 2: AI Content Generation
        # ============================================================
        print("\n" + "=" * 80)
        print("🤖 PHASE 2: Filling Files with AI-Generated Content")
        print("=" * 80)
        Logger.info("Phase 2: Generating AI content")
        
        print(f"⏱️  Estimated time: {(total_files * 12) // 60} minutes")
        print(f"🎯 Processing {len(file_paths)} files...")
        
        # Process files in batches with progress monitoring
        await self._fill_files_with_ai(ddd_analyzer, bounded_contexts, template_files, out_root)
        
        # Summary
        elapsed = time.time() - start_time
        print("\n" + "=" * 80)
        print("✅ DOCUMENTATION GENERATION COMPLETED")
        print("=" * 80)
        print(f"📊 Bounded Contexts: {len(bounded_contexts)}")
        print(f"📦 Aggregates: {total_aggregates}")
        print(f"📄 Files Generated: {total_files}")
        print(f"⏱️  Total Time: {elapsed // 60:.0f}m {elapsed % 60:.0f}s")
        print(f"📁 Output: {out_root}")
        print("=" * 80)
        
        Logger.info(f"Enhanced wiki export completed to {out_root}")
        Logger.info(f"Generated {total_files} files for {len(bounded_contexts)} bounded contexts")

    def _create_directory_structure(
        self, 
        out_root: Path, 
        bounded_contexts: Dict[str, any]
    ) -> List[Tuple[Path, str, str, str]]:
        """
        Phase 1: Create all directories and empty .md files
        Returns: List of (file_path, bc_name, aggregate_name, layer_name) tuples
        """
        file_paths = []
        
        # Create BoundedContext folder
        bc_folder = "BoundedContext"
        bc_root = out_root / bc_folder
        bc_root.mkdir(parents=True, exist_ok=True)
        
        # Create bounded context order file
        bc_names = sorted(bounded_contexts.keys())
        (bc_root / ".order").write_text("\n".join(bc_names))
        
        layer_files = ["Application.md", "ChangeLog.md", "Domain.md", "Infrastructure.md", "Quality.md", "WebUi.md"]
        
        for bc_name, bc_info in bounded_contexts.items():
            bc_dir = bc_root / bc_name
            bc_dir.mkdir(parents=True, exist_ok=True)
            
            # Create .order file for bounded context aggregates
            if bc_info.aggregates:
                (bc_dir / ".order").write_text("\n".join(sorted(bc_info.aggregates)))
            
            for aggregate_name in bc_info.aggregates:
                agg_dir = bc_dir / aggregate_name
                agg_dir.mkdir(parents=True, exist_ok=True)
                
                # Create .order file for aggregate layers
                (agg_dir / ".order").write_text("\n".join([f.replace('.md', '') for f in layer_files]))
                
                # Create empty .md files
                for layer_file in layer_files:
                    file_path = agg_dir / layer_file
                    if not file_path.exists():
                        file_path.write_text("", encoding='utf-8')
                    
                    layer_name = layer_file.replace('.md', '')
                    file_paths.append((file_path, bc_name, aggregate_name, layer_name))
                    
                    print(f"  📄 Created: {bc_name}/{aggregate_name}/{layer_file}")
        
        return file_paths

    async def _fill_files_with_ai(
        self,
        ddd_analyzer: DDDAnalyzerAgent,
        bounded_contexts: Dict[str, any],
        template_files: Dict[str, str],
        out_root: Path
    ):
        """
        Phase 2: Fill empty .md files with AI-generated content
        Process in parallel batches with progress monitoring
        """
        bc_root = out_root / "BoundedContext"
        
        processed = 0
        failed = 0
        total_aggregates = sum(len(bc.aggregates) for bc in bounded_contexts.values())
        
        # Semaphore for controlling concurrency (from environment variable)
        max_concurrent = config.DDD_MAX_CONCURRENT
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_aggregate_with_semaphore(bc_idx, bc_name, bc_info, agg_idx, aggregate_name):
            """Process a single aggregate with concurrency control"""
            nonlocal processed, failed
            
            async with semaphore:
                agg_start = time.time()
                
                print(f"\n🔄 [{bc_idx}.{agg_idx}] Processing {bc_name}/{aggregate_name}...")
                Logger.info(f"Generating documentation for {bc_name}/{aggregate_name}")
                
                bc_dir = bc_root / bc_name
                agg_dir = bc_dir / aggregate_name
                
                try:
                    # Generate documentation using AI
                    docs = await ddd_analyzer.generate_aggregate_documentation(
                        bc_name, 
                        aggregate_name,
                        template_files
                    )
                    
                    # Write generated content to files
                    for layer_file, content in docs.items():
                        target_path = agg_dir / layer_file
                        target_path.write_text(content, encoding='utf-8')
                        processed += 1
                        
                        # Extract first line for preview
                        preview = content.split('\n')[0][:60] if content else "empty"
                        print(f"  ✅ {layer_file:20s} ({len(content):5d} chars) - {preview}...")
                    
                    agg_elapsed = time.time() - agg_start
                    print(f"  ⏱️  Completed in {agg_elapsed:.1f}s ({len(docs)} files)")
                    
                except Exception as e:
                    Logger.error(f"Error generating docs for {bc_name}/{aggregate_name}: {e}")
                    print(f"  ❌ Error: {str(e)[:80]}")
                    
                    # Create fallback documentation
                    self._create_fallback_documentation(agg_dir, bc_name, aggregate_name, template_files)
                    failed += 6
                
                # Progress summary
                progress_pct = (processed + failed) / (total_aggregates * 6) * 100
                print(f"  📊 Progress: {processed} files processed, {failed // 6} fallbacks, {progress_pct:.1f}% complete")
        
        # Create tasks for all aggregates
        tasks = []
        for bc_idx, (bc_name, bc_info) in enumerate(bounded_contexts.items(), 1):
            print(f"\n{'=' * 60}")
            print(f"📦 Bounded Context {bc_idx}/{len(bounded_contexts)}: {bc_name}")
            print(f"{'=' * 60}")
            
            for agg_idx, aggregate_name in enumerate(bc_info.aggregates, 1):
                task = process_aggregate_with_semaphore(bc_idx, bc_name, bc_info, agg_idx, aggregate_name)
                tasks.append(task)
        
        # Process all aggregates in parallel with controlled concurrency
        print(f"\n⚡ Processing {len(tasks)} aggregates with max {max_concurrent} concurrent requests...")
        await asyncio.gather(*tasks)

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