import shutil
import subprocess
from pathlib import Path

from .test_installation import create_virtual_env, run_in_venv, setup_test_env

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "cython_interface"


def create_pyproject_toml(
    pkg_dir: Path, pkg_name: str, backend_dir: Path, dependencies: list[str] = None
) -> None:
    """Create a pyproject.toml file with the correct backend reference.
    Can't get away without because dependency and backend dirs change
    """
    content = f'''
[build-system]
requires = [
    "hwh-backend @ file://{backend_dir}",
    "Cython<3.0.0"
]
build-backend = "hwh_backend.build"

[project]
name = "{pkg_name}"
version = "0.1.0"
requires-python = ">=3.11"
'''
    if dependencies:
        content += "dependencies = [\n"
        for dep in dependencies:
            content += f'    "{dep}",\n'
        content += "]\n"

    content += """
[tool.hwh.cython]
language = "c"
compiler_directives = { language_level = "3" }
"""

    with open(pkg_dir / "pyproject.toml", "w") as f:
        f.write(content)


def copy_test_package(
    src_pkg: str, dest_dir: Path, backend_dir: Path, dependencies: list[str] = None
) -> Path:
    """Copy a test package from fixtures to a temporary directory and set up pyproject.toml."""
    src_path = FIXTURE_DIR / src_pkg
    dest_path = dest_dir / src_pkg

    # Copy the Cython source files
    shutil.copytree(src_path, dest_path)

    # Create the pyproject.toml
    create_pyproject_toml(dest_path, src_pkg, backend_dir, dependencies)

    return dest_path


def copy_scripts(src: str, dest: Path):
    src_path = FIXTURE_DIR / src
    dest_path = dest / src
    shutil.copytree(src_path, dest_path)
    return dest_path


def test_cython_interface_dependencies(tmp_path):
    """Test building and using packages with Cython interfaces."""
    # Create test environment
    venv_dir = create_virtual_env(tmp_path / "venv")
    setup_test_env(venv_dir)
    backend_dir = Path(__file__).parent.parent.parent.absolute()

    # Create packages
    base_math = copy_test_package("base_math", tmp_path, backend_dir)
    geometry = copy_test_package(
        "geometry",
        tmp_path,
        backend_dir,
        dependencies=[f"base_math @ file://{base_math.absolute()}"],
    )
    scripts = copy_scripts("scripts", tmp_path)

    try:
        # Install base package
        run_in_venv(venv_dir, ["pip", "install", "--upgrade", "pip"])
        run_in_venv(
            venv_dir,
            ["pip", "install", str(base_math)],
            show_output=True,
        )
        # assert False
        verify_script = scripts / "verify_pxd.py"
        test_script = scripts / "assert_geometry_operations.py"
        run_in_venv(venv_dir, ["python", str(verify_script)], show_output=True)
        run_in_venv(venv_dir, ["pip", "list"], show_output=True)

        # Install geometry package
        run_in_venv(
            venv_dir,
            ["pip", "install", str(geometry), "--no-build-isolation"],
            show_output=True,
        )

        # Run test script
        result = run_in_venv(venv_dir, ["python", str(test_script)])
        assert "All tests passed!" in result.stdout

    except subprocess.CalledProcessError as e:
        print("\nTest failed")
        print("Output:", e.output)
        print("Error:", e.stderr)
        raise


def test_cython_interface_regular_install(tmp_path):
    """Test regular installation of packages with Cython interfaces."""
    # Create test environment
    venv_dir = create_virtual_env(tmp_path / "venv")
    setup_test_env(venv_dir)
    backend_dir = Path(__file__).parent.parent.parent.absolute()

    # Create packages
    base_math = copy_test_package("base_math", tmp_path, backend_dir)
    geometry = copy_test_package(
        "geometry",
        tmp_path,
        backend_dir,
        dependencies=[f"base_math @ file://{base_math.absolute()}"],
    )

    scripts = copy_scripts("scripts", tmp_path)
    test_script = scripts / "assert_vector_in_geometry.py"

    run_in_venv(venv_dir, ["pip", "install", "--upgrade", "pip"])

    try:
        # Install base package
        run_in_venv(venv_dir, ["pip", "install", str(base_math)], show_output=True)

        # Install geometry with --no-build-isolation (required atm)
        run_in_venv(venv_dir, ["pip", "install", "--no-build-isolation", str(geometry)])

        # Test the installation
        run_in_venv(venv_dir, ["python", str(test_script)])

    except subprocess.CalledProcessError as e:
        print("\nTest failed")
        print("Output:", e.output)
        print("Error:", e.stderr)
        raise


def test_cython_interface_editable_install(tmp_path):
    """Test editable installation with Cython interfaces."""
    venv_dir = create_virtual_env(tmp_path / "venv")
    setup_test_env(venv_dir)
    backend_dir = Path(__file__).parent.parent.parent.absolute()

    # Create packages
    base_math = copy_test_package("base_math", tmp_path, backend_dir)
    geometry = copy_test_package(
        "geometry",
        tmp_path,
        backend_dir,
        dependencies=[f"base_math @ file://{base_math.absolute()}"],
    )
    scripts = copy_scripts("scripts", tmp_path)
    test_script = scripts / "assert_vector_in_geometry.py"
    test_script_mod = scripts / "assert_vector_in_geometry_mod.py"

    try:
        run_in_venv(venv_dir, ["pip", "install", "--upgrade", "pip"])
        # Install base_math normally (not editable)
        run_in_venv(venv_dir, ["pip", "install", str(base_math)])

        run_in_venv(venv_dir, ["pip", "install", "-e", str(geometry)], show_output=True)

        run_in_venv(venv_dir, ["python", str(test_script)])

        # Test that the thing is actually editable by modifying geometry
        shapes_pyx = geometry / "geometry" / "shapes.pyx"
        original_content = shapes_pyx.read_text()
        try:
            # Add a new method to Rectangle
            new_content = original_content.replace(
                "cpdef double area(self):",
                "cpdef double area(self):\n        return self.size.x * self.size.y * 2  # Modified!",
            )
            shapes_pyx.write_text(new_content)

            # Test the modification (we test python -m build at the same time, how convenient)
            run_in_venv(venv_dir, ["python", "-m", "build"], cwd=str(geometry))
            run_in_venv(
                venv_dir,
                ["python", str(test_script_mod)],
                show_output=True,
            )

        finally:
            # Restore original content
            shapes_pyx.write_text(original_content)

    except subprocess.CalledProcessError as e:
        print("\nTest failed")
        print("Output:", e.output)
        print("Error:", e.stderr)
        raise
