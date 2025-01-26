import pytest

from ..utils.package_utils import copy_test_package
from ..utils.venv_utils import run_in_venv
from ..utils.verification_utils import verify_editable_install, verify_installation


@pytest.fixture
def packages(tmp_path, backend_dir, fixture_dir):
    """Set up test packages."""
    package_dir = copy_test_package(
        "sample_package", tmp_path, fixture_dir, backend_dir
    )
    dependent_dir = copy_test_package(
        "dependent_package",
        tmp_path,
        fixture_dir,
        backend_dir,
        dependencies=[f"sample-package @ file://{package_dir}"],
    )
    return package_dir, dependent_dir


def test_regular_install(test_env, packages):
    """Test regular pip install with nested modules."""
    pkg_dir, _ = packages
    test_script = pkg_dir / "scripts/verify_nested_imports.py"

    run_in_venv(test_env, ["pip", "install", str(pkg_dir)])
    verify_installation(test_env, test_script, "All nested module tests passed!")


def test_editable_install(test_env, packages):
    """Test editable install with source modifications."""
    pkg_dir, _ = packages
    test_script = pkg_dir / "scripts/verify_nested_imports.py"
    base_pyx = pkg_dir / "sample_package/core/base.pyx"

    # Install in editable mode
    run_in_venv(test_env, ["pip", "install", "-e", str(pkg_dir)])

    # Test modification
    original = base_pyx.read_text()
    modified = original.replace(
        "return self.value * 2.0", "return self.value * 3.0  # Modified!"
    )
    verify_editable_install(
        test_env,
        pkg_dir,
        base_pyx,
        original,
        modified,
        test_script,
        "All nested module tests passed!",
    )


def test_dependency_chain(test_env, packages):
    """Test package with nested Cython dependencies."""
    pkg_dir, dep_dir = packages
    dep_script = dep_dir / "scripts/check_dependency.py"

    run_in_venv(test_env, ["pip", "install", str(pkg_dir)])
    run_in_venv(test_env, ["pip", "install", "--no-deps", str(dep_dir)])
    verify_installation(test_env, dep_script, "Cython dependency test passed!")
