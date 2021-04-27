import tempfile
import os
import logging
import requests
import xmlrpc.client

from pyroma import distributiondata


def _get_project_data(project):
    # I think I should be able to monkeypatch a mock-thingy here... I think.
    response = requests.get(f"https://pypi.org/pypi/{project}/json")
    if response.status_code == 404:
        raise ValueError(f"Did not find '{project}' on PyPI. Did you misspell it?")
    if not response.ok:
        raise ValueError(
            f"Unknown http error: {response.status_code} {response.reason}"
        )

    return response.json()


def get_data(project):
    # Pick the latest release.
    project_data = _get_project_data(project)
    releases = project_data["releases"]
    data = project_data["info"]
    release = data["version"]
    logging.debug(f"Found {project} version {release}")

    # Map things around:
    data["long_description"] = data["description"]
    data["description"] = data["summary"]

    with xmlrpc.client.ServerProxy("https://pypi.org/pypi") as xmlrpc_client:
        roles = xmlrpc_client.package_roles(project)

    data["_owners"] = [user for (role, user) in roles if role == "Owner"]

    # Get download_urls:
    urls = releases[release]
    data["_pypi_downloads"] = bool(urls)

    # If there is a source download, download it, and get that data.
    # This is done mostly to do the imports check.
    data["_source_download"] = False
    data["_setuptools"] = None  # Mark as unknown, in case no sdist is found.
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
