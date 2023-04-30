"""
Extract information from a distribution file by unpacking in a temporary
directory and then using projectdata on that.
"""

import os
import pathlib
import shutil
import tarfile
import tempfile
import zipfile

from pyroma import projectdata


def _safe_extract_tar(tar, path=".", members=None, numeric_owner=False):
    """Safely extract a tar w/o traversing parent dirs to fix CVE-2007-4559."""
    root = pathlib.Path(path).resolve()
    for member in tar.getmembers():
        member_path = (root / member.name).resolve()
        if root not in member_path.parents:
            raise Exception(f"Attempted path traversal in tar file {tar.name!r}")
    tar.extractall(path, members, numeric_owner=numeric_owner)


def get_data(path):
    filename = os.path.split(path)[-1]
    basename, ext = os.path.splitext(filename)
    if basename.endswith(".tar"):
        basename, ignored = os.path.splitext(basename)

    tempdir = tempfile.mkdtemp()
    try:
        if ext in (".bz2", ".tbz", "tb2", ".gz", ".tgz", ".tar"):
            with tarfile.open(name=path, mode="r:*") as tar_file:
                _safe_extract_tar(tar_file, path=tempdir)

        elif ext in (".zip", ".egg"):
            with zipfile.ZipFile(path, mode="r") as zip_file:
                zip_file.extractall(tempdir)

        else:
            raise ValueError("Unknown file type: " + ext)

        projectpath = os.path.join(tempdir, basename)
        data = projectdata._get_data(projectpath)
    finally:
        shutil.rmtree(tempdir, ignore_errors=True)

    return data
