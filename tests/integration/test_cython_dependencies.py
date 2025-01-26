import pytest

from ..utils.package_utils import copy_test_package
from ..utils.venv_utils import run_in_venv
from ..utils.verification_utils import verify_installation


@pytest.fixture
def packages(tmp_path, backend_dir, fixture_dir):
    """Set up base and dependent packages."""
    base = copy_test_package("sample_package", tmp_path, fixture_dir, backend_dir)
    dependent = copy_test_package(
        "dependent_package",
        tmp_path,
        fixture_dir,
        backend_dir,
        dependencies=[f"sample-package @ file://{base}"],
    )
    return base, dependent


def test_regular_dependency_install(test_env, packages):
    """Test normal installation with Cython dependencies."""
    base_pkg, dep_pkg = packages
    test_script = dep_pkg / "scripts/check_dependency.py"

    run_in_venv(test_env, ["pip", "install", str(base_pkg)])
    run_in_venv(test_env, ["pip", "install", "--no-deps", str(dep_pkg)])
    verify_installation(test_env, test_script, "Cython dependency test passed!")


def test_editable_dependency_install(test_env, packages):
    """Test editable install with Cython dependencies."""
    base_pkg, dep_pkg = packages
    test_script = dep_pkg / "scripts/check_dependency.py"
    modified_test = dep_pkg / "scripts/check_modified.py"

    run_in_venv(test_env, ["pip", "install", str(base_pkg)])
    run_in_venv(test_env, ["pip", "install", "-e", str(dep_pkg)])

    # Test initial state
    verify_installation(test_env, test_script, "Cython dependency test passed!")

    # Modify source
    operations_pyx = dep_pkg / "dependent_package/operations.pyx"
    original = operations_pyx.read_text()
    modified = original.replace(
        "return self.base_op.compute() * self.factor",
        "return self.base_op.compute() * self.factor + 1.0",
    )

    try:
        # Rebuild
        operations_pyx.write_text(modified)
        run_in_venv(
            test_env,
            ["python", "-m", "build", "--no-isolation", "--wheel"],
            cwd=str(dep_pkg),
        )
        verify_installation(test_env, modified_test, "Cython dependency test passed!")
    finally:
        operations_pyx.write_text(original)


def test_multiple_versions(test_env, packages):
    """Test --force-reinstall with version update."""
    base_pkg, dep_pkg = packages
    test_script = dep_pkg / "scripts/check_dependency.py"

    # Initial install
    run_in_venv(test_env, ["pip", "install", str(base_pkg)])
    run_in_venv(test_env, ["pip", "install", str(dep_pkg)])
    verify_installation(test_env, test_script, "Cython dependency test passed!")

    # Update version in existing pyproject.toml
    pyproject_path = dep_pkg / "pyproject.toml"
    content = pyproject_path.read_text()
    content = content.replace('version = "0.1.0"', 'version = "0.2.0"')
    pyproject_path.write_text(content)

    # Force reinstall and verify
    run_in_venv(test_env, ["pip", "install", "--force-reinstall", str(dep_pkg)])
    verify_installation(test_env, test_script, "Cython dependency test passed!")

    result = run_in_venv(test_env, ["pip", "list"])
    # Verify version in pip list
    import re

    pattern = r"dependent_package\s+0\.2\.0"
    assert re.search(pattern, result.stdout)
