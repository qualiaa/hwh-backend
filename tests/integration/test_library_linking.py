import subprocess
from pathlib import Path

import pytest

from ..utils.package_utils import create_test_package
from ..utils.venv_utils import create_virtual_env, run_in_venv, setup_test_env
from ..utils.verification_utils import verify_installation


def create_shared_lib(pkg_dir: Path) -> Path:
    """Create .so +header"""
    lib_dir = pkg_dir / "lib"
    lib_dir.mkdir(exist_ok=True)

    lib_source = lib_dir / "testlib.c"
    lib_source.write_text("""
    #include <stdio.h>
    int multiply_by_two(int x) {
        return x * 2;
    }
    """)

    header = lib_dir / "testlib.h"
    header.write_text("""
    #ifndef TESTLIB_H
    #define TESTLIB_H
    int multiply_by_two(int x);
    #endif
    """)

    subprocess.run(
        [
            "gcc",
            "-shared",
            "-fPIC",
            str(lib_source),
            "-o",
            str(lib_dir / "libtestlib.so"),
        ],
        check=True,
    )

    return lib_dir


@pytest.fixture
def linked_package(tmp_path: Path, backend_dir: Path):
    """Create a test package that links against the .so"""
    # Define Cython extension that uses the library
    cython_files = {
        "math.pyx": '''
# distutils: language = c
cdef extern from "testlib.h":
    int multiply_by_two(int x)

def double_value(x: int) -> int:
    """Double the input value using the external library."""
    return multiply_by_two(x)
''',
    }

    package = create_test_package(
        tmp_path,
        "linked-package",
        cython_files,
        backend_dir,
        pkg_dir_name="linked_package",
    )

    lib_dir = create_shared_lib(package)

    pyproject = package / "pyproject.toml"
    config = pyproject.read_text()
    config += f"""
[tool.hwh.cython.modules]
libraries = ["testlib"]
library_dirs = ["{lib_dir}"]
runtime_library_dirs = ["{lib_dir}"]
include_dirs = ["{lib_dir}"]
"""
    pyproject.write_text(config)

    test_script = package / "scripts" / "test_linking.py"
    test_script.write_text("""
from linked_package.math import double_value
print(f"Result: {double_value(21)}")
""")

    return package


@pytest.mark.parametrize("pip_arguments", [("--no-build-isolation",), ("-e",)])
def test_library_linking(tmp_path: Path, linked_package: Path, pip_arguments):
    """Test that extension successfully links against shared library."""
    # Create and set up virtual environment
    backend_dir = Path(__file__).parent.parent.parent.absolute()

    venv_dir = create_virtual_env(tmp_path / "venv")
    setup_test_env(venv_dir, backend_dir)

    arguments = ["pip", "install", *pip_arguments, str(linked_package)]
    # Install the package
    run_in_venv(
        venv_dir,
        arguments,
        show_output=True,
    )

    test_script = linked_package / "scripts" / "test_linking.py"
    verify_installation(venv_dir, test_script, "Result: 42")
