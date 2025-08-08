import subprocess
import os
import signal
import re

def kill_port(port):
    result = subprocess.run(f'netstat -ano | findstr :{port}', capture_output=True, text=True)
    for line in result.stdout.strip().split('\n'):
        match = re.search(r'\s+(\d+)\s*$', line)
        if match:
            pid = match.group(1)
            try:
                os.kill(int(pid), signal.SIGTERM)
                print(f"Killed process on port {port}, PID: {pid}")
            except Exception as e:
                print(f"Failed to kill PID {pid}: {e}")

kill_port(8000)

# subprocess.run([
#     "uvicorn", "backend.main:app",
#     "--reload", "--host", "127.0.0.1", "--port", "8000"
# ])
