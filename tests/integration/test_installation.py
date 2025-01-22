import subprocess
import sys
import venv
from pathlib import Path
from typing import Optional

import pytest


def create_virtual_env(tmp_path: Path) -> Path:
    """Create a virtual environment for testing installations."""
    venv_dir = tmp_path / "env"
    venv.create(venv_dir, with_pip=True)
    return venv_dir


def get_venv_python(venv_dir: Path) -> str:
    """Get path to Python executable in virtual environment."""
    if sys.platform == "win32":
        return str(venv_dir / "Scripts" / "python.exe")
    return str(venv_dir / "bin" / "python")


def run_in_venv(
    venv_dir: Path,
    commands: list[str],
    show_output: bool = False,
    cwd: Optional[str] = None,
) -> subprocess.CompletedProcess:
    """Run commands in virtual environment."""
    python = get_venv_python(venv_dir)

    if commands[0] == "pip":
        # For pip commands, use -m
        full_command = [python, "-m"] + commands
        if "-v" not in commands:
            full_command.append("-v")
    elif commands[0] == "python":
        # For Python script execution
        if len(commands) > 2 and commands[1] == "-m":
            # Handle python -m module_name style commands
            full_command = [python, "-m"] + commands[2:]
        else:
            # Handle direct script execution
            full_command = [python] + commands[1:]
    else:
        # For other module execution like pytest
        full_command = [python, "-m"] + commands

    print(f"Running command: {' '.join(map(str, full_command))}")
    result = subprocess.run(
        full_command,
        capture_output=True,
        text=True,
        check=True,
        cwd=cwd,  # Add this line
    )

    if show_output:
        print("\nOutput:", result.stdout)
        if result.stderr:
            print("Error:", result.stderr)
    return result


def setup_test_env(venv_dir: Path) -> None:
    """Set up test environment with our backend package."""
    backend_dir = Path(__file__).parent.parent.parent.absolute()

    # First install backend dependencies
    run_in_venv(
        venv_dir,
        [
            "pip",
            "install",
            "setuptools",
            "wheel",
            "Cython<3.0.0",
            "pyproject-metadata",
            "build",
        ],
    )

    # Install our backend package normally (not in editable mode)
    run_in_venv(venv_dir, ["pip", "install", "--no-deps", str(backend_dir)])
    run_in_venv(venv_dir, ["pip", "install", f"{backend_dir}[all]"])


@pytest.fixture
def test_env(tmp_path) -> Path:
    """Create and set up test environment."""
    venv_dir = create_virtual_env(tmp_path)
    setup_test_env(venv_dir)
    return venv_dir


@pytest.fixture
def test_package(tmp_path):
    """Create a test package with Cython code."""
    pkg_dir = tmp_path / "test_pkg"
    pkg_dir.mkdir()

    # Create package structure
    src_dir = pkg_dir / "test_pkg"
    src_dir.mkdir()

    # Create a simple Cython file
    with open(src_dir / "simple.pyx", "w") as f:
        f.write("""
def hello():
    return "Hello from Cython!"
""")
    # with open(src_dir / "simple.pxd", "w") as f:
    #     f.write("""

    # cython: language_level=3
    # cpdef str hello() except *
    # """)

    # (src_dir / "__init__.py").touch()
    with open(src_dir / "__init__.py", "w") as f:
        f.write("")
    # with open(src_dir / "__init__.pxd", "w") as f:
    #     f.write("")
    with open(pkg_dir / "README.md", "w") as f:
        f.write("# Test Package\nA simple test package with Cython extensions.")

    with open(pkg_dir / "MANIFEST.in", "w") as f:
        f.write("""
include README.md
recursive-include test_pkg *.pyx
recursive-include test_pkg *.pxd
""")

    backend_dir = Path(__file__).parent.parent.parent.absolute()

    # Create pyproject.toml with local backend reference
    with open(pkg_dir / "pyproject.toml", "w") as f:
        f.write(f"""
[build-system]
requires = [
    "setuptools",
    "wheel",
    "Cython<3.0.0",
    "hwh-backend @ file://{backend_dir}",
]
build-backend = "hwh_backend.build"

[project]
name = "test_pkg"
version = "0.1.0"
description = "A test package"
requires-python = ">=3.11"

[tool.hwh.cython]
language = "c"
""")

    return pkg_dir


def test_basic_installation(tmp_path, test_package, test_env):
    """Test basic package installation."""
    # Create a test script to verify the environment
    env_check = """
import sys
print("Python path:", sys.path)
print("\\nInstalled packages:")
import pkg_resources
for pkg in pkg_resources.working_set:
    print(f"{pkg.key} {pkg.version}")
"""
    check_script = tmp_path / "env_check.py"
    check_script.write_text(env_check)

    print("\n=== Environment before package installation ===")
    run_in_venv(test_env, ["python", str(check_script)])


def setup_base_package(pkg_dir: Path):
    """Set up a base package with Cython code."""
    pkg_dir.mkdir()
    src_dir = pkg_dir / "base_pkg"
    src_dir.mkdir()

    with open(src_dir / "core.pyx", "w") as f:
        f.write("""
def get_base_message():
    return "Message from base"
""")

    backend_dir = Path(__file__).parent.parent.parent.absolute()

    with open(pkg_dir / "pyproject.toml", "w") as f:
        f.write(f"""
[build-system]
requires = [
    "hwh-backend @ file://{backend_dir}",
    "Cython<3.0.0"
]
build-backend = "hwh_backend.build"

[project]
name = "base_pkg"
version = "0.1.0"
description = "A base package"
requires-python = ">=3.11"
""")


def test_editable_installation(tmp_path, test_package, test_env):
    """Test editable package installation."""
    try:
        run_in_venv(
            test_env, ["pip", "install", "-e", str(test_package)], show_output=True
        )
    except subprocess.CalledProcessError as e:
        print("\nEditable install failed")
        print("Output:", e.output)
        print("Error:", e.stderr)

        # Check if build backend is properly installed
        check_script = tmp_path / "check_backend.py"
        check_script.write_text("""
import sys
print("Python path:", sys.path)
try:
    from hwh_backend import build
    print("Backend found at:", build.__file__)
    print("Backend build hooks:")
    print(" - build_wheel:", hasattr(build, "build_wheel"))
    print(" - build_editable:", hasattr(build, "build_editable"))
except ImportError as e:
    print("Failed to import backend:", e)
""")
        try:
            print("\nChecking backend installation:")
            run_in_venv(test_env, ["python", str(check_script)])
        except subprocess.CalledProcessError as e2:
            print("Backend check failed:", e2)

        raise

    # Verify the editable installation worked
    check_script = tmp_path / "verify_install.py"
    check_script.write_text("""
from test_pkg.simple import hello
print(hello())
""")
    result = run_in_venv(test_env, ["python", str(check_script)])
    assert "Hello from Cython!" in result.stdout


def test_installation_with_dependencies(tmp_path, test_env):
    """Test installation with Cython dependencies."""
    # Create two packages: base and dependent
    base_pkg = tmp_path / "base_pkg"
    dependent_pkg = tmp_path / "dependent_pkg"

    setup_base_package(base_pkg)
    setup_dependent_package(dependent_pkg, base_pkg)

    # Install base package first
    run_in_venv(test_env, ["pip", "install", str(base_pkg)])

    # Then install dependent package
    run_in_venv(test_env, ["pip", "install", str(dependent_pkg)])


def setup_dependent_package(pkg_dir: Path, base_pkg: Path):
    """Set up a dependent package that uses the base package."""
    pkg_dir.mkdir()
    src_dir = pkg_dir / "dependent_pkg"
    src_dir.mkdir()

    with open(src_dir / "main.pyx", "w") as f:
        f.write("""
from base_pkg.core import get_base_message

def get_message():
    base = get_base_message()
    return f"{base} via dependent"
""")

    backend_dir = Path(__file__).parent.parent.parent.absolute()

    with open(pkg_dir / "pyproject.toml", "w") as f:
        f.write(f"""
[build-system]
requires = [
    "hwh-backend @ file://{backend_dir}",
    "Cython<3.0.0"
]
build-backend = "hwh_backend.build"

[project]
name = "dependent_pkg"
version = "0.1.0"
description = "A dependent package"
requires-python = ">=3.11"
dependencies = [
    "base_pkg @ file://{base_pkg.absolute()}"
]
""")


def test_python_build_command(tmp_path, test_package, test_env):
    """Test that python -m build works correctly for building both sdist and wheel."""
    try:
        # Install build first
        run_in_venv(
            test_env,
            ["pip", "install", "build", "setuptools", "wheel"],
            show_output=True,
        )

        # Try building with python -m build
        result = run_in_venv(
            test_env,
            ["python", "-m", "build", "--no-isolation", str(test_package)],
            show_output=True,
        )

        # Check if both sdist and wheel were created
        dist_dir = test_package / "dist"
        assert dist_dir.exists(), "dist directory was not created"

        # Should have both .tar.gz (sdist) and .whl (wheel) files
        sdist_files = list(dist_dir.glob("*.tar.gz"))
        wheel_files = list(dist_dir.glob("*.whl"))

        assert len(sdist_files) == 1, "No source distribution was built"
        assert len(wheel_files) == 1, "No wheel was built"

        # DEBUG: Inspect wheel contents
        wheel_path = wheel_files[0]
        debug_script = tmp_path / "inspect_wheel.py"
        debug_script.write_text("""
import zipfile
import sys

wheel_path = sys.argv[1]
print(f"\\nInspecting wheel: {wheel_path}")
with zipfile.ZipFile(wheel_path) as zf:
    print("\\nWheel contents:")
    for name in zf.namelist():
        print(f"  {name}")
""")
        run_in_venv(
            test_env, ["python", str(debug_script), str(wheel_path)], show_output=True
        )

        # Verify the wheel is platform specific (not pure Python)
        wheel_name = wheel_files[0].name
        assert "py3-none-any" not in wheel_name, "Wheel should be platform specific"

        # Try installing the built wheel
        run_in_venv(test_env, ["pip", "install", "-v", str(wheel_files[0])])

        # Add debug info to verify script
        check_script = tmp_path / "verify_wheel_install.py"
        check_script.write_text("""
import sys
print("Python sys.path:", sys.path)
print("\\nAttempting import...")
from test_pkg.simple import hello
print("Import successful")
val = hello()
print(f"Got value: {val}")
assert hello() == "Hello from Cython!"
""")
        run_in_venv(test_env, ["python", str(check_script)])

    except subprocess.CalledProcessError as e:
        print("\nBuild command failed")
        print("Output:", e.output)
        print("Error:", e.stderr)
        raise


def test_python_build_editable(tmp_path, test_package, test_env):
    """Test that python -m build works correctly for building in editable mode."""
    try:
        # Install build
        run_in_venv(test_env, ["pip", "install", "build", "setuptools", "wheel"])

        # Try building with python -m build --wheel
        result = run_in_venv(
            test_env,
            ["python", "-m", "build", "--no-isolation", "--wheel", str(test_package)],
        )

        # Install in editable mode
        run_in_venv(test_env, ["pip", "install", "-e", str(test_package)])

        # Verify editable install works
        check_script = tmp_path / "verify_editable_install.py"
        check_script.write_text("""
from test_pkg.simple import hello
assert hello() == "Hello from Cython!"
""")
        run_in_venv(test_env, ["python", str(check_script)])

        # Modify the source and verify changes are reflected
        (test_package / "test_pkg" / "simple.pyx").write_text("""
def hello():
    return "Modified hello from Cython!"
""")

        # Rebuild the extension
        result = run_in_venv(
            test_env,
            ["python", "-m", "build", "--no-isolation", "--wheel", str(test_package)],
        )

        # Verify changes are reflected
        check_script.write_text("""
from test_pkg.simple import hello
assert hello() == "Modified hello from Cython!"
""")
        run_in_venv(test_env, ["python", str(check_script)])

    except subprocess.CalledProcessError as e:
        print("\nBuild command failed")
        print("Output:", e.output)
        print("Error:", e.stderr)
        raise
