# CodeGen Agent

A structured, step-by-step code generation and automation agent, designed for advanced AI-driven workflows. The agent operates in a start-plan-action-observe mode, using available tools to resolve user queries efficiently and safely.

## Features
- **Structured Workflow**: Follows a clear start → plan → action → observe → output process.
- **Tool Integration**: Supports tools for weather, system commands, and more (customizable).
- **Extensible**: Easily add new tools and capabilities.
- **Secure**: Validates steps and input before executing potentially sensitive operations.
- **Interactive**: Designed for CLI or AI assistant integration.

## Setup
1. **Clone the repo** and enter the project directory:
   ```bash
   git clone <your-repo-url>
   cd codegen-agent
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Environment Setup**:
   - Create a `.env` file with your API keys (if needed, e.g., for OpenAI/OpenRouter).

## Usage
Run the agent interactively:
```bash
python codegen-agent.py
```

You will be prompted for input. The agent will plan, select tools, act, and respond in a structured way (see code for details).

## Extending
- Add new tools by editing the `avaiable_tools` dictionary in `codegen-agent.py`.
- Adjust planning and output logic as needed for your workflow.

## License
MIT
