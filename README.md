Below is the PoC (Proof of Concept) plan for a Multi-Agent Reproducer Assistant. This plan integrates the multi-agent logic, the robust GDB communication, and the Groq-based reasoning you requested.
---

## **Phase 1: Architecture & Logic Flow**

We will move away from a single linear script and use a **"State-Based" Multi-Agent** approach. This prevents hallucinations by requiring the "Judge" to verify GDB facts before the "Reporter" writes the final code.

1. **Agent A: The Investigator (Llama 3.3)**
* **Input:** Initial crash backtrace.
* **Output:** A list of specific GDB commands (e.g., `f 1`, `p *curr`, `info args`).


2. **Agent B: The Judge/Critic (Llama 3.3)**
* **Input:** Raw GDB logs from the Investigator's commands.
* **Output:** Fact-check summary. It looks for "Smoking Guns" (0x0 addresses, specific logic flags like `threshold=42`).


3. **Agent C: The Reporter (Llama 3.3)**
* **Input:** Verified facts from the Judge.
* **Output:** Reproducer Report with a standalone C reproducer.



---

## **Phase 2: Robust Technical Implementation**

To solve the **"Hanging/Freezing"** issue, the GDB communication must use a non-blocking "Expect" pattern. We will use a `timeout` and a search for the `(gdb)` prompt.

### **The "Master" Script Structure**

| Component | Implementation Detail |
| --- | --- |
| **GDB Controller** | Use `subprocess` with a 2-second per-command timeout to prevent hangs. |
| **Environment** | Native Windows (MSYS2 GDB) + Groq Cloud API. |
| **Prompt Library** | A single `SYSTEM_PROMPT` for each agent stored in a Python dictionary to avoid manual tweaking. |
| **Register Focus** | Hardcoded to **x64** (`$rax`, `$rsp`) for the current Windows PoC. |

---

## **Phase 3: The "Target" Challenge**

We will use the **`C Files\crash_test.c`** as the primary test case because it forces the AI to:

* Navigate frames (moving from `strcpy` back to `validate_and_process`).
* Understand structs (dereferencing `Node*`).
* Identify logic state (connecting the `threshold` variable to the crash).

---

## **Phase 4: PoC Success Metrics**

The PoC must meet these criteria:

1. **Zero Hallucination:** The report must correctly identify the NULL pointer, not guess a buffer overflow.
2. **Turn-Around Time (TAT):** The total execution from "Run" to "Report" should be under **30 seconds**.
3. **Actionable Output:** The C code provided in the report should compile and crash exactly like the original.

---

## Project Structure
GDB Reproducer/
├── C Files/            # Source files (Which are used to generate the crash)
├── .env                # API Keys (Groq, etc.)
├── config.yaml         # GDB paths, model names, timeouts
├── main.py             # Entry point
├── agents/             # OODPP Agent Logic
│   ├── base.py         # SOLID Base Classes
│   ├── investigator.py # Strategist Agent
│   ├── judge.py        # Critic/Verification Agent
│   └── reporter.py     # Synthesis Agent
├── utils/
│   ├── gdb_wrapper.py  # Non-blocking GDB interface
│   └── config_loader.py