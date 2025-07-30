# Extracts information from a project
import build
import build.util
import os
import pathlib
import re
from importlib.metadata import metadata

from setuptools.config.setupcfg import read_configuration
from distutils.errors import DistutilsFileError

# MAP from old setup.py type keys to Core Metadata keys
METADATA_MAP = {
    "description": "summary",
    "classifiers": "classifier",
    "project-urls": "project-url",
    "url": "home-page",
    "long-description": "description",
    "long-description-content-type": "description-content-type",
    "python-requires": "requires-python",
}


def normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def wheel_metadata(path, isolated=None):
    # If explictly specified whether to use isolation, pass it directly
    if isolated is not None:
        return build.util.project_wheel_metadata(path, isolated=isolated)

    # Otherwise, try without build isolation first for efficiency
    try:
        return build.util.project_wheel_metadata(path, isolated=False)
    # If building with build isolation fails, e.g. missing build deps, try with it
    except (build.BuildException, build.BuildBackendException):
        return build.util.project_wheel_metadata(path, isolated=True)


def build_metadata(path, isolated=None):
    try:
        metadata = wheel_metadata(path, isolated)
    except build.BuildBackendException:
        # The backend failed spectacularily. This happens with old packages,
        # when we can't build a wheel. It's not always a fatal error. F ex, if
        # you are getting info for a package from PyPI, we already have the
        # metadata from PyPI, we just couldn't get the additional build data.
        return {"_wheel_build_failed": True}

    return normalize_metadata(metadata)


def normalize_metadata(metadata):
    # As far as I can tell, we can't trust that the builders normalize the keys,
    # so we do it here. Definitely most builders do not lower case them, which
    # Core Metadata Specs recommend.
    data = {}
    for key in set(metadata.keys()):
        value = metadata.get_all(key)
        key = normalize(key)

        if len(value) == 1:
            value = value[0]
            if value.strip() == "UNKNOWN":
                # XXX This is also old behavior that may not hjappen any more.
                continue

        data[key] = value

    if "description" not in data.keys():
        # XXX I *think* having the description as a payload doesn't happen anymore, but I haven't checked.
        # Having the description as a payload tends to add two newlines, we clean that up here:
        description = metadata.get_payload().strip()
        if description:
            data["description"] = description + "\n"
    return data


def installed_metadata(name):
    """Retrieve the metadata for an package that is installed in the environment."""
    return normalize_metadata(metadata(name))


def get_build_data(path, isolated=None):
    metadata = build_metadata(path, isolated=isolated)
    # Check if there is a pyproject_toml
    if "pyproject.toml" not in os.listdir(path):
        metadata["_missing_pyproject_toml"] = True
    return metadata


def get_setupcfg_data(path):
    data = read_configuration(str(pathlib.Path(path) / "setup.cfg"))

    metadata = {}
    # Python requires is under "options" in setup.cfg (and so are other
    # requirements, but those are optional and have no tests)
    if "python_requires" in data["options"]:
        metadata["requires-python"] = data["options"]["python_requires"]

    for key, value in data["metadata"].items():
        key = normalize(key)
        if key in METADATA_MAP:
            key = METADATA_MAP[key]
        metadata[key] = value

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
                return {"_no_config_found": True}
        else:
            # There's something else wrong
            raise e
