import tempfile
import os
import re
import logging
from pyroma import distributiondata
try:
    from xmlrpc import client as xmlrpclib
    from urllib import request as urllib
except ImportError:
    import xmlrpclib
    import urllib

OWNER_RE = re.compile(
    r'<strong>Package Index Owner:</strong>\s*?<span>(.*?)</span>')
READTHEDOCS_RE = re.compile(r'(https?://.*?\.readthedocs.org)')


def _get_client():
    # I think I should be able to monkeypatch a mock-thingy here... I think.
    return xmlrpclib.ServerProxy('http://pypi.python.org/pypi')


def get_data(project):
    client = _get_client()
    # Pick the latest release.
    releases = client.package_releases(project)
    if not releases:
        # Try to find project by case-insensitive name
        project_name = project.lower()
        projects = client.search({'name': project_name})
        projects = [p for p in projects if p['name'].lower() == project_name]
        if not projects:
            raise ValueError(
                "Did not find '%s' on PyPI. Did you misspell it?" % project)
        project = projects[0]['name']
        releases = [p['version'] for p in reversed(projects)]
    release = releases[0]
    # Get the metadata:
    logging.debug("Found %s version %s" % (project, release))
    data = client.release_data(project, release)

    # Map things around:
    data['long_description'] = data['description']
    data['description'] = data['summary']

    # Get download_urls:
    urls = client.release_urls(project, release)
    data['_pypi_downloads'] = bool(urls)

    # Scrape the PyPI project page for owner info:
    url = '/'.join(('http://pypi.python.org/pypi', project, release))
    page = urllib.urlopen(url)
    content_type = page.headers.get('content-type', '')
    if '=' not in content_type:
        encoding = 'utf-8'
    else:
        encoding = content_type.split('=')[1]
    html = page.read().decode(encoding)
    owners = OWNER_RE.search(html).groups()[0]
    data['_owners'] = [x.strip() for x in owners.split(',')]

    logging.debug("Looking for documentation")
    # See if there is any docs on http://pythonhosted.org
    data['_packages_docs'] = False
    try:
        page = urllib.urlopen('http://pythonhosted.org/' + project)
        if page.code == 200:
            data['_packages_docs'] = True
    except urllib.HTTPError:
        pass

    # Maybe on readthedocs?
    data['_readthe_docs'] = False
    rtdocs = READTHEDOCS_RE.search(html)
    if rtdocs:
        page = urllib.urlopen(rtdocs.groups()[0])
        if page.code == 200:
            data['_readthe_docs'] = True

    # If there is a source download, download it, and get that data.
    # This is done mostly to do the imports check.
    data['_source_download'] = False
    data['_setuptools'] = None  # Mark as unknown, in case no sdist is found.
    data['_has_sdist'] = False

    for download in urls:
        if download['packagetype'] == 'sdist':
            # Found a source distribution. Download and analyze it.
            data['_has_sdist'] = True
            tempdir = tempfile.gettempdir()
            filename = download['url'].split('/')[-1]
            tmp = os.path.join(tempdir, filename)
            logging.debug("Downloading %s to verify distribution" % filename)
            try:
                with open(tmp, 'wb') as outfile:
                    outfile.write(urllib.urlopen(download['url']).read())
                ddata = distributiondata.get_data(tmp)
            except Exception:
                # Clean up the file
                os.unlink(tmp)
                raise

            # Combine them, with the PyPI data winning:
            ddata.update(data)
            data = ddata
            data['_source_download'] = True
            break

    return data
