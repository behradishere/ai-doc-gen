import os

from opentelemetry import trace
from pydantic_ai import ModelRetry, Tool

import config
from utils import Logger


class FileReadTool:
    def __init__(self, repo_path=None):
        self.repo_path = repo_path

    def get_tool(self):
        return Tool(self._run, name="Read-File", takes_ctx=False, max_retries=config.TOOL_FILE_READER_MAX_RETRIES)

    def _run(self, file_path: str, line_number: int = 0, line_count: int = 200) -> str:
        """Read a file and return its contents.

        Args:
            file_path (str): The path to the file to read.
            line_number (int, optional): The line number to start reading from (0-indexed). Defaults to 0.
            line_count (int, optional): The number of lines to read. Defaults to 200. Set to -1 to read all lines.

        Returns:
            str: The contents of the file from the specified line number for the specified number of lines.
                If the file is a .go file, returns an error message directing to use the Go-Analyzer-Tool.
                If the file cannot be read, returns an error message with details about the failure.
        """
        try:
            Logger.debug("Tool Call: Read File", data={"file_path": file_path})
        except:
            # Fallback if logger not initialized
            print(f"[DEBUG] Tool Call: Read File - {file_path}")

        try:
            trace.get_current_span().set_attribute("input", file_path)
        except:
            # Ignore tracing errors
            pass

        # Handle both absolute and relative paths - try multiple resolution strategies
        tried_paths = []
        resolved_path = None
        
        # Strategy 1: Try original path as-is
        if os.path.exists(file_path):
            resolved_path = file_path
        else:
            tried_paths.append(file_path)
            
            # Strategy 2: Try as absolute path
            abs_path = os.path.abspath(file_path)
            if os.path.exists(abs_path):
                resolved_path = abs_path
            else:
                tried_paths.append(abs_path)
                
                # Strategy 3: Try relative to current working directory
                cwd_path = os.path.join(os.getcwd(), file_path)
                if os.path.exists(cwd_path):
                    resolved_path = cwd_path
                else:
                    tried_paths.append(cwd_path)
                    
                    # Strategy 4: Try relative to repo_path if available
                    if self.repo_path and not os.path.isabs(file_path):
                        repo_relative_path = os.path.join(str(self.repo_path), file_path)
                        if os.path.exists(repo_relative_path):
                            resolved_path = repo_relative_path
                        else:
                            tried_paths.append(repo_relative_path)
                            
                            # Strategy 5: Try common .NET patterns if file looks like a class name
                            if '.' not in file_path and not file_path.endswith('.cs'):
                                # Try as .cs file in various common locations
                                common_patterns = [
                                    f"Application/{file_path}.cs",
                                    f"Domain/{file_path}.cs", 
                                    f"Infrastructure/{file_path}.cs",
                                    f"Application/*/{file_path}.cs",
                                    f"Domain/*/{file_path}.cs"
                                ]
                                
                                for pattern in common_patterns:
                                    if '*' in pattern:
                                        # Handle wildcard patterns
                                        import glob
                                        matches = glob.glob(os.path.join(str(self.repo_path), pattern))
                                        if matches:
                                            resolved_path = matches[0]  # Take first match
                                            break
                                        else:
                                            tried_paths.append(os.path.join(str(self.repo_path), pattern))
                                    else:
                                        pattern_path = os.path.join(str(self.repo_path), pattern)
                                        if os.path.exists(pattern_path):
                                            resolved_path = pattern_path
                                            break
                                        else:
                                            tried_paths.append(pattern_path)
        
        if resolved_path is None:
            try:
                Logger.warning(f"File not found: {file_path}, tried paths: {tried_paths}")
            except:
                print(f"[WARNING] File not found: {file_path}, tried paths: {tried_paths}")
            
            # Instead of raising an error, return a helpful message
            return f"File not found: {file_path}\n\nThis file may not exist in the current project structure. Consider:\n- Checking if the file exists with a different name\n- Looking for similar files in the same directory\n- Using List-Files tool to explore available files\n\nTried paths:\n" + "\n".join(f"- {path}" for path in tried_paths[:3])

        try:
            with open(resolved_path, "r") as file:
                lines = file.readlines()
                total_lines = len(lines)

                if line_number > 0:
                    lines = lines[line_number:]
                if line_count > 0:
                    lines = lines[:line_count]

                output = (
                    f"File Line:{line_number} to {line_number + line_count} from: {total_lines}\n--- start---\n"
                    + "".join(lines)
                    + "\n--- end ---\n"
                )
                trace.get_current_span().set_attribute("output", output)

                return output
        except PermissionError:
            try:
                Logger.error(f"Permission denied reading file: {file_path} -> {resolved_path}")
            except:
                print(f"[ERROR] Permission denied reading file: {file_path} -> {resolved_path}")
            raise ModelRetry(message=f"Permission denied when trying to read file: {resolved_path}")
        except Exception as e:
            try:
                Logger.error(f"Failed to read file: {file_path} -> {resolved_path}, error: {str(e)}")
            except:
                print(f"[ERROR] Failed to read file: {file_path} -> {resolved_path}, error: {str(e)}")
            raise ModelRetry(message=f"Failed to read file {resolved_path}. {str(e)}")
