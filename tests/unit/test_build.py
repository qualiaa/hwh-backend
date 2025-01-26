import pytest

from hwh_backend.build import (
    _parse_build_settings,
    find_cython_files,
)


@pytest.mark.parametrize(
    "sources,exclude_dirs,file_structure,expected_count",
    [
        (["a.pyx"], ["foo"], {"test_project/": ["foo.pyx", "a.pyx", "x.pyx"]}, 1),
        (
            # sources
            None,
            # exclude_dirs
            ["foo/"],
            # file structure
            {
                "test_project/": ["foo.pyx", "a.pyx"],
                "test_project/include_me": ["pick.pyx"],
                "test_project/foo": ["skip.pyx"],
            },
            # num expected files after find_cython_files()
            3,
        ),
        (
            None,
            None,
            {
                "test_project/": ["a.pyx", "b.pyx"],
                "test_project/sub/": ["c.pyx", "d.pyx"],
            },
            4,
        ),
    ],
)
def test_find_cython_files_combinations(
    tmp_path, sources, exclude_dirs, file_structure, expected_count
):
    # Create test structure
    for dir_path, files in file_structure.items():
        full_dir = tmp_path / dir_path
        full_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            (full_dir / f).touch()

    pkg_dir = tmp_path / "test_project"
    result = find_cython_files(pkg_dir, sources=sources, exclude_dirs=exclude_dirs)
    print(result)
    assert len(result) == expected_count


def test_parse_build_settings():
    settings = {"annotate": "true", "nthreads": "4", "force": "false"}
    parsed = _parse_build_settings(settings)
    assert parsed["annotate"] is True
    assert parsed["nthreads"] == 4
    assert parsed["force"] is False


def test_parse_invalid_build_settings():
    settings = {"annotate": "true", "nthreads": "invalid", "force": "false"}
    parsed = _parse_build_settings(settings)
    assert "nthreads" not in parsed


def test_parse_empty_build_settings():
    assert _parse_build_settings(None) == {}
