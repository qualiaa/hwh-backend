from pathlib import Path
from typing import Optional

from .venv_utils import run_in_venv


def verify_installation(
    venv_dir: Path,
    test_script: Path,
    expected_output: str,
    cwd: Optional[str] = None,
) -> None:
    """Verify package installation by running a test script."""
    result = run_in_venv(venv_dir, ["python", str(test_script)], cwd=cwd)
    assert expected_output in result.stdout, f"Expected '{expected_output}' in output"


def verify_editable_install(
    venv_dir: Path,
    package_dir: Path,
    source_file: Path,
    original_content: str,
    modified_content: str,
    test_script: Path,
    expected_output: str,
) -> None:
    """Verify editable installation with source modification."""
    try:
        # Modify source file
        source_file.write_text(modified_content)

        # Rebuild package
        run_in_venv(
            venv_dir,
            ["python", "-m", "build", "--no-isolation", "--wheel"],
            cwd=str(package_dir),
            show_output=True,
        )

        # Verify modified behavior
        verify_installation(venv_dir, test_script, expected_output)
    finally:
        # Restore original content. Do we need this though?
        source_file.write_text(original_content)
