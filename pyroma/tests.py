import collections
import io
import os
import unittest

try:
    from xmlrpc import client as xmlrpclib
    from urllib import request as urllib
except ImportError:
    import xmlrpclib
    import urllib

from pyroma import projectdata, distributiondata, pypidata
from pyroma.ratings import rate
from pkg_resources import resource_filename, resource_string

long_description = resource_string(
    __name__, os.path.join("testdata", "complete", "README.txt")
)
if not isinstance(long_description, str):
    long_description = long_description.decode()
# Translate newlines to universal format
long_description = io.StringIO(long_description, newline=None).read()

COMPLETE = {
    "_setuptools": True,
    "name": "complete",
    "version": "1.0",
    "description": "This is a test package for pyroma.",
    "long_description": long_description,
    "classifiers": [
        "Development Status :: 6 - Mature",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "License :: OSI Approved :: MIT License",
    ],
    "keywords": ["pypi", "quality", "example"],
    "author": "Lennart Regebro",
    "author_email": "regebro@gmail.com",
    "url": "https://github.com/regebro/pyroma",
    "project_urls": {"Source Code": "https://github.com/regebro/pyroma"},
    "license": "MIT",
    "zip_safe": True,
    "test_suite": "complete",
}


class FakeResponse:
    def __init__(self, responsecode, filename=None):
        self.filename = filename
        self.headers = collections.defaultdict(lambda: None)
        self.code = responsecode

    def read(self):
        with open(self.filename, "rb") as f:
            file_contents = f.read()
        return file_contents


def urlopenstub(url):
    if url.find("readthedocs.org") != -1:
        host = url.split("/")[2]
        package = host.split(".")[0]
        # Faking the docs:
        if package in ("distribute", "complete"):
            return FakeResponse(200)
        else:
            # This package doesn't have docs on pythonhosted.org:
            return FakeResponse(404)

    if url.startswith("http://pypi.org/project"):
        filename = url[len("http://pypi.org/project/") :]
        # Faking PyPI package
        datafile = resource_filename(
            __name__, os.path.join("testdata", "xmlrpcdata", filename + ".html")
        )
        return FakeResponse(200, datafile)

    if url.startswith("http://pypi.python.org/packages"):
        filename = [x for x in url.split("/") if x][-1]
        # Faking PyPI file downloads
        datafile = resource_filename(
            __name__, os.path.join("testdata", "distributions", filename)
        )
        return FakeResponse(200, datafile)

    raise ValueError("Don't know how to stub " + url)


class ProxyStub:
    def __init__(self, dataname, real_class, developmode):
        filename = resource_filename(
            __name__, os.path.join("testdata", "xmlrpcdata", dataname)
        )
        data = {}
        with open(filename, encoding="UTF-8") as f:
            exec(f.read(), None, data)
        self.args = data["args"]
        self.kw = data["kw"]
        self._data = data["data"]

        if developmode:
            self._real = real_class(*self.args, **self.kw)
        else:
            self._real = None

    def __call__(self, *args, **kw):
        assert args == self.args
        assert kw == self.kw
        return self

    def _make_proxy(self, name):
        def _proxy_method(*args, **kw):
            return self._data[name][args]

        return _proxy_method

    def _make_unknown_proxy(self, name):
        def _proxy_method(*args, **kw):
            if self._real is None:
                raise AttributeError("ProxyStub unkown method " + name)
            print()
            print("== ProxyStub unknown method ==")
            print(name, ":", args, kw)
            result = getattr(self._real, name)(*args, **kw)
            print("Result :")
            print(result)
            return result

        return _proxy_method

    def __getattr__(self, attr):
        if attr in self._data:
            return self._make_proxy(attr)
        return self._make_unknown_proxy(attr)


class RatingsTest(unittest.TestCase):
    def _get_file_rating(self, dirname):
        directory = resource_filename(__name__, os.path.join("testdata", dirname))
        data = projectdata.get_data(directory)
        return rate(data)

    def test_complete(self):
        rating = self._get_file_rating("complete")
        # Should have a perfect score
        self.assertEqual(rating, (10, []))

    def test_setup_config(self):
        rating = self._get_file_rating("setup_config")
        self.assertEqual(rating, (10, []))

    def test_only_config(self):
        rating = self._get_file_rating("only_config")
        self.assertEqual(rating, (10, []))

    def test_minimal(self):
        rating = self._get_file_rating("minimal")

        self.assertEqual(
            rating,
            (
                2,
                [
                    "The package's version number does not comply with PEP-386 or PEP-440.",
                    "The package's description should be longer than 10 characters.",
                    "The package's long_description is quite short.",
                    "Your package does not have classifiers data.",
                    "You should specify what Python versions you support.",
                    "Your package does not have keywords data.",
                    "Your package does not have author data.",
                    "Your package does not have author_email data.",
                    "Your package should have a 'url' field with a link to the project home page, or a 'project_urls' field, with a dictionary of links, or both.",
                    "Your package does neither have a license field nor any license classifiers.",
                    "Specifying a development status in the classifiers gives users "
                    "a hint of how stable your software is.",
                ],
            ),
        )

    def test_lacking(self):
        rating = self._get_file_rating("lacking")

        self.assertEqual(
            rating,
            (
                0,
                [
                    "The package had no description!",
                    "The package's long_description is quite short.",
                    "Your package does not have classifiers data.",
                    "You should specify what Python versions you support.",
                    "Your package does not have keywords data.",
                    "Your package does not have author data.",
                    "Your package does not have author_email data.",
                    "Your package should have a 'url' field with a link to the project home page, or a 'project_urls' field, with a dictionary of links, or both.",
                    "Your package does neither have a license field nor any license classifiers.",
                    "Your long_description is not valid ReST: \n<string>:1: (WARNING/2) Inline literal start-string without end-string.",
                    "Specifying a development status in the classifiers gives users "
                    "a hint of how stable your software is.",
                ],
            ),
        )

    def test_custom_test(self):
        rating = self._get_file_rating("custom_test")

        self.assertEqual(
            rating,
            (
                2,
                [
                    "The package's version number does not comply with PEP-386 or PEP-440.",
                    "The package's description should be longer than 10 characters.",
                    "The package's long_description is quite short.",
                    "Your package does not have classifiers data.",
                    "You should specify what Python versions you support.",
                    "Your package does not have keywords data.",
                    "Your package does not have author data.",
                    "Your package does not have author_email data.",
                    "Your package should have a 'url' field with a link to the project home page, or a 'project_urls' field, with a dictionary of links, or both.",
                    "Your package does neither have a license field nor any license classifiers.",
                    "Specifying a development status in the classifiers gives users "
                    "a hint of how stable your software is.",
                ],
            ),
        )

    def test_markdown(self):
        # Markdown and text shouldn't get ReST errors
        testdata = COMPLETE.copy()
        testdata["long_description"] = "# Broken ReST\n\n``Valid  Markdown\n"
        testdata["long_description_content_type"] = "text/markdown"
        rating = rate(testdata)
        self.assertEqual(
            rating, (9, ["The package's long_description is quite short."])
        )

        testdata["long_description_content_type"] = "text/plain"
        rating = rate(testdata)
        self.assertEqual(
            rating, (9, ["The package's long_description is quite short."])
        )


class PyPITest(unittest.TestCase):
    def test_distribute(self):
        real_urlopen = urllib.urlopen
        real_server_proxy = xmlrpclib.ServerProxy
        try:
            xmlrpclib.ServerProxy = ProxyStub(
                "distributedata.py", xmlrpclib.ServerProxy, False
            )
            urllib.urlopen = urlopenstub
            data = pypidata.get_data("distribute")
            rating = rate(data)

            self.assertEqual(
                rating,
                (
                    9,
                    [
                        "The classifiers should specify what minor versions of Python "
                        "you support as well as what major version.",
                        "You should have three or more owners of the project on PyPI.",
                    ],
                ),
            )
        finally:
            xmlrpclib.ServerProxy = real_server_proxy
            urllib.urlopen = real_urlopen

    def test_complete(self):
        real_urlopen = urllib.urlopen
        real_server_proxy = xmlrpclib.ServerProxy
        try:
            xmlrpclib.ServerProxy = ProxyStub(
                "completedata.py", xmlrpclib.ServerProxy, False
            )
            urllib.urlopen = urlopenstub
            data = pypidata.get_data("complete")
            rating = rate(data)

            self.assertEqual(rating, (10, []))
        finally:
            xmlrpclib.ServerProxy = real_server_proxy
            urllib.urlopen = real_urlopen


class ProjectDataTest(unittest.TestCase):

    maxDiff = None

    def test_complete(self):
        directory = resource_filename(__name__, os.path.join("testdata", "complete"))

        data = projectdata.get_data(directory)
        self.assertEqual(data, COMPLETE)


class DistroDataTest(unittest.TestCase):
    def test_complete(self):
        directory = resource_filename(
            __name__, os.path.join("testdata", "distributions")
        )

        for filename in os.listdir(directory):
            if filename.startswith("complete"):
                data = distributiondata.get_data(os.path.join(directory, filename))
                self.assertEqual(data, COMPLETE)
