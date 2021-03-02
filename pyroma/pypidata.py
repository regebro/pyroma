import tempfile
import os
import logging
from pyroma import distributiondata

try:
    from xmlrpc import client as xmlrpclib
    from urllib import request as urllib
except ImportError:
    import xmlrpclib
    import urllib


def _get_client():
    # I think I should be able to monkeypatch a mock-thingy here... I think.
    return xmlrpclib.ServerProxy("https://pypi.org/pypi")


def get_data(project):
    client = _get_client()
    # Pick the latest release.
    releases = client.package_releases(project)
    if not releases:
        # Try to find project by case-insensitive name
        project_name = project.lower()
        projects = client.search({"name": project_name})
        projects = [p for p in projects if p["name"].lower() == project_name]
        if not projects:
            raise ValueError(
                f"Did not find '{project}' on PyPI. Did you misspell it?"
            )
        project = projects[0]["name"]
        releases = [p["version"] for p in reversed(projects)]
    release = releases[0]
    # Get the metadata:
    logging.debug(f"Found {project} version {release}")
    data = client.release_data(project, release)

    # Map things around:
    data["long_description"] = data["description"]
    data["description"] = data["summary"]

    roles = client.package_roles(project)
    data["_owners"] = [user for (role, user) in roles if role == "Owner"]

    # Get download_urls:
    urls = client.release_urls(project, release)
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
                    outfile.write(urllib.urlopen(download["url"]).read())
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
