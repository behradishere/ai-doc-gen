#!/usr/bin/env python3

"""
Simple DDD documentation generator without AI complexity
This creates the basic structure with fallback content
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def create_simple_docs(process_all=False):
    dotnet_project_path = Path("/Users/behradafshe/repo/Daya_Backend/Daya_Backend")
    output_path = dotnet_project_path / "Docs"
    
    print(f"🚀 Creating Simple DDD Documentation")
    print(f"📂 Source: {dotnet_project_path}")
    print(f"📁 Output: {output_path}")
    
    # Check if path exists
    if not dotnet_project_path.exists():
        print(f"❌ Path does not exist: {dotnet_project_path}")
        return
    
    # Check if Application folder exists
    app_path = dotnet_project_path / "Application"
    if not app_path.exists():
        print(f"❌ Application folder not found: {app_path}")
        return
    
    # Create output structure
    bc_root = output_path / "BoundedContext"
    bc_root.mkdir(parents=True, exist_ok=True)
    
    # Discover bounded contexts
    contexts = {}
    skip_folders = {
        'Common', 'Shared', 'Base', 'Core', 'Extensions', 
        'Interfaces', 'Abstractions', 'Constants'
    }
    
    print("\n📁 Discovering bounded contexts...")
    for item in app_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            if item.name not in skip_folders:
                contexts[item.name] = item
                print(f"   - {item.name}")
    
    print(f"\n✅ Found {len(contexts)} bounded contexts")
    
    # Create bounded context order file
    bc_names = sorted(contexts.keys())
    (bc_root / ".order").write_text("\n".join(bc_names))
    
    print(f"\n🔄 Generating documentation...")
    
    # Process each bounded context
    processed_count = 0
    items_to_process = list(contexts.items()) if process_all else list(contexts.items())[:10]
    for bc_name, bc_path in items_to_process:
        print(f"\n📦 Processing {bc_name}...")
        
        bc_dir = bc_root / bc_name
        bc_dir.mkdir(parents=True, exist_ok=True)
        
        # Find aggregates in this bounded context
        aggregates = set()
        
        # Strategy 1: Look for Definitions folders
        definitions_path = bc_path / "Definitions"
        if definitions_path.exists():
            for item in definitions_path.iterdir():
                if item.is_dir():
                    aggregates.add(item.name)
        
        # Strategy 2: Look for folders containing Commands or Queries
        for folder in bc_path.rglob("*"):
            if folder.is_dir() and folder != bc_path:
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
        
        final_aggregates = sorted(list(set(cleaned_aggregates)))
        print(f"   Found {len(final_aggregates)} aggregates: {final_aggregates[:3]}{'...' if len(final_aggregates) > 3 else ''}")
        
        if final_aggregates:
            # Create .order file for aggregates
            (bc_dir / ".order").write_text("\n".join(final_aggregates))
            
            # Create documentation for each aggregate
            aggregates_to_process = final_aggregates if process_all else final_aggregates[:3]
            for agg_name in aggregates_to_process:
                print(f"     Creating docs for {agg_name}")
                create_aggregate_docs(bc_dir, bc_name, agg_name)
                processed_count += 1
    
    print(f"\n✅ Documentation generation completed!")
    print(f"📊 Summary:")
    print(f"   - Bounded contexts: {len(contexts)}")
    print(f"   - Processed contexts: {processed_count}")
    print(f"   - Generated aggregate docs: {processed_count}")
    print(f"   - Output location: {output_path}")
    
    # Show some sample files
    print(f"\n📄 Sample generated files:")
    for md_file in bc_root.rglob("*.md"):
        print(f"   {md_file.relative_to(output_path)}")
        if len(list(bc_root.rglob("*.md"))) > 10:
            break

def create_aggregate_docs(bc_dir: Path, bc_name: str, agg_name: str):
    """Create documentation files for an aggregate"""
    agg_dir = bc_dir / agg_name
    agg_dir.mkdir(parents=True, exist_ok=True)
    
    # Create .order file
    layer_files = ["Application", "ChangeLog", "Domain", "Infrastructure", "Quality", "WebUi"]
    (agg_dir / ".order").write_text("\n".join(layer_files))
    
    # Create each documentation file
    docs = {
        "Application.md": f"""# Application Layer – {agg_name}

## Commands

### Create{agg_name}Command
- **Purpose**: Creates a new {agg_name.lower()}.
- **Validation**: Validates input parameters.
- **Handler**: Handles the creation logic.

```csharp
public class Create{agg_name}Command : IRequest<int>
{{
    // Properties would be defined here based on the entity
}}
```

### Update{agg_name}Command
- **Purpose**: Updates an existing {agg_name.lower()}.
- **Validation**: Validates input parameters and existence.
- **Handler**: Handles the update logic.

### Delete{agg_name}Command
- **Purpose**: Deletes an existing {agg_name.lower()}.
- **Validation**: Validates existence and constraints.
- **Handler**: Handles the deletion logic.

## Queries

### Get{agg_name}Query
- **Purpose**: Retrieves {agg_name.lower()} information.
- **Handler**: Handles the query logic.
- **Return Type**: {agg_name}Dto
""",
        
        "Domain.md": f"""# Domain Model – {agg_name}

The **{agg_name}** entity represents {agg_name.lower()} in the {bc_name} bounded context.

### Table And Schema
```csharp
[Table("{agg_name}s", Schema = "{bc_name}")]
```

### Entity Definition:
```csharp
public class {agg_name}
{{
    public int {agg_name}Id {{ get; set; }}
    // Additional properties would be defined here
}}
```

### RELATIONS
```csharp
// Related entities would be listed here
```

### Business Rules
- Standard validation rules apply
- Entity integrity must be maintained
- Related entities must be valid
""",
        
        "Infrastructure.md": f"""# Infrastructure: {agg_name} Configuration

**Namespace:** `Infrastructure.Persistence.Configurations.{bc_name}`  
**File:** `{agg_name}Configuration.cs`  
**Database Table:** `[{bc_name}].[{agg_name}s]`  
**Entity:** `Domain.Entity.{bc_name}.{agg_name}`  

---

## Entity Configuration

| Property | Configuration | Notes |
|-----------|----------------|-------|
| `{agg_name}Id` | `HasKey()` | Defines the primary key. |

## Repository Implementation
- **Interface**: I{agg_name}Repository
- **Implementation**: {agg_name}Repository
- **Key Methods**: GetById, GetAll, Add, Update, Delete

## External Services
No external service integrations documented.

## Caching Strategy
No specific caching strategy implemented.
""",
        
        "Quality.md": f"""# Quality & Testing – {agg_name}

### Unit Tests
- **Create{agg_name}Command**: Validates input and creation logic.
- **Update{agg_name}Command**: Validates update logic and constraints.
- **Delete{agg_name}Command**: Validates deletion logic and references.

### Performance Tests
- Verify list queries perform optimally when paging large datasets.

### Integration Tests
- Test complete workflows from API to database.

### Observability
- Log every failure in command validation and database exceptions.
- Monitor performance metrics for query operations.

For detailed test cases, see the **Test Cases** section.
""",
        
        "WebUi.md": f"""# {agg_name}Controller

**Namespace:** `WebUi.Areas.{bc_name}.Controllers`  
**Inherits:** `{bc_name}BaseController`  
**Purpose:** Manage CRUD operations for {bc_name} {agg_name} using MediatR.

---

## Create {agg_name}

**Method:** `POST`  
**Route:** `/{agg_name}/{agg_name}_Create`

Creates a new {agg_name.lower()}.

**Request Body:**
```json
{{
  "name": "Sample Name",
  "description": "Sample Description"
}}
```

## Update {agg_name}

**Method:** `PUT`  
**Route:** `/{agg_name}/{agg_name}_Edit/{{id}}`

Updates an existing {agg_name.lower()}.

## List {agg_name}

**Method:** `GET`  
**Route:** `/{agg_name}/{agg_name}_List`

Retrieves a list of {agg_name.lower()}s.

**Response:**
```json
{{
  "succeeded": true,
  "data": [
    {{
      "id": 1,
      "name": "Sample Name"
    }}
  ]
}}
```
""",
        
        "ChangeLog.md": f"""# Change History – {agg_name}

## Latest Version
- **Version**: 1.0.0
- **Date**: {datetime.now().strftime('%Y-%m-%d')}
- **Changes**:
  * Initial implementation of {agg_name} aggregate
  * Basic CRUD operations implemented
  * Domain rules and validations added

## Previous Versions
No previous versions available.

## Migration Notes
No migration notes for initial version. This is the baseline implementation.

## Future Enhancements
- Performance optimizations
- Additional business rules
- Enhanced validation
- API improvements
"""
    }
    
    # Write all documentation files
    for file_name, content in docs.items():
        (agg_dir / file_name).write_text(content, encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description='Generate simple DDD documentation')
    parser.add_argument('--full', action='store_true', help='Process all bounded contexts (not just first 10)')
    args = parser.parse_args()
    
    create_simple_docs(process_all=args.full)

if __name__ == "__main__":
    main()