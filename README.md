# BabyAGI — LLM-Based Autonomous Task Agent

A student-friendly Python project inspired by the classic BabyAGI task loop. It includes an LLM chatbot and a bounded task agent that performs:

**Task Execution → Task Creation → Task Prioritization**

## Features

- Chat interface that answers questions using an LLM API.
- Converts a user objective into smaller tasks.
- Executes tasks and stores their results in session memory.
- Creates relevant follow-up tasks.
- Reprioritizes pending tasks.
- Configurable maximum number of iterations to help control API usage.
- Streamlit web interface.

## Important scope note

This is an educational BabyAGI-inspired implementation, not the complete original BabyAGI repository. It uses in-session text memory rather than a vector database. It does not browse the web, run generated code, or perform external actions. LLM outputs may be incorrect, so verify important information.

## Requirements

- Python 3.10 or newer
- VS Code
- An API key for a model provider compatible with the OpenAI Python SDK
- Internet connection for API requests

API usage may incur charges according to your provider's pricing. Keep the iteration limit low while testing.

## Setup in VS Code

### 1. Open the project

Extract the ZIP file, open VS Code, and choose **File → Open Folder**. Select the `babyagi_tae2_project` folder.

### 2. Create a virtual environment

Open **Terminal → New Terminal** in VS Code.

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, either run this command for the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Or use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure your API key

In VS Code, create a copy of `.env.example` named `.env`.

The project folder should contain both `.env.example` and `.env`. Edit `.env`:

```dotenv
OPENAI_API_KEY=your_real_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

Use a real API key from your provider. Do not include quotes unless your key format requires them. Never commit `.env` to GitHub. The `.gitignore` file excludes it.

### 5. Run the application

```bash
streamlit run app.py
```

Streamlit will show a local URL, normally `http://localhost:8501`. Open it in your browser.

## How to use the application

### Chatbot

1. Open **Ask the LLM**.
2. Enter a question in the chat input at the bottom.
3. Read the model's response.

### BabyAGI agent

1. Open **Run BabyAGI**.
2. Enter an objective, for example: `Create a 7-day study plan for learning the basics of large language models.`
3. Set the maximum iterations in the sidebar (start with 2 or 3).
4. Click **Run BabyAGI**.
5. Review the activity log, completed task results, and any remaining tasks.

## Project structure

```text
babyagi_tae2_project/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## How the agent works

1. **Task creation:** the LLM breaks the objective into an initial list.
2. **Prioritization:** the LLM orders the pending task queue.
3. **Execution:** the LLM produces a result for the highest-priority task.
4. **Memory:** the result is saved and recent results are passed as context to later tasks.
5. **Follow-up task creation:** the LLM may suggest new tasks based on the result.
6. **Stop condition:** the agent stops when no tasks remain or the iteration limit is reached.

## Troubleshooting

- **`OPENAI_API_KEY is missing`:** check that `.env` exists in the same folder as `app.py` and contains the key.
- **Authentication error:** confirm the key is valid and belongs to a provider account with API access.
- **Model not found / unavailable:** change `OPENAI_MODEL` to a model available to your account, or change the model field in the sidebar.
- **`streamlit` is not recognized:** activate the virtual environment and run `python -m pip install -r requirements.txt`.
- **Port already in use:** run `streamlit run app.py --server.port 8502`.
- **API rate limit or quota error:** wait, check provider quota/billing, and lower the iteration count.
- **PowerShell activation error:** use the process-scoped policy command above or activate through Command Prompt.

## Upload to GitHub

### 1. Create a repository

1. Sign in to GitHub.
2. Click **New repository**.
3. Name it `babyagi-tae2`.
4. Choose Public or Private according to your instructor's requirements.
5. Do not initialize it with a README if you plan to push this existing project as-is.
6. Create the repository and copy its HTTPS URL.

### 2. Initialize Git and push

Run these commands in the VS Code terminal from the project folder. Replace the URL with your own repository URL:

```bash
git init
git add .
git status
git commit -m "Initial commit: BabyAGI TAE-2 project"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/babyagi-tae2.git
git push -u origin main
```

If Git asks you to identify yourself first:

```bash
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

GitHub may ask you to sign in through a browser or credential manager. Follow the authentication prompt; do not paste an API key into Git commands.

### 3. Confirm the upload

Refresh your GitHub repository page. Confirm that `app.py`, `requirements.txt`, `.env.example`, `.gitignore`, and `README.md` are visible.

### If `remote origin already exists`

```bash
git remote -v
git remote set-url origin https://github.com/YOUR-USERNAME/babyagi-tae2.git
git push -u origin main
```

### If the push is rejected because the remote has a README

If you created a README on GitHub and also have local commits, first inspect the repository state. One common resolution is:

```bash
git pull --rebase origin main
git push -u origin main
```

Resolve any reported merge conflicts before pushing.

## Suggested demonstration for evaluation

1. Start the app and show the direct LLM chatbot.
2. Enter a study-planning or research objective in the BabyAGI tab.
3. Show the initial tasks, task execution results, and activity log.
4. Explain how the agent creates follow-up tasks and prioritizes the queue.
5. Show the README and GitHub repository.

## References

- Original BabyAGI repository: https://github.com/yoheinakajima/babyagi
- Streamlit documentation: https://docs.streamlit.io/
- OpenAI API documentation: https://platform.openai.com/docs/
