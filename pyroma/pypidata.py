import xmlrpclib
import urllib
import tempfile
import os
import contextlib
import re
from pyroma import distributiondata

OWNER_RE = re.compile(r'<strong>Package Index Owner:</strong>\s*?<span>(.*?)</span>')

def _get_client():
    # I think I should be able to monkeypatch a mock-thingy here... I think.
    return xmlrpclib.ServerProxy('http://pypi.python.org/pypi')

def get_data(project):
    client = _get_client()
    # Pick the latest release.
    release = client.package_releases(project)[0]
    # Get the metadata:
    data = client.release_data(project, release)
    
    # Map things around:
    data['long_description'] = data['description']
    data['description'] = data['summary']
    
    # Get download_urls:
    urls = client.release_urls(project, release)
    data['_pypi_downloads'] = bool(urls)
    
    # Scrape the PyPI project page for owner info:
    page = urllib.urlopen('http://pypi.python.org/pypi/' + project)
    html = page.read()
    owners = OWNER_RE.search(html).groups()[0]
    data['_owners'] = [x.strip() for x in owners.split(',')]
    
    # See if there is any docs on http://packages.python.org/
    page = urllib.urlopen('http://packages.python.org/' + project)
    if page.code == 200:
        data['_packages_docs'] = True
    else:
        data['_packages_docs'] = False

    # If there is a source download, download it, and get that data.
    # This is done mostly to do the imports check.
    data['_source_download'] = False
    for download in urls:
        if download['packagetype'] == 'sdist':
            # Found a source distribution. Download and analyze it.
            tempdir = tempfile.gettempdir()
            filename = download['url'].split('/')[-1]
            tmp = os.path.join(tempdir, filename)
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
    