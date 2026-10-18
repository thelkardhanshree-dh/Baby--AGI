import json
import urllib.error
import urllib.request
from typing import Any

import streamlit as st

APP_TITLE = "BabyAGI Task Agent"
DEFAULT_MODEL = "llama3.2:1b"
OLLAMA_URL = "http://localhost:11434/api/chat"


def llm_text(model: str, system_prompt: str, user_prompt: str) -> str:
    """Send a prompt to the Ollama server running locally."""
    payload = {
        "model": model.strip() or DEFAULT_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "options": {"temperature": 0.3},
    }
    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Could not connect to Ollama at http://localhost:11434. "
            "Make sure Ollama is installed and running, then try again."
        ) from exc
    content = data.get("message", {}).get("content", "")
    if not content.strip():
        raise RuntimeError("Ollama returned an empty response. Try again.")
    return content.strip()


def parse_json_array(text: str) -> list[Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.rstrip().endswith("```"):
            cleaned = cleaned.rstrip()[:-3]
    start, end = cleaned.find("["), cleaned.rfind("]")
    if start < 0 or end < start:
        return []
    try:
        value = json.loads(cleaned[start:end + 1])
        return value if isinstance(value, list) else []
    except json.JSONDecodeError:
        return []


def normalize_tasks(items: list[Any], limit: int = 5) -> list[dict]:
    tasks = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        if not title:
            continue
        try:
            priority = int(item.get("priority", 3))
        except (TypeError, ValueError):
            priority = 3
        tasks.append({"title": title, "priority": max(1, min(5, priority))})
        if len(tasks) >= limit:
            break
    return tasks


def create_initial_tasks(model: str, objective: str) -> list[dict]:
    prompt = f"""
Break this objective into 3 to 5 small, actionable tasks.
Objective: {objective}
Return ONLY a JSON array of objects. Each object must have:
"title" (short task description) and "priority" (integer from 1 to 5; 1 is highest).
Do not include unsafe actions, private account access, or claims of real-world actions.
"""
    raw = llm_text(
        model, "You are BabyAGI's task creation agent. Return valid JSON only.", prompt
    )
    return normalize_tasks(parse_json_array(raw), 5)


def execute_task(model: str, objective: str, task_title: str, memory: list[dict]) -> str:
    memory_text = "\n".join(
        f"- Task: {entry['task']}\n  Result: {entry['result'][:900]}"
        for entry in memory[-5:]
    ) or "No completed tasks yet."
    prompt = f"""
Overall objective: {objective}
Current task: {task_title}
Previous task results (use only when relevant):
{memory_text}

Complete the current task with a useful, clear result. State assumptions when needed.
Do not claim you browsed the web, ran code, or performed an external action unless a
tool actually did so. If facts may be uncertain or time-sensitive, say so.
"""
    return llm_text(
        model, "You are BabyAGI's task execution agent. Be accurate and concise.", prompt
    )


def create_follow_up_tasks(
    model: str, objective: str, completed_task: str, result: str, pending_tasks: list[dict]
) -> list[dict]:
    pending_text = "\n".join(f"- {task['title']}" for task in pending_tasks) or "None"
    prompt = f"""
Objective: {objective}
Completed task: {completed_task}
Result:
{result[:2000]}
Already pending:
{pending_text}

Suggest 0 to 2 NEW follow-up tasks only if useful. Do not repeat completed or pending
tasks. If none are needed, return []. Return ONLY a JSON array of objects with "title"
and "priority" (1 to 5, where 1 is highest).
"""
    raw = llm_text(
        model, "You are BabyAGI's task creation agent. Return valid JSON only.", prompt
    )
    existing = {task["title"].strip().lower() for task in pending_tasks}
    existing.add(completed_task.strip().lower())
    result_tasks = []
    for task in normalize_tasks(parse_json_array(raw), 2):
        if task["title"].lower() not in existing:
            result_tasks.append(task)
            existing.add(task["title"].lower())
    return result_tasks


def prioritize_tasks(model: str, objective: str, tasks: list[dict]) -> list[dict]:
    if len(tasks) < 2:
        return tasks
    titles = [task["title"] for task in tasks]
    prompt = f"""
Objective: {objective}
Order these task titles from most important to least important.
Return ONLY a JSON array containing the exact task titles in the desired order.
Tasks: {json.dumps(titles, ensure_ascii=False)}
"""
    try:
        raw = llm_text(
            model, "You are BabyAGI's prioritization agent. Return valid JSON only.", prompt
        )
        ordered = parse_json_array(raw)
        rank = {
            title.strip().lower(): index
            for index, title in enumerate(ordered)
            if isinstance(title, str)
        }
        return sorted(
            tasks,
            key=lambda task: (rank.get(task["title"].strip().lower(), 999), task["priority"]),
        )
    except Exception:
        return sorted(tasks, key=lambda task: task["priority"])


def run_babyagi(model: str, objective: str, max_iterations: int):
    initial = create_initial_tasks(model, objective)
    if not initial:
        initial = [
            {"title": "Clarify the objective and required outcome", "priority": 1},
            {"title": "Create a practical step-by-step plan", "priority": 2},
            {"title": "Summarize recommended next actions", "priority": 3},
        ]
    pending = [
        {"id": i, "title": task["title"], "priority": task["priority"], "status": "Pending"}
        for i, task in enumerate(initial, start=1)
    ]
    memory, logs = [], []
    next_id = len(pending) + 1

    for iteration in range(1, max_iterations + 1):
        if not pending:
            logs.append("Task queue is empty. Stopping.")
            break
        pending = prioritize_tasks(model, objective, pending)
        current = pending.pop(0)
        logs.append(f"Iteration {iteration}: executing Task {current['id']} — {current['title']}")
        result = execute_task(model, objective, current["title"], memory)
        memory.append({"task": current["title"], "result": result, "task_id": current["id"]})
        followups = create_follow_up_tasks(
            model, objective, current["title"], result, pending
        )
        for task in followups:
            pending.append({
                "id": next_id, "title": task["title"],
                "priority": task["priority"], "status": "Pending",
            })
            logs.append(f"Created Task {next_id}: {task['title']}")
            next_id += 1
        pending = prioritize_tasks(model, objective, pending)

    if pending:
        logs.append(f"Stopped at the configured limit. {len(pending)} task(s) remain pending.")
    return memory, pending, logs


st.set_page_config(page_title=APP_TITLE, page_icon="🤖", layout="wide")
st.title("🤖 BabyAGI — LLM-Based Autonomous Task Agent")
st.caption("Educational BabyAGI task loop: execution → creation → prioritization.")

with st.sidebar:
    st.header("Settings")
    model = st.text_input("Ollama model", value=DEFAULT_MODEL)
    st.caption("Runs locally through Ollama. No OpenAI API key or paid API credits needed.")
    max_iterations = st.slider("Maximum task iterations", 1, 5, 2)
    st.info("Local model responses can take some time.")
    if st.button("Clear chat and task results"):
        for key in ("chat_history", "agent_runs"):
            st.session_state.pop(key, None)
        st.rerun()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "agent_runs" not in st.session_state:
    st.session_state.agent_runs = []

chat_tab, agent_tab, about_tab = st.tabs(
    ["💬 Ask the LLM", "🧠 Run BabyAGI", "ℹ️ How it works"]
)

with chat_tab:
    st.subheader("LLM Chatbot")
    st.write("Ask a question using your local Ollama model.")
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    question = st.chat_input("Ask BabyAGI's LLM a question...")
    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking with your local model..."):
                try:
                    answer = llm_text(
                        model,
                        "You are a helpful assistant for a student project about LLMs and BabyAGI. "
                        "Answer clearly and distinguish facts from uncertainty.",
                        question,
                    )
                    st.markdown(answer)
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": answer}
                    )
                except Exception as exc:
                    st.error(f"Could not get a response: {exc}")

with agent_tab:
    st.subheader("Autonomous goal execution")
    st.write(
        "Enter a goal. BabyAGI creates tasks, executes them, suggests follow-up tasks, "
        "and reprioritizes the queue."
    )
    with st.form("agent_form"):
        objective = st.text_area(
            "Your objective",
            placeholder="Example: Create a 7-day study plan for learning the basics of LLMs.",
            height=100,
        )
        run_button = st.form_submit_button("Run BabyAGI", type="primary")
    if run_button:
        if not objective.strip():
            st.warning("Please enter an objective first.")
        else:
            try:
                with st.spinner("BabyAGI is working. Local model responses may take a little time..."):
                    memory, pending, logs = run_babyagi(model, objective.strip(), max_iterations)
                st.session_state.agent_runs.insert(0, {
                    "objective": objective.strip(), "memory": memory,
                    "pending": pending, "logs": logs,
                })
                st.success("Agent run finished.")
            except Exception as exc:
                st.error(f"Agent run failed: {exc}")

    if st.session_state.agent_runs:
        run_data = st.session_state.agent_runs[0]
        st.markdown("### Latest run")
        st.markdown(f"**Objective:** {run_data['objective']}")
        st.markdown("#### Agent activity")
        for log in run_data["logs"]:
            st.write(f"• {log}")
        st.markdown("#### Completed tasks and results")
        if not run_data["memory"]:
            st.info("No tasks were completed in this run.")
        for index, entry in enumerate(run_data["memory"], start=1):
            with st.expander(f"✅ {index}. {entry['task']}", expanded=(index == 1)):
                st.write(entry["result"])
        st.markdown("#### Remaining task queue")
        if run_data["pending"]:
            for task in run_data["pending"]:
                st.write(
                    f"**Task {task['id']}** — {task['title']} "
                    f"(priority {task['priority']}, {task['status']})"
                )
        else:
            st.write("No pending tasks.")

with about_tab:
    st.subheader("Architecture")
    st.markdown(
        """
        1. **Task Creation Agent** — breaks the goal into smaller tasks and suggests follow-ups.
        2. **Task Execution Agent** — uses the local LLM to complete a task.
        3. **Task Prioritization Agent** — orders pending tasks by relevance.
        4. **Task Memory** — stores results from completed tasks for later steps.
        5. **Stop condition** — stops when the queue is empty or the iteration limit is reached.

        This educational prototype does not use a vector database, execute generated code,
        or browse the web. Always verify important answers.
        """
    )
    st.info(
        "BabyAGI is an agent orchestration approach, not a foundation model. "
        "Response quality depends on the local LLM."
    )

