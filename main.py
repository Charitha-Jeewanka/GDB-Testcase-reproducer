import os
import sys
import time
import subprocess
from utils.config_loader import load_config
from utils.gdb_wrapper import GDBController
from agents.investigator import InvestigatorAgent
from agents.judge import JudgeAgent
from agents.reporter import ReporterAgent

def main():
    # 1. Load Configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    # 2. Setup Paths
    # Ensure MSYS2 bin is in PATH for GCC/GDB dependencies
    gcc_path = config.get("gcc_path")
    if gcc_path:
        bin_dir = os.path.dirname(gcc_path)
        if bin_dir not in os.environ["PATH"]:
             os.environ["PATH"] = bin_dir + os.pathsep + os.environ["PATH"]
             print(f"Added {bin_dir} to PATH")

    # For PoC, we expect the executable to be 'linked_crash.exe' in 'C Files' or root.
    # We will assume it's compiled.
    exe_path = os.path.abspath("linked_crash.exe")
    if not os.path.exists(exe_path):
        # transform C Files/linked_crash.c to .exe
        c_source = os.path.abspath(os.path.join("C Files", "linked_crash.c"))
        if os.path.exists(c_source):
             print(f"Compiling {c_source}...")
             gcc = config.get("gcc_path", "gcc")
             try:
                 subprocess.run([gcc, "-g", c_source, "-o", "linked_crash.exe"], check=True)
             except subprocess.CalledProcessError:
                 print("Compilation failed.")
                 return
             except FileNotFoundError:
                 print(f"GCC not found at {gcc}")
                 return
        else:
             print("Error: linked_crash.exe not found and C Files/linked_crash.c not found.")
             return

    print(f"Target: {exe_path}")

    # 3. Initialize Components
    gdb = GDBController(gdb_path=config.get("gdb_path", "gdb"), timeout=config["timeouts"]["gdb_command"])
    investigator = InvestigatorAgent(model_name=config["model"]["name"])
    judge = JudgeAgent(model_name=config["model"]["name"])
    reporter = ReporterAgent(model_name=config["model"]["name"])

    try:
        # 4. Start GDB
        print("Starting GDB...")
        gdb.start(exe_path)
        
        # 5. Run to crash
        print("Running program...")
        output = gdb.run_command("run")
        print(f"Initial Output:\n{output}")
        
        # Get basic context
        bt = gdb.run_command("bt full")
        initial_context = output + "\n" + bt
        print(f"Backtrace:\n{bt}")

        # 6. Agent Loop (Simplified: Linear A -> B -> C)
        
        # --- Investigator ---
        print("\n--- Investigator Agent ---")
        gdb_commands_str = investigator.analyze(initial_context)
        print("Suggested Commands:")
        print(gdb_commands_str)
        
        # Execute commands
        print("\nExecuting Investigator's commands...")
        gdb_log = f"Context:\n{initial_context}\n\nSession:\n"
        
        commands = [line.strip() for line in gdb_commands_str.split('\n') if line.strip()]
        for cmd in commands:
            # Basic validation to prevent harmful commands if needed
            print(f"> {cmd}")
            cmd_out = gdb.run_command(cmd)
            gdb_log += f"(gdb) {cmd}\n{cmd_out}\n"
            print(cmd_out)

        # --- Judge ---
        print("\n--- Judge Agent ---")
        judge_report = judge.evaluate(gdb_log)
        print("Judge's Report:")
        print(judge_report)

        # --- Reporter ---
        # Only proceed if SOLVED (or for PoC, just proceed)
        if "SOLVED" in judge_report or "Root Cause" in judge_report:
            print("\n--- Reporter Agent ---")
            reproducer_code = reporter.generate_report(judge_report)
            
            with open("reproducer_output.c", "w") as f:
                f.write(reproducer_code)
                
            print("\nReproducer written to 'reproducer_output.c'")
        else:
            print("\nJudge marked as INCONCLUSIVE. Stopping.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        gdb.stop()
        print("GDB Stopped.")

if __name__ == "__main__":
    main()
