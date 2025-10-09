#!/usr/bin/env python3
"""
Cross-platform TypeScript client generator for LangPlug.

This script replaces the duplicate .sh and .bat scripts with a unified
Python solution that works on Windows, macOS, and Linux.

The script:
1. Exports OpenAPI specification from the running FastAPI backend
2. Generates TypeScript client using npm run generate-client
3. Validates the generated client
"""

import os
import subprocess
import sys
import json
import platform
from pathlib import Path
from typing import Optional


class TypeScriptClientGenerator:
    """Cross-platform TypeScript client generator."""

    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.backend_dir = self.root_dir / "Backend"
        self.frontend_dir = self.root_dir / "Frontend"
        self.openapi_spec_path = self.root_dir / "openapi_spec.json"

    def generate_client(self) -> bool:
        """
        Generate TypeScript client from OpenAPI specification.

        Returns:
            True if generation succeeds, False otherwise
        """
        print("🔧 TypeScript Client Generator")
        print("=" * 50)
        print(f"Platform: {platform.system()}")
        print(f"Root directory: {self.root_dir}")

        try:
            # Step 1: Export OpenAPI specification
            if not self._export_openapi_spec():
                return False

            # Step 2: Generate TypeScript client
            if not self._generate_typescript_client():
                return False

            # Step 3: Validate generated client
            if not self._validate_generated_client():
                return False

            print("\n✅ TypeScript client generation completed successfully!")
            return True

        except KeyboardInterrupt:
            print("\n⚠️  Generation interrupted by user")
            return False
        except Exception as e:
            print(f"❌ Error during client generation: {e}")
            return False

    def _export_openapi_spec(self) -> bool:
        """Export OpenAPI specification from FastAPI backend."""
        print("\n📋 Exporting OpenAPI specification...")

        # Change to backend directory
        os.chdir(self.backend_dir)

        # Find Python executable in virtual environment
        python_exe = self._find_python_executable()
        if not python_exe:
            print("❌ Could not find Python executable in virtual environment")
            return False

        # Python code to export OpenAPI spec
        export_code = """
from core.app import create_app
import json

app = create_app()
spec = app.openapi()

with open("../openapi_spec.json", "w") as f:
    json.dump(spec, f, indent=2)

print("OpenAPI spec exported successfully")
"""

        try:
            result = subprocess.run(
                [python_exe, "-c", export_code],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                print("❌ Failed to export OpenAPI spec:")
                print(result.stderr)
                return False

            # Verify the file was created
            if not self.openapi_spec_path.exists():
                print("❌ OpenAPI spec file was not created")
                return False

            # Verify it's valid JSON
            try:
                with open(self.openapi_spec_path) as f:
                    spec = json.load(f)
                print(
                    f"✅ OpenAPI spec exported ({len(spec.get('paths', {}))} endpoints)"
                )
                return True
            except json.JSONDecodeError:
                print("❌ Generated OpenAPI spec is not valid JSON")
                return False

        except Exception as e:
            print(f"❌ Error exporting OpenAPI spec: {e}")
            return False

    def _generate_typescript_client(self) -> bool:
        """Generate TypeScript client using npm."""
        print("\n🔨 Generating TypeScript client...")

        # Change to frontend directory
        os.chdir(self.frontend_dir)

        # Check if package.json exists
        if not (self.frontend_dir / "package.json").exists():
            print("❌ package.json not found in Frontend directory")
            return False

        # Run npm run generate-client
        try:
            result = subprocess.run(
                ["npm", "run", "generate-client"],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                print("❌ Failed to generate TypeScript client:")
                print(result.stderr)
                # Also print stdout as it might contain useful info
                if result.stdout:
                    print("Output:", result.stdout)
                return False

            print("✅ TypeScript client generated successfully")
            return True

        except FileNotFoundError:
            print("❌ npm not found. Please install Node.js and npm.")
            return False
        except Exception as e:
            print(f"❌ Error generating TypeScript client: {e}")
            return False

    def _validate_generated_client(self) -> bool:
        """Validate that the generated client looks correct."""
        print("\n✅ Validating generated client...")

        # Look for common generated files
        generated_files = ["src/api/generated", "src/generated", "generated"]

        found_generated = False
        for potential_path in generated_files:
            full_path = self.frontend_dir / potential_path
            if full_path.exists():
                print(f"✅ Found generated files at: {potential_path}")
                found_generated = True
                break

        if not found_generated:
            print("⚠️  Could not locate generated client files")
            print("   This might be normal depending on your configuration")

        return True

    def _find_python_executable(self) -> Optional[str]:
        """Find the Python executable in the virtual environment."""
        # Common virtual environment paths
        venv_paths = [
            "api_venv/Scripts/python.exe",  # Windows
            "api_venv/bin/python",  # Unix
            "venv/Scripts/python.exe",  # Windows
            "venv/bin/python",  # Unix
            ".venv/Scripts/python.exe",  # Windows
            ".venv/bin/python",  # Unix
        ]

        for venv_path in venv_paths:
            full_path = self.backend_dir / venv_path
            if full_path.exists():
                return str(full_path)

        # Fall back to system Python
        return sys.executable

    def clean_generated_files(self) -> bool:
        """Clean up generated files."""
        print("🧹 Cleaning up generated files...")

        files_to_clean = [
            self.openapi_spec_path,
        ]

        cleaned_count = 0
        for file_path in files_to_clean:
            if file_path.exists():
                try:
                    file_path.unlink()
                    print(f"   Removed: {file_path.name}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"   Failed to remove {file_path.name}: {e}")

        print(f"✅ Cleaned up {cleaned_count} files")
        return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Cross-platform TypeScript client generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/generate_typescript_client.py           # Generate client
  python scripts/generate_typescript_client.py --clean   # Clean generated files
        """,
    )

    parser.add_argument(
        "--clean", "-c", action="store_true", help="Clean up generated files"
    )

    args = parser.parse_args()

    generator = TypeScriptClientGenerator()

    if args.clean:
        success = generator.clean_generated_files()
    else:
        success = generator.generate_client()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
