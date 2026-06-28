import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SERVICES = [
    {
        "name": "web-portal",
        "cmd": [
            sys.executable,
            "-m",
            "uvicorn",
            "web_gateway.app:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8088",
        ],
    },
    {
        "name": "compliance-risk-agent",
        "cmd": [
            sys.executable,
            "-m",
            "uvicorn",
            "services.exception_agent.app:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8010",
        ],
    },
    {
        "name": "prioritization-agent",
        "cmd": [
            sys.executable,
            "-m",
            "uvicorn",
            "services.collections_agent.app:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8020",
        ],
    },
]


def main() -> int:
    procs: list[subprocess.Popen] = []
    try:
        for svc in SERVICES:
            print(f"Starting {svc['name']} on {svc['cmd'][-1]}...")
            proc = subprocess.Popen(svc["cmd"], cwd=ROOT)
            procs.append(proc)

        print("Hybrid stack is running:")
        print("- Web portal: http://127.0.0.1:8088")
        print("- Control Center: http://127.0.0.1:8088/ui/control_center.html")
        print("- Risk API: http://127.0.0.1:8010")
        print("- Prioritization API: http://127.0.0.1:8020")
        print("Press Ctrl+C to stop all.")
        while True:
            for proc in procs:
                code = proc.poll()
                if code is not None:
                    print(f"A service exited unexpectedly with code {code}. Stopping all...")
                    return code
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping services...")
        return 0
    finally:
        for proc in procs:
            if proc.poll() is None:
                proc.terminate()
        for proc in procs:
            if proc.poll() is None:
                proc.wait(timeout=10)


if __name__ == "__main__":
    raise SystemExit(main())
