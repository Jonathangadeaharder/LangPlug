#!/usr/bin/env python3
"""
Cross-platform PostgreSQL test runner for LangPlug Backend.

This script replaces the duplicate .sh and .ps1 scripts with a unified
Python solution that works on Windows, macOS, and Linux.

Requirements:
- Docker and Docker Compose
- Python with pytest and test dependencies installed
"""

import os
import subprocess
import sys
import time
import platform
from pathlib import Path


class PostgreSQLTestRunner:
    """Cross-platform PostgreSQL test runner."""

    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.backend_dir = self.script_dir.parent / "Backend"
        self.compose_file = "docker-compose.postgresql.yml"

    def run_tests(self) -> bool:
        """
        Run backend tests against a local PostgreSQL instance.

        Returns:
            True if tests pass, False otherwise
        """
        print("🐘 PostgreSQL Test Runner")
        print("=" * 50)
        print(f"Platform: {platform.system()}")
        print(f"Backend directory: {self.backend_dir}")

        try:
            # Change to backend directory
            os.chdir(self.backend_dir)

            # Start PostgreSQL container
            if not self._start_postgres():
                return False

            # Wait for PostgreSQL to be ready
            if not self._wait_for_postgres():
                return False

            # Run tests
            success = self._run_pytest()

            # Print completion message
            self._print_completion_message()

            return success

        except KeyboardInterrupt:
            print("\n⚠️  Test run interrupted by user")
            return False
        except Exception as e:
            print(f"❌ Error during test execution: {e}")
            return False

    def _start_postgres(self) -> bool:
        """Start PostgreSQL Docker container."""
        print("\n🚀 Starting PostgreSQL container...")

        cmd = ["docker", "compose", "-f", self.compose_file, "up", "-d", "db"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.returncode != 0:
                print("❌ Failed to start PostgreSQL container:")
                print(result.stderr)
                return False

            print("✅ PostgreSQL container started successfully")
            return True

        except FileNotFoundError:
            print("❌ Docker not found. Please install Docker and Docker Compose.")
            return False
        except Exception as e:
            print(f"❌ Error starting PostgreSQL: {e}")
            return False

    def _wait_for_postgres(self, max_attempts: int = 30) -> bool:
        """Wait for PostgreSQL to be ready."""
        print("\n⏳ Waiting for PostgreSQL to be ready...")

        for attempt in range(max_attempts):
            try:
                # Try to connect using docker exec
                cmd = [
                    "docker",
                    "compose",
                    "-f",
                    self.compose_file,
                    "exec",
                    "-T",
                    "db",
                    "pg_isready",
                    "-U",
                    "langplug_user",
                    "-d",
                    "langplug",
                ]

                result = subprocess.run(
                    cmd, capture_output=True, text=True, check=False
                )

                if result.returncode == 0:
                    print("✅ PostgreSQL is ready!")
                    return True

            except Exception:
                pass

            print(f"   Attempt {attempt + 1}/{max_attempts}...")
            time.sleep(2)

        print("❌ PostgreSQL failed to become ready in time")
        return False

    def _run_pytest(self) -> bool:
        """Run the pytest suite."""
        print("\n🧪 Running test suite...")

        # Set environment variables
        env = os.environ.copy()
        env["USE_TEST_POSTGRES"] = "1"
        env["TEST_POSTGRES_URL"] = env.get(
            "TEST_POSTGRES_URL",
            "postgresql+asyncpg://langplug_user:langplug_password@localhost:5432/langplug",
        )

        print(f"Using TEST_POSTGRES_URL: {env['TEST_POSTGRES_URL']}")

        # Run pytest
        cmd = [sys.executable, "-m", "pytest", "-v"]

        try:
            result = subprocess.run(cmd, env=env, check=False)

            if result.returncode == 0:
                print("\n✅ All tests passed!")
                return True
            else:
                print(f"\n❌ Tests failed with return code {result.returncode}")
                return False

        except Exception as e:
            print(f"❌ Error running pytest: {e}")
            return False

    def _print_completion_message(self) -> None:
        """Print completion message with cleanup instructions."""
        print("\n" + "=" * 50)
        print("🏁 Test run completed!")
        print("\n💡 To stop PostgreSQL container:")
        print(f"   docker compose -f {self.compose_file} stop db")
        print("\n💡 To remove PostgreSQL container:")
        print(f"   docker compose -f {self.compose_file} down")

    def cleanup(self) -> bool:
        """Stop and remove PostgreSQL container."""
        print("🧹 Cleaning up PostgreSQL container...")

        os.chdir(self.backend_dir)

        cmd = ["docker", "compose", "-f", self.compose_file, "down"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.returncode == 0:
                print("✅ PostgreSQL container cleaned up successfully")
                return True
            else:
                print(f"⚠️  Cleanup completed with warnings: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Cross-platform PostgreSQL test runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_postgres_tests.py           # Run tests
  python scripts/run_postgres_tests.py --cleanup # Clean up containers
        """,
    )

    parser.add_argument(
        "--cleanup",
        "-c",
        action="store_true",
        help="Stop and remove PostgreSQL container",
    )

    args = parser.parse_args()

    runner = PostgreSQLTestRunner()

    if args.cleanup:
        success = runner.cleanup()
    else:
        success = runner.run_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
