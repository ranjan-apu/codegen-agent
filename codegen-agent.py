import os
import json
import subprocess
import platform
import shutil
from typing import Dict, Any, List, Optional

from openai import OpenAI, APIError
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
AGENT_MODEL = "openrouter/optimus-alpha"

def write_file(params: Dict[str, Any]) -> str:
    """Write content to a file. Creates parent directories if they don't exist."""
    path = params.get("path")
    content = params.get("content")
    if not path or content is None:
        return "Error: 'path' and 'content' are required."
    try:
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File '{path}' written successfully."
    except Exception as e:
        return f"Error writing file '{path}': {e}"

def read_file(params: Dict[str, Any]) -> str:
    """Read the entire content from a specified file."""
    path = params.get("path")
    if not path:
        return "Error: 'path' is required."
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found at '{path}'."
    except Exception as e:
        return f"Error reading file '{path}': {e}"

def run_command(params: Dict[str, Any]) -> str:
    """Run a shell command in the *current* directory and return its exit code, stdout, and stderr."""
    command = params.get("command")
    if not command:
        return "Error: 'command' is required."
    try:
        print(f"[DEBUG] Running command: {command}")
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
            encoding='utf-8',
            errors='replace',
            cwd=os.getcwd()
        )
        output = f"Exit Code: {result.returncode}\n"
        if result.stdout:
            output += f"STDOUT:\n{result.stdout.strip()}\n"
        else:
            output += "STDOUT: (empty)\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr.strip()}\n"
        else:
             output += "STDERR: (empty)\n"

        if result.returncode != 0:
             output += f"\n[INFO] Command execution may have failed (non-zero exit code: {result.returncode}). Review STDERR."

        max_output_length = 4000
        if len(output) > max_output_length:
             output = output[:max_output_length] + "\n... (output truncated)"

        return output.strip()
    except Exception as e:
        return f"Error running command '{command}': {e}"

def run_in_new_terminal(params: Dict[str, Any]) -> str:
    """Run a shell command in a new Terminal window (macOS only). Starts in HOME directory unless 'cd' is part of the command."""
    command = params.get("command")
    if not command:
        return "Error: 'command' is required."
    if platform.system() != "Darwin":
        return "Error: run_in_new_terminal only works on macOS. Use run_command instead."
    try:
        safe_command = command.replace('\\', '\\\\').replace('"', '\\"')
        script = f'''osascript -e 'tell application "Terminal" to do script "{safe_command}" activate' '''
        print(f"[DEBUG] Running in new terminal: {script}")
        subprocess.run(script, shell=True, check=True)
        return f"Command '{command}' launched in a new Terminal window. Note: It runs independently and starts in the user's home directory unless the command includes 'cd'."
    except Exception as e:
        return f"Error running command '{command}' in new terminal: {e}"

def append_file(params: Dict[str, Any]) -> str:
    """Append content to the end of a file. Creates the file and directories if they don't exist."""
    path = params.get("path")
    content = params.get("content")
    if not path or content is None:
        return "Error: 'path' and 'content' are required."
    try:
        dir_path = os.path.dirname(path)
        if dir_path:
             os.makedirs(dir_path, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        return f"Content appended to '{path}'."
    except Exception as e:
        return f"Error appending to file '{path}': {e}"

def list_files(params: Dict[str, Any]) -> str:
    """List all files and directories within a specified directory."""
    directory = params.get("directory", ".")
    try:
        entries = os.listdir(directory)
        detailed_entries = []
        for entry in entries:
            try:
                entry_path = os.path.join(directory, entry)
                is_dir = os.path.isdir(entry_path)
                detailed_entries.append({"name": entry, "type": "directory" if is_dir else "file"})
            except OSError:
                detailed_entries.append({"name": entry, "type": "unknown/inaccessible"})
        return json.dumps(detailed_entries)
    except FileNotFoundError:
        return f"Error: Directory not found at '{directory}'."
    except Exception as e:
        return f"Error listing files in '{directory}': {e}"

def search_in_file(params: Dict[str, Any]) -> str:
    """Search for a specific string within a file and return matching lines with line numbers."""
    path = params.get("path")
    query = params.get("query")
    if not path or not query:
        return "Error: 'path' and 'query' are required."
    try:
        matches = []
        with open(path, "r", encoding="utf-8", errors='replace') as f:
            for i, line in enumerate(f):
                if query in line:
                    matches.append({"line_number": i + 1, "content": line.strip()})
        if not matches:
            return f"No matches found for '{query}' in file '{path}'."
        max_matches = 50
        if len(matches) > max_matches:
             return json.dumps(matches[:max_matches]) + f"\n... (truncated, {len(matches) - max_matches} more matches found)"
        return json.dumps(matches)
    except FileNotFoundError:
        return f"Error: File not found at '{path}'."
    except Exception as e:
        return f"Error searching in file '{path}': {e}"

def delete_file(params: Dict[str, Any]) -> str:
    """Delete a single file."""
    path = params.get("path")
    if not path:
        return "Error: 'path' is required."
    try:
        os.remove(path)
        return f"File '{path}' deleted successfully."
    except FileNotFoundError:
        return f"Error: File not found at '{path}', cannot delete."
    except IsADirectoryError:
         return f"Error: '{path}' is a directory. Use delete_directory tool."
    except Exception as e:
        return f"Error deleting file '{path}': {e}"

def create_directory(params: Dict[str, Any]) -> str:
    """Create a new directory, including parent directories if needed."""
    directory = params.get("directory")
    if not directory:
        return "Error: 'directory' is required."
    try:
        os.makedirs(directory, exist_ok=True)
        return f"Directory '{directory}' created or already exists."
    except Exception as e:
        return f"Error creating directory '{directory}': {e}"

def delete_directory(params: Dict[str, Any]) -> str:
    """Delete a directory and all its contents recursively. Use with caution!"""
    directory = params.get("directory")
    if not directory:
        return "Error: 'directory' is required."
    if not os.path.isdir(directory):
         return f"Error: '{directory}' is not a valid directory."
    abs_path = os.path.abspath(directory)
    home_dir = os.path.expanduser("~")
    if directory.strip() in ['.', '..', '/'] or abs_path == home_dir :
        return f"Error: Safety preventions disallow deleting '{directory}'."
    try:
        shutil.rmtree(directory)
        return f"Directory '{directory}' and its contents deleted successfully."
    except Exception as e:
        return f"Error deleting directory '{directory}': {e}"

def ask_user_for_feedback(params: Dict[str, Any]) -> str:
    """Pause execution and ask the human user a clarifying question. Returns the user's response."""
    question = params.get("question")
    if not question:
        return "Error: 'question' parameter is required for ask_user_for_feedback."

    print(f"\n[AGENT ASKS] {question}")
    try:
        user_response = input("Your Response>> ")
        return f"User response to '{question}': {user_response}"
    except EOFError:
        return "Error: Could not get user input (EOF reached)."
    except Exception as e:
        return f"Error getting user input: {e}"


AVAILABLE_TOOLS = {
    "write_file": {
        "fn": write_file,
        "description": "Write content to a file. Creates parent directories if needed. Overwrites existing files.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path (including filename) where content should be written."},
                "content": {"type": "string", "description": "The text content to write into the file."}
            },
            "required": ["path", "content"]
        }
    },
    "read_file": {
        "fn": read_file,
        "description": "Read the entire content from a specified file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path to the file to be read."}
            },
            "required": ["path"]
        }
    },
    "run_command": {
        "fn": run_command,
        "description": "Execute a shell command in the agent's current working directory and capture its exit code, stdout, and stderr. Use for commands that complete and exit (compile, install, test, format, run scripts, get current path 'pwd', etc.).",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute (e.g., 'python script.py', 'javac Main.java', 'npm install', 'cargo run', 'pwd')."}
            },
            "required": ["command"]
        }
    },
    "run_in_new_terminal": {
        "fn": run_in_new_terminal,
        "description": "Execute a shell command in a NEW, separate Terminal window (macOS only). The new terminal starts in the user's HOME directory. Use for long-running foreground processes (like dev servers 'npm run dev') or when the user should see live output. IMPORTANT: The command MUST include 'cd /path/to/dir && ...' if it needs to run in a specific directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute in the new terminal. MUST include 'cd' to the correct directory if not running from HOME (e.g., 'cd /Users/user/project && npm run dev')."}
            },
            "required": ["command"]
        }
    },
    "ask_user_for_feedback": {
        "fn": ask_user_for_feedback,
        "description": "Ask the human user a question to get clarification, confirmation, or additional input needed to proceed. Use sparingly.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The question to ask the user."}
            },
            "required": ["question"]
        }
    },
    "append_file": {
        "fn": append_file,
        "description": "Append content to the end of an existing file. Creates the file and directories if they don't exist.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path (including filename) to append to."},
                "content": {"type": "string", "description": "The text content to append."}
            },
            "required": ["path", "content"]
        }
    },
    "list_files": {
        "fn": list_files,
        "description": "List all files and directories within a specified directory, showing their type.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "The path to the directory whose contents should be listed. Defaults to current directory '.' if omitted."}
            },
            "required": []
        }
    },
    "search_in_file": {
        "fn": search_in_file,
        "description": "Search for a specific string within a file and return all lines containing the string, along with their line numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path to the file to search within."},
                "query": {"type": "string", "description": "The string pattern to search for."}
            },
            "required": ["path", "query"]
        }
    },
    "delete_file": {
        "fn": delete_file,
        "description": "Delete a single file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path to the file to be deleted."}
            },
            "required": ["path"]
        }
    },
    "create_directory": {
        "fn": create_directory,
        "description": "Create a new directory. Creates parent directories as needed if they don't exist.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "The full path of the directory to create."}
            },
            "required": ["directory"]
        }
    },
    "delete_directory": {
        "fn": delete_directory,
        "description": "Delete a directory and all its contents recursively. Use with caution! Consider using 'ask_user_for_feedback' for confirmation first.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "The path to the directory to be deleted."}
            },
            "required": ["directory"]
        }
    }
}


def generate_system_prompt(tools: Dict[str, Any]) -> str:
    """Generates the system prompt including formatted tool descriptions and handling for pathing and user feedback."""
    tool_descriptions = {}
    for name, tool_info in tools.items():
        tool_descriptions[name] = {
            "description": tool_info["description"],
            "parameters": tool_info["parameters"]
        }

    formatted_tools = json.dumps(tool_descriptions, indent=2)
    personalization_hints = "The user often works with React and Java Spring Boot, and enjoys competitive coding (Python, C++, Java)."

    return f'''
You are a highly capable AI Coding Agent with file system and terminal access, designed to work across various programming languages and frameworks. {personalization_hints} For any user request, follow this workflow meticulously:

1.  **Plan:** Briefly state your plan. Outline the steps, including the specific shell commands. Critically identify commands that start long-running processes (like web servers) and commands that need to run in specific directories. Determine if user clarification is needed.
2.  **Act:** Execute steps sequentially using *only* the available tools, one tool per action.
3.  **Observe:** After each action, you receive the tool's output (or user response).
4.  **Analyze & Iterate:** Carefully analyze the observation. Check for errors, extract needed information (like paths from `pwd`). If unsure or before destructive actions, consider using `ask_user_for_feedback`. Adjust plan if needed.
5.  **Output:** Once the request is fully addressed, provide the final result/confirmation. If a server was started, mention how to access it.

**KEY RULES & TOOL USAGE:**
*   **Language Agnostic:** Infer and use correct shell commands for the requested language/task.
*   **`run_command`:** Use for commands that **finish** (compile, install, test, format, `pwd`, one-off scripts). Runs in the agent's *current* directory. Analyze its exit code, stdout, stderr.
*   **`run_in_new_terminal` (macOS):** Use *only* for **long-running foreground processes** (dev servers like `npm run dev`, watchers).
    *   **PATHING IS CRITICAL:** This tool opens a *new* terminal which starts in the **HOME** directory.
    *   **If the command must run in a specific project directory:**
        1.  First, use `run_command` with `pwd` to get the agent's current absolute path.
        2.  Analyze the `pwd` output.
        3.  Construct the `run_in_new_terminal` command string to explicitly `cd` to the target directory before running the actual command. Example: `cd /Users/me/projects/my-app && npm run dev`.
    *   Assume launch succeeded if no *immediate* tool error occurs. The agent won't get further output from this separate terminal.
    *   After launching, usually proceed directly to the final "output" step.
*   **`ask_user_for_feedback`:** Use this tool **sparingly** when you genuinely need clarification, confirmation (e.g., before `delete_directory`), or input from the user that wasn't in the original request. Frame clear, concise questions. The tool pauses execution until the user responds.
*   **File Paths:** Be precise with relative and absolute paths. Use `pwd` if unsure about the current location before constructing paths.
*   **JSON Output:** Adhere strictly to the specified JSON format for *every* response.
*   **Error Handling:** Check `run_command` output. Diagnose errors and try to fix them (e.g., install missing dependencies, correct syntax).
*   **Final Output:** Use the "output" step only when the *entire* request is fulfilled.

**AVAILABLE TOOLS:**
{formatted_tools}

**OUTPUT JSON FORMAT:**
{{
  "step": "string",  // Must be one of: "plan", "action", "observe", "output"
  "content": "string",  // Plan description, analysis, reasoning, or final user message.
  "function": "string",  // Tool name. Required only for step="action".
  "input": {{}}      // Tool parameters object. Required only for step="action".
}}

**STEP DESCRIPTIONS:**
*   `plan`: Outline strategy, commands, path considerations, potential user questions.
*   `action`: Specify the *single* tool call (`run_command`, `run_in_new_terminal`, `ask_user_for_feedback`, file ops, etc.).
*   `observe`: (Input from System) Provides the result/output from the executed tool or user response.
*   `output`: Present the final response/result to the user.

**EXAMPLE 1: React Dev Server (Handling Path)**

User: "Create a react app using vite in 'my-vite-app' and start the dev server."

[Agent Response 1]
{{
  "step": "plan",
  "content": "1. Create React app 'my-vite-app' using `npm create vite@latest`. 2. Install dependencies via `npm install` in the new directory. 3. Get current path using `pwd`. 4. Start dev server using `npm run dev` in the new directory via `run_in_new_terminal`, constructing the command with the path from `pwd`."
}}
[Agent Response 2]
{{
  "step": "action",
  "function": "run_command",
  "input": {{"command": "npm create vite@latest my-vite-app -- --template react"}},
  "content": "Creating the Vite React app."
}}
[System Input - Observation]
{{
  "step": "observe",
  "content": "Exit Code: 0\\nSTDOUT:\\n...\\nDone. Now run:\\n  cd my-vite-app\\n  npm install\\n  npm run dev\\nSTDERR: (empty)\\n"
}}
[Agent Response 3]
{{
  "step": "action",
  "function": "run_command",
  "input": {{"command": "cd my-vite-app && npm install"}},
  "content": "Installing dependencies inside ./my-vite-app/."
}}
[System Input - Observation]
{{
  "step": "observe",
  "content": "Exit Code: 0\\nSTDOUT:\\nadded X packages...\\nSTDERR: (empty)\\n"
}}
[Agent Response 4]
{{
  "step": "action",
  "function": "run_command",
  "input": {{"command": "pwd"}},
  "content": "Getting current working directory to construct the path for the dev server command."
}}
[System Input - Observation]
{{
  "step": "observe",
  "content": "Exit Code: 0\\nSTDOUT:\\n/Users/apurba/Desktop/Gen-Ai-cohort/LearningSession\\nSTDERR: (empty)\\n"
}}
[Agent Response 5]
{{
  "step": "action",
  "function": "run_in_new_terminal",
  "input": {{"command": "cd /Users/apurba/Desktop/Gen-Ai-cohort/LearningSession/my-vite-app && npm run dev"}},
  "content": "Starting the development server in 'my-vite-app' in a new terminal window."
}}
[System Input - Observation]
{{
  "step": "observe",
  "content": "Command 'cd /Users/apurba/Desktop/Gen-Ai-cohort/LearningSession/my-vite-app && npm run dev' launched in a new Terminal window. Note: It runs independently..."
}}
[Agent Response 6]
{{
  "step": "output",
  "content": "Successfully created 'my-vite-app', installed dependencies, and started the dev server in a new window. Check the new terminal for the URL (likely http://localhost:5173)."
}}

**EXAMPLE 2: Using User Feedback**

User: "Delete the 'temp-project' directory."

[Agent Response 1]
{{
  "step": "plan",
  "content": "The user wants to delete 'temp-project'. Since this is destructive, I will first ask for confirmation using `ask_user_for_feedback`. If confirmed, I will use `delete_directory`."
}}
[Agent Response 2]
{{
  "step": "action",
  "function": "ask_user_for_feedback",
  "input": {{"question": "Are you sure you want to permanently delete the directory 'temp-project' and all its contents? (yes/no)"}},
  "content": "Asking user for confirmation before deleting directory."
}}
[System Input - Observation]
{{
  "step": "observe",
  "content": "User response to 'Are you sure you want to permanently delete the directory 'temp-project' and all its contents? (yes/no)': yes"
}}
[Agent Response 3]
{{
  "step": "plan",
  "content": "User confirmed deletion. Proceeding with `delete_directory`."
}}
[Agent Response 4]
{{
  "step": "action",
  "function": "delete_directory",
  "input": {{"directory": "temp-project"}},
  "content": "Deleting directory 'temp-project' as confirmed by user."
}}
[System Input - Observation]
{{
  "step": "observe",
  "content": "Directory 'temp-project' and its contents deleted successfully."
}}
[Agent Response 5]
{{
  "step": "output",
  "content": "Directory 'temp-project' has been deleted."
}}
'''


class CodingAgent:
    def __init__(self, model: str = AGENT_MODEL, tools: Dict[str, Any] = AVAILABLE_TOOLS):
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY environment variable not set.")

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
        self.model = model
        self.tools = tools
        # Ensure the __init__ method calls the updated prompt generator
        self.system_prompt = generate_system_prompt(tools)
        self.messages: List[Dict[str, str]] = [{"role": "system", "content": self.system_prompt}]
        self.max_iterations = 25 # Increased slightly for potential user feedback loops

    def _call_llm(self) -> Optional[Dict[str, Any]]:
        """Calls the LLM, handles potential errors, and parses JSON response."""
        print(f"\n[DEBUG] Sending {len(self.messages)} messages to LLM (model: {self.model}). Last message role: {self.messages[-1]['role']}")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                response_format={"type": "json_object"},
                temperature=0.5, # Keep temp reasonable for reliable tool use
                # max_tokens=1500 # Adjust if needed, but response_format helps
            )
            response_content = response.choices[0].message.content
            if not response_content:
                 print("[ERROR] LLM returned empty content.")
                 error_msg = {"role": "assistant", "content": json.dumps({"step": "observe", "content": "Error: LLM returned empty content. Please try again."})}
                 self.messages.append(error_msg)
                 # Return an observation step so the agent loop can continue and potentially recover
                 return {"step": "observe", "content": "Error: LLM returned empty content."}

            try:
            
                json_start = response_content.find('{')
                json_end = response_content.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    potential_json = response_content[json_start:json_end]
                    parsed_output = json.loads(potential_json)
                else:
                    raise json.JSONDecodeError("No JSON object found", response_content, 0)

                # Basic validation
                if "step" not in parsed_output:
                     raise ValueError("Missing 'step' key in LLM response.")
                if parsed_output["step"] == "action" and ("function" not in parsed_output or "input" not in parsed_output):
                     raise ValueError("Malformed 'action' step: missing 'function' or 'input'.")

                # Add the *original* (potentially slightly messy) response content to history
                # This lets the LLM see if it included extra text it shouldn't have
                self.messages.append({"role": "assistant", "content": response_content})
                return parsed_output
            except (json.JSONDecodeError, ValueError) as e:
                print(f"[ERROR] Failed to parse or validate LLM JSON response: {e}\nResponse: {response_content}")
                error_msg_content = f"Error: Invalid JSON response received: ```{response_content}```. Please provide output *strictly* in the required JSON format with all necessary keys ({e}). Only output the JSON object itself, nothing else."
                error_msg = {"role": "assistant", "content": json.dumps({"step": "observe", "content": error_msg_content})}
                self.messages.append(error_msg)
                return {"step": "observe", "content": "Error: Invalid JSON response received from LLM."}

        except APIError as e:
            print(f"[ERROR] API Error: {e}")
            error_msg_content = f"Error: API Error encountered: {e}. The request may need to be retried or modified."
            error_msg = {"role": "assistant", "content": json.dumps({"step": "observe", "content": error_msg_content})}
            self.messages.append(error_msg)
            return {"step": "observe", "content": f"Error: API Error: {e}"}
        except Exception as e:
            print(f"[ERROR] Unexpected error during LLM call: {e}")
            error_msg_content = f"Error: An unexpected issue occurred: {e}. Please analyze the situation."
            error_msg = {"role": "assistant", "content": json.dumps({"step": "observe", "content": error_msg_content})}
            self.messages.append(error_msg)
            return {"step": "observe", "content": f"Error: Unexpected error: {e}"}


    def _execute_tool(self, function_name: str, function_input: Dict[str, Any]) -> str:
        """Executes the specified tool function safely."""
        print(f"\n[TOOL] Calling: {function_name} with params: {json.dumps(function_input)}")
        if function_name in self.tools:
            tool_info = self.tools[function_name]
            tool_function = tool_info["fn"]
            try:
                # Parameter validation
                required_params = tool_info["parameters"].get("required", [])
                for param in required_params:
                    if param not in function_input:
                        return f"Error: Missing required parameter '{param}' for tool '{function_name}'."

                # Type validation (basic example)
                properties = tool_info["parameters"].get("properties", {})
                for param_name, param_data in properties.items():
                    if param_name in function_input:
                        expected_type = param_data.get("type")
                        actual_value = function_input[param_name]
                        if expected_type == "string" and not isinstance(actual_value, str):
                            return f"Error: Invalid type for parameter '{param_name}'. Expected string, got {type(actual_value).__name__}."
                        # Add more types (integer, boolean, object, array) if needed

                output = tool_function(function_input)
                print(f"[TOOL OUTPUT]\n{output}")
                # Limit output length before adding observation
                max_tool_output_length = 5000
                if len(output) > max_tool_output_length:
                    output = output[:max_tool_output_length] + "\n... (tool output truncated)"
                return output
            except Exception as e:
                error_message = f"Error executing tool '{function_name}': {e}"
                print(f"[TOOL ERROR] {error_message}")
                # Add traceback potentially? Be careful with length.
                # import traceback
                # error_message += f"\n{traceback.format_exc()}"
                return error_message
        else:
            error_message = f"Error: Tool '{function_name}' not found."
            print(f"[TOOL ERROR] {error_message}")
            return error_message

    def run_interaction(self, user_query: str):
        """Runs a full interaction cycle for a given user query."""
        print(f"\n[USER QUERY] {user_query}")
        # Reset message history *except* for the system prompt for a new query
        self.messages = [self.messages[0]] # Keep only system prompt
        self.messages.append({"role": "user", "content": user_query})

        iteration_count = 0
        while iteration_count < self.max_iterations:
            iteration_count += 1
            print(f"\n--- Iteration {iteration_count}/{self.max_iterations} ---")

            parsed_output = self._call_llm()

            # Handle case where LLM call failed critically or returned an observation directly
            if not parsed_output or parsed_output.get("step") == "observe":
                # If it was an error observation generated by _call_llm, print it
                if parsed_output and "content" in parsed_output:
                    print(f"[LLM/SYSTEM ERROR] {parsed_output['content']}")
                else:
                     print("[AGENT] Failed to get valid action/plan/output from LLM. Aborting interaction.")
                     self.messages.append({"role": "assistant", "content": json.dumps({"step":"output", "content":"Agent failed to get a valid response from the language model."})})
                     break # Exit if LLM call fails critically
                # If it was just an observation, let the loop continue so LLM can act on it
                if parsed_output and parsed_output.get("step") == "observe":
                    print("[ANALYSIS/OBSERVE] LLM provided an observation step. Waiting for next action.")
                    continue
                else: # If it was a critical failure from _call_llm
                    break


            step = parsed_output.get("step")
            content = parsed_output.get("content", "")

            print(f"[LLM RESPONSE] Step: {step}")

            if step == "plan":
                print(f"[PLAN] {content}")
                # Continue loop: LLM will provide action next
                continue

            elif step == "action":
                function_name = parsed_output.get("function")
                function_input = parsed_output.get("input")
                action_content = parsed_output.get("content", "") # Optional reasoning/commentary

                if action_content:
                     print(f"             Action Rationale: {action_content}")

                if not function_name or function_input is None:
                    print("[ERROR] LLM action step missing 'function' or 'input'. Informing LLM.")
                    obs_content = "Error: Your previous 'action' step was malformed (missing 'function' or 'input'). Please provide a valid action step with both fields in the correct JSON format."
                    # Send back as an observation for LLM to correct itself
                    self.messages.append({"role": "assistant", "content": json.dumps({"step": "observe", "content": obs_content})})
                    continue # Let LLM retry

                # Execute the tool
                tool_output = self._execute_tool(function_name, function_input)

                # Add the observation message for the LLM's next turn
                observation_message = {"role": "assistant", "content": json.dumps({"step": "observe", "content": tool_output})}
                self.messages.append(observation_message)
                print(f"[OBSERVATION ADDED] (Content length: {len(tool_output)})")
                # Continue loop: LLM will process the observation next

            # elif step == "observe": # Handled implicitly above - if _call_llm returns observe, we just loop
            #     print(f"[ANALYSIS/OBSERVE] {content}")
            #     continue

            elif step == "output":
                print(f"\n[FINAL OUTPUT]\n{content}")
                # Interaction complete
                break

            else:
                print(f"[ERROR] Unknown step type '{step}' received from LLM. Informing LLM.")
                obs_content = f"Error: You provided an unknown step type '{step}'. Allowed steps are 'plan', 'action', 'output'. Please respond with a valid step in the correct JSON format."
                self.messages.append({"role": "assistant", "content": json.dumps({"step": "observe", "content": obs_content})})
                continue # Let LLM try to recover

        if iteration_count >= self.max_iterations:
            print("\n[AGENT] Reached maximum iterations. Aborting interaction.")
            timeout_message_content = f"Reached maximum iterations ({self.max_iterations}). The task may be incomplete. Please review the steps or refine the request."
            timeout_message = {"role": "assistant", "content": json.dumps({"step":"output", "content": timeout_message_content})}
            # Avoid double output if the last step was already output
            last_msg = {}
            try:
                if self.messages[-1].get("role") == "assistant":
                    last_msg = json.loads(self.messages[-1].get("content", "{}"))
            except json.JSONDecodeError:
                pass # Ignore malformed last message

            if last_msg.get("step") != "output":
                 self.messages.append(timeout_message)
                 print(f"\n[FINAL OUTPUT]\n{timeout_message_content}")


# --- Main Execution ---
if __name__ == "__main__":
    print("Initializing AI Coding Agent...")
    # Ensure environment variable is loaded before initializing agent
    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY environment variable not set. Please set it in a .env file or export it.")
        exit(1)
    try:
        agent = CodingAgent()
        print(f"System Prompt Length: {len(agent.system_prompt)} characters")
        print("Agent Ready. Type 'exit' or 'quit' to quit.")
    except ValueError as e:
        print(f"Error initializing agent: {e}")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during initialization: {e}")
        exit(1)


    while True:
        try:
            user_query = input("\nUser>> ")
            if user_query.lower() in ['exit', 'quit']:
                break
            if not user_query.strip():
                continue

            # Start a new interaction cycle for the query
            agent.run_interaction(user_query)
            print("\n[AGENT] Interaction complete or max iterations reached. Ready for next query.")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except EOFError:
            print("\nInput stream closed. Exiting...")
            break
        except Exception as e:
            print(f"\n[FATAL ERROR] An unexpected error occurred in the main loop: {e}")
            # import traceback
            # print(traceback.format_exc()) # Uncomment for full traceback
            break
