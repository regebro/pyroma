import logging
import os
import re
import requests
import tempfile
import xmlrpc.client

from pyroma import distributiondata

# MAP from old PyPI `info` keys to Core Metadata keys
INFO_MAP = {
    "classifiers": "classifier",
    "project-urls": "project-url",
    "project-url": "home-page",
}

DEFAULT_PYPI_XMLRPC_URL = "https://pypi.org/pypi"


def normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def _get_xmlrpc_url(index_url=None):
    if not index_url:
        return DEFAULT_PYPI_XMLRPC_URL

    base_url = index_url.rstrip("/")
    if base_url.endswith("/pypi"):
        return base_url
    return f"{base_url}/pypi"


def _get_project_data(project, index_url=None):
    # I think I should be able to monkeypatch a mock-thingy here... I think.
    xmlrpc_url = _get_xmlrpc_url(index_url)
    response = requests.get(f"{xmlrpc_url}/{project}/json")
    if response.status_code == 404:
        if xmlrpc_url == DEFAULT_PYPI_XMLRPC_URL:
            raise ValueError(f"Did not find '{project}' on PyPI. Did you misspell it?")
        raise ValueError(f"Did not find '{project}' on package index {xmlrpc_url}.")
    if not response.ok:
        raise ValueError(f"Unknown http error: {response.status_code} {response.reason}")

    return response.json()


def get_data(project, index_url=None):
    # Pick the latest release.
    project_data = _get_project_data(project, index_url=index_url)
    releases = project_data["releases"]
    data = {}

    for key, value in project_data["info"].items():
        key = normalize(key)
        if key in INFO_MAP:
            key = INFO_MAP[key]
        data[key] = value

    release = data["version"]
    logging.debug(f"Found {project} version {release}")

    try:
        with xmlrpc.client.ServerProxy(_get_xmlrpc_url(index_url)) as xmlrpc_client:
            roles = xmlrpc_client.package_roles(project)
            data["_owners"] = [user for (role, user) in roles if role == "Owner"]
    except xmlrpc.client.ProtocolError:
        logging.warning(
            "Could not get package roles from XMLRPC API. Not all custom indexes "
            "support this, and some may have it disabled. Skipping role checks."
        )

    # Get download_urls:
    urls = releases[release]
    data["_pypi_downloads"] = bool(urls)

    # If there is a source download, download it, and get that data.
    # This is done mostly to do the imports check.
    data["_source_download"] = False
    data["_has_sdist"] = False

    for download in urls:
        if download["packagetype"] == "sdist":
            # Found a source distribution. Download and analyze it.
            data["_has_sdist"] = True
            tempdir = tempfile.gettempdir()
            filename = download["url"].split("/")[-1]
            tmp = os.path.join(tempdir, filename)
            logging.debug(f"Downloading {filename} to verify distribution")
            try:
                with open(tmp, "wb") as outfile:
                    outfile.write(requests.get(download["url"]).content)
                ddata = distributiondata.get_data(tmp)
            except Exception:
                # Clean up the file
                os.unlink(tmp)
                raise

            # Combine them, with the PyPI data winning:
            ddata.update(data)
            data = ddata
            data["_source_download"] = True
            break

    return data
