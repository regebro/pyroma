# Extracts information from a distribution file by unpacking in a temporary
# directory and then using projectdata on that.
import os
import shutil
import tempfile
import zipfile
import tarfile

from pyroma import projectdata


def get_data(path):
    filename = os.path.split(path)[-1]
    basename, ext = os.path.splitext(filename)
    if basename.endswith('.tar'):
        basename, ignored = os.path.splitext(basename)

    try:
        tempdir = tempfile.mkdtemp()

        if ext in ('.bz2', '.tbz', 'tb2', '.gz', '.tgz', '.tar'):
            tarfile.open(name=path, mode='r:*').extractall(tempdir)

        elif ext in ('.zip', '.egg'):
            zipfile.ZipFile(path, mode='r').extractall(tempdir)

        else:
            raise ValueError('Unknown file type: ' + ext)

        projectpath = os.path.join(tempdir, basename)
        data = projectdata.get_data(projectpath)

    finally:
        shutil.rmtree(tempdir)

    return data
