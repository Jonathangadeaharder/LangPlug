#!/usr/bin/env python3
"""
DEPRECATED: This script has been replaced by a1decider_cli_pipeline.py
Please use the new pipeline-based CLI interface instead.
"""

import os
import sys
import subprocess

def main():
    print("\n" + "="*60, file=sys.stderr)
    print("DEPRECATION NOTICE", file=sys.stderr)
    print("="*60, file=sys.stderr)
    print("This script (a1decider_cli.py) has been deprecated.", file=sys.stderr)
    print("Please use 'a1decider_cli_pipeline.py' instead.", file=sys.stderr)
    print("\nThe new script uses the ProcessingPipeline architecture", file=sys.stderr)
    print("and provides the same functionality with improved performance.", file=sys.stderr)
    print("="*60 + "\n", file=sys.stderr)
    
    # Try to run the new pipeline version with the same arguments
    new_script = os.path.join(os.path.dirname(__file__), 'a1decider_cli_pipeline.py')
    
    if os.path.exists(new_script):
        print("Automatically redirecting to a1decider_cli_pipeline.py...", file=sys.stderr)
        try:
            # Pass all arguments to the new script
            cmd = [sys.executable, new_script] + sys.argv[1:]
            result = subprocess.run(cmd, check=False)
            sys.exit(result.returncode)
        except Exception as e:
            print(f"Error running new script: {e}", file=sys.stderr)
            print("Please run 'python a1decider_cli_pipeline.py' manually.", file=sys.stderr)
            sys.exit(1)
    else:
        print("New script not found. Please run:", file=sys.stderr)
        print(f"python a1decider_cli_pipeline.py {' '.join(sys.argv[1:])}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()