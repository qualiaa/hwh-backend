import pytest

from ..utils.package_utils import copy_test_package
from ..utils.venv_utils import run_in_venv
from ..utils.verification_utils import verify_installation


@pytest.fixture
def interface_packages(tmp_path, backend_dir, fixture_dir):
    """Set up base_math and geometry packages."""
    base_math = copy_test_package(
        "base_math", tmp_path, fixture_dir / "cython_interface", backend_dir
    )
    geometry = copy_test_package(
        "geometry",
        tmp_path,
        fixture_dir / "cython_interface",
        backend_dir,
        dependencies=[f"base_math @ file://{base_math}"],
    )
    return base_math, geometry


def test_interface_regular_install(test_env, interface_packages):
    """Test interface dependencies with regular install."""
    base_math, geometry = interface_packages
    test_script = geometry / "scripts/assert_geometry_operations.py"

    run_in_venv(test_env, ["pip", "install", str(base_math)])
    run_in_venv(test_env, ["pip", "install", "--no-build-isolation", str(geometry)])
    verify_installation(test_env, test_script, "All tests passed!")


def test_interface_editable_install(test_env, interface_packages):
    """Test interface with editable install and modifications."""
    base_math, geometry = interface_packages
    shapes_pyx = geometry / "geometry/shapes.pyx"
    test_script = geometry / "scripts/assert_geometry_operations.py"
    modified_test = geometry / "scripts/assert_vector_in_geometry_mod.py"

    # Install base normally, geometry in editable mode
    run_in_venv(test_env, ["pip", "install", str(base_math)])
    run_in_venv(test_env, ["pip", "install", "-e", str(geometry)])
    verify_installation(test_env, test_script, "All tests passed!")

    # Modify geometry implementation
    original = shapes_pyx.read_text()
    modified = original.replace(
        "return self.size.x * self.size.y",
        "return self.size.x * self.size.y * 2  # Modified!",
    )

    try:
        shapes_pyx.write_text(modified)
        run_in_venv(
            test_env,
            ["python", "-m", "build", "--no-isolation", "--wheel"],
            cwd=str(geometry),
        )
        verify_installation(test_env, modified_test, "Regular install test passed!")
    finally:
        shapes_pyx.write_text(original)
