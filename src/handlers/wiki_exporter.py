from datetime import datetime
import os
from pathlib import Path
from typing import Dict, List
import re

from pydantic import BaseModel, Field

from utils import Logger
from .base_handler import BaseHandler, BaseHandlerConfig


class WikiExporterConfig(BaseHandlerConfig):
	output_path: Path = Field(default=Path("Docs"), description="Output path for generated Wiki (Docs/) folder")


class WikiExporterHandler(BaseHandler):
	def __init__(self, config: WikiExporterConfig):
		super().__init__(config)

	async def handle(self) -> None:
		Logger.info("Starting wiki exporter handler")

		repo_path: Path = self.config.repo_path
		out_root: Path = (self.config.repo_path / self.config.output_path).resolve()

		Logger.info(f"Exporting wiki to {out_root}")

		# Create BoundedContext folder only
		bc_folder = "BoundedContext"
		p = out_root / bc_folder
		p.mkdir(parents=True, exist_ok=True)
		# create .order file used by Azure DevOps Wiki ordering
		order_file = p / ".order"
		if not order_file.exists():
			order_file.write_text("")

		# Load analyzer outputs if present - we'll still load these for potential use in documentation
		ai_docs_dir = repo_path / ".ai" / "docs"
		ai_docs: Dict[str, str] = {}
		if ai_docs_dir.exists() and ai_docs_dir.is_dir():
			for md in ai_docs_dir.iterdir():
				if md.is_file() and md.suffix.lower() == ".md":
					try:
						ai_docs[md.name] = md.read_text(encoding="utf-8")
					except Exception as e:
						Logger.warning(f"Failed to read ai doc {md}: {e}")

		# common heuristics used by extraction logic
		ignore_names = set(["application", "domain", "infrastructure", "webui", "commands", "queries", "validators", "handlers", "dto", "dtos", "models", "common", "tests", "controllers", "repositories", "migrations"])
		verbs = [
			'create', 'update', 'delete', 'get', 'add', 'remove', 'search', 'import', 'export'
		]

		def extract_entity_name(path_parts: List[str], filename: str) -> str:
			"""Extract entity name from path or filename.

			Behavior:
			- Prefer the folder after 'Definitions' or 'Entity'.
			- Otherwise pick the nearest meaningful parent folder (skip technical folders).
			- As a last resort, derive from Command/Query filenames like CreateDegreeCommand -> Degree.
			- Return empty string when no reasonable entity is found (we'll skip these to avoid creating BC-level files).
			"""
			# function will use ignore_names and verbs defined in outer scope

			# Prefer Definitions/ or Entity/ folders
			for i, part in enumerate(path_parts):
				if part.lower() in ["definitions", "entity", "entities"]:
					if len(path_parts) > i + 1:
						candidate = path_parts[i + 1]
						# Normalize: remove trailing 's' for plural folders like 'ContractTypes' -> 'ContractType'
						if candidate.lower().endswith('s') and len(candidate) > 1:
							candidate = candidate[:-1]
						# ignore candidate that look like verbs
						if not any(candidate.lower().startswith(v) for v in verbs):
							return candidate

			# If there's a Commands/Queries folder, take the parent folder as the aggregate
			for i, part in enumerate(path_parts):
				if part.lower() in ['commands', 'queries'] and i > 0:
					candidate = path_parts[i-1]
					if candidate.lower().endswith('s') and len(candidate) > 1:
						candidate = candidate[:-1]
					if not any(candidate.lower().startswith(v) for v in verbs):
						return candidate

			# Choose nearest meaningful folder (walk backwards skipping technical folders and filename)
			for folder in reversed(path_parts[:-1]):
				if folder and folder.lower() not in ignore_names:
					candidate = folder
					if candidate.lower().endswith('s') and len(candidate) > 1:
						candidate = candidate[:-1]
					# exclude obvious non-entity tokens and verb-like folders
					if len(candidate) > 1 and not candidate.lower().endswith(('info', 'dto', 'model', 'validator', 'command', 'query')) and not any(candidate.lower().startswith(v) for v in verbs):
						return candidate

			# Fallback: extract from filename patterns like CreateDegreeCommand
			if filename.endswith('.cs'):
				name = filename[:-3]
				# remove known suffixes
				for suffix in ['Command', 'Query', 'Dto', 'Model', 'Info', 'Validator']:
					if name.endswith(suffix):
						name = name[:-len(suffix)]
				# remove common prefixes used for actions
				for prefix in ['Create', 'Update', 'Delete', 'Get', 'Add', 'Remove']:
					if name.startswith(prefix):
						name = name[len(prefix):]
				if name and not name.lower() in ignore_names:
					if name.lower().endswith('s'):
						name = name[:-1]
					return name

			# No good entity found
			return ""

		# Detect bounded contexts and entities by scanning .cs files
		contexts: Dict[str, Dict[str, List[Path]]] = {}

		for cs in repo_path.rglob("*.cs"):
			try:
				parts = cs.relative_to(repo_path).parts
			except Exception:
				parts = cs.parts

			# find index of 'Application' or 'Domain' in path parts
			idx = None
			for i, part in enumerate(parts):
				if part.lower() in ["application", "domain"]:
					idx = i
					break

			if idx is None:
				# fallback: take top-level folder as potential bounded context
				if len(parts) >= 2:
					bc = parts[0]
				else:
					continue
			else:
				# bounded context is the first segment after Application/Domain
				if len(parts) > idx + 1:
					bc = parts[idx + 1]
				else:
					continue

			# Try to derive aggregate from namespace in the file (more reliable than path folders)
			namespace_agg = ""
			try:
				head = cs.read_text(encoding='utf-8', errors='ignore')[:4096]
				m = re.search(r"namespace\s+([A-Za-z0-9_\.]+)", head)
				if m:
					ns = m.group(1)
					parts_ns = ns.split('.')
					# find Application or Domain in namespace
					if 'Application' in parts_ns:
						ai = parts_ns.index('Application')
						if len(parts_ns) > ai + 1:
							bc_from_ns = parts_ns[ai + 1]
							# prefer Definitions/ pattern
							if 'Definitions' in parts_ns:
								di = parts_ns.index('Definitions')
								if len(parts_ns) > di + 1:
									namespace_agg = parts_ns[di + 1]
							elif 'Commands' in parts_ns:
								ci = parts_ns.index('Commands')
								if ci > 0:
									namespace_agg = parts_ns[ci - 1]
							else:
								# fallback: take the part after Application as aggregate candidate
								if len(parts_ns) > ai + 2:
									namespace_agg = parts_ns[ai + 2]
					elif 'Domain' in parts_ns:
						di = parts_ns.index('Domain')
						if len(parts_ns) > di + 1:
							namespace_agg = parts_ns[di + 1]
			except Exception:
				namespace_agg = ""

			# If namespace-derived aggregate exists and looks valid, use it
			entity = ""
			if namespace_agg:
				cand = namespace_agg
				if cand.lower().endswith('s'):
					cand = cand[:-1]
				if not any(cand.lower().startswith(v) for v in verbs) and cand.lower() not in [n.lower() for n in ignore_names]:
					entity = cand

			# Fallback to path-based extraction
			if not entity:
				entity = extract_entity_name(list(parts), cs.name)
				if not entity:
					continue

			# normalize entity and add
			entity = entity.replace(' ', '')
			contexts.setdefault(bc, {}).setdefault(entity, []).append(cs)

		# Create BoundedContext structure
		bc_root = out_root / "BoundedContext"
		for bc_name, aggregates in contexts.items():
			bc_dir = bc_root / bc_name
			bc_dir.mkdir(parents=True, exist_ok=True)
			# .order for BC
			(bc_dir / ".order").write_text("")
			# Remove any top-level .md pages under BC to avoid duplicated aggregate-level docs
			for existing in list(bc_dir.iterdir()):
				if existing.is_file() and existing.suffix.lower() == '.md':
					try:
						existing.unlink()
					except Exception:
						pass

			for agg_name, files in aggregates.items():
				agg_dir = bc_dir / agg_name
				agg_dir.mkdir(parents=True, exist_ok=True)
				(agg_dir / ".order").write_text("")

				# create per-layer files expected by your wiki
				layer_files = ["Application.md", "ChangeLog.md", "Domain.md", "Infrastructure.md", "Quality.md", "WebUi.md"]
				# Write .order file with names without .md extension
				order_names = [f.replace(".md", "") for f in layer_files]
				(agg_dir / ".order").write_text("\n".join(order_names))
				
				for lf in layer_files:
					target = agg_dir / lf
					if target.exists():
						continue

					# Generate content based on layer
					if lf == "Application.md":
						content = [f"# Application Layer – {agg_name}\n\n"]
						content.append("## Commands\n\n")

						# Group files by command type
						commands = [f for f in files if f.name.endswith("Command.cs")]
						for cmd_file in sorted(commands):
							try:
								cmd_content = cmd_file.read_text(encoding="utf-8")
								cmd_name = cmd_file.stem  # filename without extension
								
								# Extract command properties
								class_start = cmd_content.find(f"public class {cmd_name}")
								if class_start != -1:
									class_end = cmd_content.find("}", class_start)
									if class_end != -1:
										cmd_props = cmd_content[class_start:class_end]
										
										# Add command documentation
										content.append(f"### {cmd_name}\n")
										if cmd_name.startswith("Create"):
											purpose = "Creates a new"
										elif cmd_name.startswith("Update"):
											purpose = "Updates an existing"
										elif cmd_name.startswith("Delete"):
											purpose = "Deletes an existing"
										else:
											purpose = "Manages"
											
										content.append(f"- **Purpose**: {purpose} {agg_name.lower()}.\n")
										content.append(f"- **Handler**: Validates input, {'creates' if 'Create' in cmd_name else 'updates' if 'Update' in cmd_name else 'deletes' if 'Delete' in cmd_name else 'processes'} the entity.\n\n")
										
										content.append("```csharp\n")
										content.append(cmd_props)
										content.append("}\n```\n\n")
							except Exception as e:
								Logger.warning(f"Failed to read command file {cmd_file}: {e}")

						body = "".join(content)

					else:
						# Build richer content per layer using heuristics and analyzer snippets
						title = lf.replace('.md','')
						layer_lines: List[str] = [f"# {title} Layer – {agg_name}\n\n"]

						# helper to add file lists and short snippets
						def add_files_section(section_title: str, predicate):
							candidates = [f for f in files if predicate(f)]
							if not candidates:
								return
							layer_lines.append(f"## {section_title}\n\n")
							for cf in sorted(candidates):
								try:
									text = cf.read_text(encoding='utf-8')
								except Exception:
									text = ''
								rel = cf
								try:
									rel = cf.relative_to(repo_path)
								except Exception:
									pass
								layer_lines.append(f"- `{rel.as_posix()}`\n")
								# include a small snippet (first class or interface)
								m = re.search(r"(public|internal)\s+(class|interface|record)\s+\w+", text)
								if m:
									start = m.start()
									snippet = text[start:start+400]
									layer_lines.append("```csharp\n")
									layer_lines.append(snippet.strip() + "\n")
									layer_lines.append("```\n\n")

						# Use analyzer docs snippets relevant to this bc/agg
						for name, content in ai_docs.items():
							if bc_name.lower() in content.lower() or agg_name.lower() in content.lower():
								layer_lines.append(f"<!-- excerpt from {name} -->\n")
								layer_lines.append(content[:800] + "\n\n")

						if title == 'Domain':
							# Entities and value objects
							add_files_section('Entities & Value Objects', lambda p: ('Domain' in p.parts or p.name.lower().endswith('entity.cs') or 'entity' in p.name.lower() or 'aggregate' in p.name.lower()))
							# invariants: look for validation/invariant code
							add_files_section('Invariants & Rules', lambda p: ('Validator' in p.name or 'Invariant' in p.name or 'Rule' in p.name))

						elif title == 'Infrastructure':
							add_files_section('Repositories & Persistence', lambda p: ('Repository' in p.name or 'Infrastructure' in p.parts or 'Persistence' in p.name))
							add_files_section('Integrations', lambda p: ('HttpClient' in p.name or 'Client' in p.name or 'Integration' in p.name))

						elif title == 'Quality':
							# validators and tests
							add_files_section('Validators', lambda p: p.name.lower().endswith('validator.cs') or 'validator' in p.name.lower())
							add_files_section('Tests', lambda p: 'test' in ''.join(p.parts).lower() or p.suffix.lower() == '.cs' and ('tests' in p.parts or p.name.lower().endswith('tests.cs')))

						elif title == 'WebUi':
							add_files_section('Controllers & Endpoints', lambda p: p.name.endswith('Controller.cs') or 'controllers' in [pp.lower() for pp in p.parts])

						elif title == 'ChangeLog':
							# prefer an analyzer-provided changelog snippet if available
							if 'changelog.md' in ai_docs:
								layer_lines.append(ai_docs['changelog.md'])
							else:
								layer_lines.append('No changelog data available. Consider enabling git-based history extraction.')

						# If no specific sections added, include a source files section
						if len(layer_lines) == 1:
							# only header present: add source files list
							layer_lines.append('## Source files\n\n')
							for f in sorted(files):
								try:
									rel = f.relative_to(repo_path)
								except Exception:
									rel = f
								layer_lines.append(f"- `{rel.as_posix()}`\n")

						body = ''.join(layer_lines)

						target.write_text(body, encoding='utf-8')

		Logger.info(f"Wiki export completed to {out_root}")
		
		return None
