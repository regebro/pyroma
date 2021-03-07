"""
Extract information from a distribution file by unpacking in a temporary
directory and then using projectdata on that.
"""

import os
import shutil
import tarfile
import tempfile
import zipfile

from pyroma import projectdata


def get_data(path):
    filename = os.path.split(path)[-1]
    basename, ext = os.path.splitext(filename)
    if basename.endswith(".tar"):
        basename, ignored = os.path.splitext(basename)

    tempdir = tempfile.mkdtemp()
    try:
        if ext in (".bz2", ".tbz", "tb2", ".gz", ".tgz", ".tar"):
            with tarfile.open(name=path, mode="r:*") as tar_file:
                tar_file.extractall(tempdir)

        elif ext in (".zip", ".egg"):
            with zipfile.ZipFile(path, mode="r") as zip_file:
                zip_file.extractall(tempdir)

        else:
            raise ValueError("Unknown file type: " + ext)

        projectpath = os.path.join(tempdir, basename)
        data = projectdata.get_data(projectpath)
    finally:
        shutil.rmtree(tempdir, ignore_errors=True)

    return data
