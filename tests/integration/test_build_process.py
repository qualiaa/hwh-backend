import os
import tomllib
from pathlib import Path

import pytest

from hwh_backend import build, parser


def generate_project_dir(project_dir, pyproject, filestructure):
    import tomli_w

    project_dir.mkdir()
    toml_path = project_dir / "pyproject.toml"
    with open(toml_path, "wb") as f:
        tomli_w.dump(pyproject, f)

    readme_path = project_dir / "README.md"
    readme_path.write_text("lorem ipsum")

    for dir_name, file_names in filestructure.items():
        new_path: Path = project_dir / dir_name
        new_path.mkdir()
        for f in file_names:
            f_path: Path = new_path / f
            f_path.touch()
    return project_dir


def list_files_walk(start_path="."):
    for root, dirs, files in os.walk(start_path):
        for file in files:
            print(os.path.join(root, file))


@pytest.mark.parametrize(
    "sources,exclude_dirs,file_structure",
    [
        (["a.pyx"], ["foo"], {"test_project/": ["foo.pyx", "a.pyx", "x.pyx"]}),
        ([], ["foo"], {"test_project/": ["foo.pyx", "a.pyx", "x.pyx"]}),
        (
            None,
            ["foo/"],  # exclude dirs inside the package
            {
                "test_project/": ["foo.pyx", "a.pyx", "x.pyx"],
                "test_project/include_me": ["pickme.pyx", "andme.pyx"],
                "test_project/exclude_me": ["dontthis.pyx", "nor_this.pyx"],
            },
        ),
        (
            None,
            None,
            {
                "test_project/": ["foo.pyx", "a.pyx", "x.pyx"],
                "test_project/sub/": ["sub1.pyx", "sub2.pyx"],
            },
        ),
    ],
)
def test_find_cython_files(
    tmp_path, sample_pyproject, sources, exclude_dirs, file_structure
):
    print(f"Temp path = {tmp_path}")
    print(f"Sources = {sources}")
    print(f"Exlude dirs = {exclude_dirs}")
    pyproj = tomllib.loads(sample_pyproject)
    pyproj["tool"]["hwh"]["cython"]["modules"] = {
        "sources": sources or "",
        "exclude_dirs": exclude_dirs or "",
    }

    project_dir = tmp_path / "test_project"
    generate_project_dir(project_dir, pyproj, file_structure)
    p = parser.PyProject(project_dir)
    pkg_dir = project_dir / "test_project"
    res_files: list[Path] = build.find_cython_files(
        pkg_dir,
        sources=p.get_hwh_config().cython.sources,
        exclude_dirs=p.get_hwh_config().cython.exclude_dirs,
    )

    if sources:
        for f in res_files:
            assert f.name in sources
        return

    excluded_files = []
    exclude_dirs = exclude_dirs or []
    for dir in exclude_dirs:
        dir_path = project_dir / dir
        excluded_files.extend(list(dir_path.rglob("*.pyx")))

    all_files = []
    for dir, files in file_structure.items():
        dir_path = project_dir / dir
        sub_files = [dir_path / f for f in files]
        all_files.extend(sub_files)

    # all_strs = "\n".join([str(fname) for fname in all_files])
    # excluded_strs = "\n".join([str(fname) for fname in excluded_files])
    # print(f"ALL FILES\n{all_strs}\n===\n")
    # print(f"EXCL FILES\n{excluded_strs}\n===\n")
    for rf in res_files:
        assert rf not in excluded_files
        if rf not in excluded_files:
            assert rf in all_files
