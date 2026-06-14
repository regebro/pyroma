# Extracts information from a project
import build
import build.util
import os
import pathlib
import re
import tomli as tomllib

from setuptools.config import pyprojecttoml, setupcfg
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


def _read_pyproject(path):
    pyproject = pathlib.Path(path) / "pyproject.toml"
    if not pyproject.exists():
        return None

    with open(pyproject, "rb") as f:
        return tomllib.load(f)


def _guess_readme_content_type(filename):
    suffix = pathlib.Path(filename).suffix.lower()
    if suffix in (".md", ".markdown"):
        return "text/markdown"
    if suffix == ".rst":
        return "text/x-rst"
    return "text/plain"


def _read_project_readme(path, readme):
    if isinstance(readme, str):
        readme_path = pathlib.Path(path) / readme
        return readme_path.read_text(encoding="UTF-8"), _guess_readme_content_type(readme)

    if isinstance(readme, dict):
        if "text" in readme:
            content_type = readme.get("content-type", "text/plain")
            return readme["text"], content_type
        if "file" in readme:
            content_type = readme.get("content-type", _guess_readme_content_type(readme["file"]))
            readme_path = pathlib.Path(path) / readme["file"]
            return readme_path.read_text(encoding="UTF-8"), content_type

    return None, None


def get_pyproject_data(path):
    pyproject = _read_pyproject(path)
    if pyproject is None:
        return None

    project = dict(pyproject.get("project", {}))
    build_system = pyproject.get("build-system", {})
    backend = build_system.get("build-backend", "")

    if backend.startswith("setuptools.build_meta"):
        data = get_setuptools_data(path, project)
    else:
        data = _pep621_to_metadata(path, project)

    if backend:
        data["_build_backend"] = backend
    return data


def get_setuptools_data(path, project):
    pyproject_path = pathlib.Path(path) / "pyproject.toml"
    config = pyprojecttoml.read_configuration(str(pyproject_path), expand=True, ignore_option_errors=False)
    expanded = dict(config.get("project", {}))
    expanded["_build_backend"] = project.get("_build_backend")
    return _pep621_to_metadata(path, expanded)


def _pep621_to_metadata(path, project):
    if not project:
        return {}

    if "description" in project:
        project["summary"] = project.pop("description")

    if "classifiers" in project:
        project["classifier"] = project.pop("classifiers")

    if "keywords" in project and isinstance(project["keywords"], list):
        project["keywords"] = ",".join(project["keywords"])

    if "dependencies" in project:
        project["requires-dist"] = project.pop("dependencies")

    authors = project.pop("authors", None)
    if authors:
        first = authors[0]
        if "name" in first:
            project["author"] = first["name"]
        if "email" in first:
            project["author-email"] = first["email"]

    if "license" in project:
        license_data = project["license"]
        if isinstance(license_data, dict):
            if "text" in license_data:
                project["license"] = license_data["text"]
            elif "file" in license_data:
                license_path = pathlib.Path(path) / license_data["file"]
                project["license"] = license_path.read_text(encoding="UTF-8")

    urls = project.pop("urls", None)
    if urls:
        project_urls = []
        for title, url in urls.items():
            project_urls.append(f"{title}, {url}")
            if normalize(title) == "homepage":
                project["home-page"] = url
        if project_urls:
            project["project-url"] = project_urls

    readme = project.pop("readme", None)
    if readme is not None:
        description, content_type = _read_project_readme(path, readme)
        if description:
            # Keep newline behavior from built metadata for consistent validation.
            project["description"] = description if description.endswith("\n") else description + "\n"
        if content_type:
            project["description-content-type"] = content_type

    return project


def _has_required_metadata(data):
    # A package must have these to avoid needing backend-generated metadata.
    return bool(data.get("name") and data.get("version"))


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
                # XXX This is also old behavior that may not happen any more.
                continue

        data[key] = value

    if "description" not in data.keys():
        # XXX I *think* having the description as a payload doesn't happen anymore, but I haven't checked.
        # Having the description as a payload tends to add two newlines, we clean that up here:
        description = metadata.get_payload().strip()
        if description:
            data["description"] = description + "\n"
    return data


def get_build_data(path, isolated=None):
    metadata = build_metadata(path, isolated=isolated)
    # Check if there is a pyproject_toml
    if "pyproject.toml" not in os.listdir(path):
        metadata["_missing_pyproject_toml"] = True
    return metadata


def get_setupcfg_data(path):
    data = setupcfg.read_configuration(str(pathlib.Path(path) / "setup.cfg"))

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
    pyproject = get_pyproject_data(path)

    if pyproject is not None and _has_required_metadata(pyproject):
        return pyproject

    try:
        metadata = get_build_data(path)
        if pyproject:
            # Prefer explicit pyproject metadata; use wheel metadata as a fallback source.
            metadata.update(pyproject)
        return metadata
    except build.BuildException as e:
        if "no pyproject.toml or setup.py" in e.args[0]:
            # It couldn't build the package, because there is no setup.py or pyproject.toml.
            # Let's see if there is a setup.cfg:
            try:
                metadata = get_setupcfg_data(path)
                if pyproject:
                    metadata.update(pyproject)
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
