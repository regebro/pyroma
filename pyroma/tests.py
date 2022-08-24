import io
import json
import os
import unittest
import unittest.mock
from pkg_resources import resource_filename, resource_string
from xmlrpc import client as xmlrpclib

from pyroma import projectdata, distributiondata, pypidata
from pyroma.ratings import rate

long_description = resource_string(__name__, os.path.join("testdata", "complete", "README.txt"))
if not isinstance(long_description, str):
    long_description = long_description.decode()
# Translate newlines to universal format
long_description = io.StringIO(long_description, newline=None).read()

COMPLETE = {
    "metadata_version": "2.1",
    "name": "complete",
    "version": "1.0.dev1",
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
    "keywords": "pypi,quality,example",
    "author": "Lennart Regebro",
    "author_email": "regebro@gmail.com",
    "url": "https://github.com/regebro/pyroma",
    "project_urls": "Source Code, https://github.com/regebro/pyroma",
    "requires_dist": "zope.event",
    "requires_python": ">=2.6",
    "license": "MIT",
}


class ProxyStub:
    def set_debug_context(self, dataname, real_class, developmode):
        filename = resource_filename(__name__, os.path.join("testdata", "xmlrpcdata", dataname))
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
        if attr in ("_data", "_make_proxy", "_make_unknown_proxy"):
            raise AttributeError("Break infinite recursion chain")
        if attr in self._data:
            return self._make_proxy(attr)
        return self._make_unknown_proxy(attr)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        return


proxystub = ProxyStub()


class RatingsTest(unittest.TestCase):

    maxDiff = None

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

        self.assertEqual(
            rating,
            (
                8,
                [
                    "You seem to have a setup.cfg, but neither a setup.py, nor a build-system defined. "
                    "This makes it unclear how your project should be built. You probably want to "
                    "have a pyproject.toml file with the following configuration:\n\n"
                    "    [build-system]\n"
                    '    requires = ["setuptools>=42"]\n'
                    '    build-backend = "setuptools.build_meta"\n\n'
                    "In the future this will become a hard failure and your package will be "
                    'rated as "not cheese".'
                ],
            ),
        )

    def test_pep517(self):
        rating = self._get_file_rating("pep517")
        self.assertEqual(
            rating,
            (
                10,
                [],
            ),
        )

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
                    "You should specify what Python versions you support with 'classifiers=...'.\nYou should specify what Python versions you support with 'python_requires=....'.",
                    "Your package does not have keywords data.",
                    "Your package does not have author data.",
                    "Your package does not have author_email data.",
                    "Your package should have a 'url' field with a link to the project home page, or a "
                    "'project_urls' field, with a dictionary of links, or both.",
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
                    "You should specify what Python versions you support with 'classifiers=...'.\nYou should specify what Python versions you support with 'python_requires=....'.",
                    "Your package does not have keywords data.",
                    "Your package does not have author data.",
                    "Your package does not have author_email data.",
                    "Your package should have a 'url' field with a link to the project home page, or a "
                    "'project_urls' field, with a dictionary of links, or both.",
                    "Your package does neither have a license field nor any license classifiers.",
                    "Your long_description is not valid ReST: \n<string>:1: (WARNING/2) Inline literal "
                    "start-string without end-string.",
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
                    "You should specify what Python versions you support with 'classifiers=...'.\nYou should specify what Python versions you support with 'python_requires=....'.",
                    "Your package does not have keywords data.",
                    "Your package does not have author data.",
                    "Your package does not have author_email data.",
                    "Your package should have a 'url' field with a link to the project home page, or a "
                    "'project_urls' field, with a dictionary of links, or both.",
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
        self.assertEqual(rating, (9, ["The package's long_description is quite short."]))

        testdata["long_description_content_type"] = "text/plain"
        rating = rate(testdata)
        self.assertEqual(rating, (9, ["The package's long_description is quite short."]))


class PyPITest(unittest.TestCase):

    maxDiff = None

    @unittest.mock.patch("xmlrpc.client.ServerProxy", proxystub)
    @unittest.mock.patch("pyroma.pypidata._get_project_data")
    def test_distribute(self, projectdatamock):
        datafile = resource_filename(__name__, os.path.join("testdata", "jsondata", "distribute.json"))
        with open(datafile, "rt", encoding="UTF-8") as file:
            projectdatamock.return_value = json.load(file)

        proxystub.set_debug_context("distributedata.py", xmlrpclib.ServerProxy, False)

        data = pypidata.get_data("distribute")
        rating = rate(data)

        # build + older versions of setuptools works, later setuptools does not, so
        # we can get two different results here:
        self.assertEqual(
            rating,
            (
                7,
                [
                    "The classifiers should specify what minor versions of Python "
                    "you support as well as what major version.",
                    "You should have three or more owners of the project on PyPI.",
                    "Your Cheese may have spoiled!! The only way to gather metadata from your package was to execute "
                    "a patched setup.py. This indicates that your package is using very old packaging techniques, "
                    "(or that your setup.py isn't executable at all), and Pyroma will soon regard that as a "
                    "complete failure!\nPlease modernize your packaging! If it is already modern, this is a bug.",
                ],
            ),
        )

    @unittest.mock.patch("xmlrpc.client.ServerProxy", proxystub)
    @unittest.mock.patch("pyroma.pypidata._get_project_data")
    def test_complete(self, projectdatamock):
        datafile = resource_filename(__name__, os.path.join("testdata", "jsondata", "complete.json"))
        with open(datafile, "rt", encoding="UTF-8") as file:
            projectdatamock.return_value = json.load(file)

        proxystub.set_debug_context("completedata.py", xmlrpclib.ServerProxy, False)

        data = pypidata.get_data("complete")
        rating = rate(data)

        self.assertEqual(rating, (10, []))


class ProjectDataTest(unittest.TestCase):

    maxDiff = None

    def test_complete(self):
        directory = resource_filename(__name__, os.path.join("testdata", "complete"))

        data = projectdata.get_data(directory)
        self.assertEqual(data, COMPLETE)


class DistroDataTest(unittest.TestCase):

    maxDiff = None

    def test_complete(self):
        directory = resource_filename(__name__, os.path.join("testdata", "distributions"))

        for filename in os.listdir(directory):
            if filename.startswith("complete"):
                data = distributiondata.get_data(os.path.join(directory, filename))
                self.assertEqual(data, COMPLETE)
