# Extracts information from a project
import build
import build.util
import os
import pathlib

from setuptools.config.setupcfg import read_configuration
from distutils.errors import DistutilsFileError

METADATA_MAP = {
    "summary": "description",
    "classifier": "classifiers",
    "project_url": "project_urls",
    "home_page": "url",
    "description": "long_description",
    "description_content_type": "long_description_content_type",
    "requires_python": "python_requires",
}


def build_metadata(path, isolated=None):
    # If explictly specified whether to use isolation, pass it directly
    if isolated is not None:
        return build.util.project_wheel_metadata(path, isolated=isolated)

    # Otherwise, try without build isolation first for efficiency
    try:
        return build.util.project_wheel_metadata(path, isolated=False)
    # If building with build isolation fails, e.g. missing build deps, try with it
    except build.BuildException:
        return build.util.project_wheel_metadata(path, isolated=True)


def map_metadata_keys(metadata):
    data = {}
    if "Description" not in metadata.keys():
        # Having the description as a payload tends to add two newlines, we clean that up here:
        long_description = metadata.get_payload().strip() + "\n"
        data["long_description"] = long_description

    for key in set(metadata.keys()):
        value = metadata.get_all(key)
        if len(value) == 1:
            value = value[0]
            if value.strip() == "UNKNOWN":
                continue
        key = key.lower().replace("-", "_")
        if key in METADATA_MAP:
            key = METADATA_MAP[key]
        data[key] = value
    return data


def get_build_data(path, isolated=None):
    metadata = map_metadata_keys(build_metadata(path, isolated=isolated))
    # Check if there is a pyproject_toml
    if "pyproject.toml" not in os.listdir(path):
        metadata["_missing_pyproject_toml"] = True
    return metadata


def get_setupcfg_data(path):
    # Note: By default, setup.cfg will read the pyroma.git/setup.cfg - forcing explicit setup.cfg under test's file path
    data = read_configuration(str(pathlib.Path(path) / "setup.cfg"))
    metadata = data["metadata"]
    return metadata


def get_data(path):
    data = _get_data(path)
    if data:
        # We got something, add the path to it.
        data["_path"] = path
    return data


def _get_data(path):
    try:
        return get_build_data(path)
    except build.BuildException as e:
        if "no pyproject.toml or setup.py" in e.args[0]:
            # It couldn't build the package, because there is no setup.py or pyproject.toml.
            # Let's see if there is a setup.cfg:
            try:
                metadata = get_setupcfg_data(path)
                # Yes, there's a setup.cfg. Pyroma accepted this earlier, because it worked,
                # and at some point the idea was that that setup.cfg should replace setup.py.
                # But that never happened, and instead pyproject.toml arrived.
                metadata["_missing_build_system"] = True
                return metadata
            except DistutilsFileError:
                # There is no setup.cfg either, so this isn't a python package at all
                return {}
        else:
            # There's something else wrong
            raise e
