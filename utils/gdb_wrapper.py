import subprocess
import time
import threading
import queue

class GDBController:
    def __init__(self, gdb_path="gdb", timeout=2):
        self.gdb_path = gdb_path
        self.timeout = timeout
        self.process = None
        self.output_queue = queue.Queue()
        self.stop_event = threading.Event()

    def start(self, executable_path):
        """Starts the GDB process."""
        cmd = [self.gdb_path, "--interpreter=mi2", executable_path] # Use MI2 interface for better parsing if needed, but for now we interact via stdin/stdout text
        # Actually, for this PoC, we will stick to plain text interaction as implied by "Raw GDB logs". 
        # Using --interpreter=mi2 is robust but harder to parse for the LLM if it expects human readable.
        # Let's check prompt: "Input: Raw GDB logs". "Output: gdb commands".
        # Standard GDB output is better for LLM.
        
        cmd = [self.gdb_path, "--quiet", "--nx", executable_path]

        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1  # Line buffered
        )
        
        self.reader_thread = threading.Thread(target=self._read_output)
        self.reader_thread.daemon = True
        self.reader_thread.start()
        
        # Consume initial output
        self._get_output_until_prompt()

    def stop(self):
        """Stops the GDB process."""
        self.stop_event.set()
        if self.process:
            self.process.terminate()
            self.process.wait()

    def _read_output(self):
        """Reads output from GDB stdout/stderr and puts it in a queue."""
        if not self.process or not self.process.stdout:
            return

        while not self.stop_event.is_set() and self.process.poll() is None:
            char = self.process.stdout.read(1)
            if char:
                self.output_queue.put(char)
            else:
                time.sleep(0.01)

    def _get_output_until_prompt(self, timeout=None):
        """Reads from the queue until '(gdb) ' prompt or timeout."""
        if timeout is None:
            timeout = self.timeout
            
        buffer = []
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            try:
                char = self.output_queue.get(timeout=0.1)
                buffer.append(char)
                current_output = "".join(buffer)
                if current_output.endswith("(gdb) \n") or current_output.endswith("(gdb) "): # Check for prompt
                    return current_output
            except queue.Empty:
                continue
                
        return "".join(buffer) # Return whatever we have on timeout

    def run_command(self, command, timeout=None):
        """Runs a GDB command and returns the output."""
        if not self.process:
            raise RuntimeError("GDB process not started.")
            
        # Clear queue just in case
        while not self.output_queue.empty():
             self.output_queue.get()

        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()
        
        return self._get_output_until_prompt(timeout)

if __name__ == "__main__":
    # Test
    pass
