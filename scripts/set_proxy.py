"""Utility to set proxy environment variables based on configuration.

Usage:
    eval $(python scripts/set_proxy.py 1)
"""
import sys
from pathlib import Path

# Add project root to sys.path to allow importing from scripts.core.config
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from scripts.core.config import PROXIES
except ImportError:
    print("echo 'Error: Could not import scripts.core.config'")
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("echo 'Usage: eval $(python scripts/set_proxy.py [1|2|3])'")
        sys.exit(1)
    
    try:
        idx = int(sys.argv[1])
        url = PROXIES.get(idx)
        if url:
            # Print export commands for shell evaluation
            print(f"export HTTP_PROXY='{url}'")
            print(f"export HTTPS_PROXY='{url}'")
            print(f"export http_proxy='{url}'")
            print(f"export https_proxy='{url}'")
            print(f"echo 'Proxy {idx} configured: {url}'")
        else:
            print(f"echo 'Error: Proxy {idx} not found in .env.local'")
    except ValueError:
        print("echo 'Error: Invalid proxy index. Please use 1, 2, or 3.'")

if __name__ == "__main__":
    main()
