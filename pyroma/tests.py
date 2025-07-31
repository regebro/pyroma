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
    "metadata-version": "2.4",
    "name": "complete",
    "version": "1.0.dev1",
    "summary": "This is a test package for pyroma.",
    "description": long_description,
    "classifier": [
        "Development Status :: 6 - Mature",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "License :: OSI Approved :: MIT License",
    ],
    "dynamic": [
        "author",
        "author-email",
        "classifier",
        "description",
        "home-page",
        "keywords",
        "license",
        "project-url",
        "requires-dist",
        "requires-python",
        "summary",
    ],
    "keywords": "pypi,quality,example",
    "author": "Lennart Regebro",
    "author-email": "regebro@gmail.com",
    "home-page": "https://github.com/regebro/pyroma",
    "project-url": "Source Code, https://github.com/regebro/pyroma",
    "requires-dist": "zope.event",
    "requires-python": ">=2.6",
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

    def _get_file_rating(self, dirname, skip_tests=None):
        directory = resource_filename(__name__, os.path.join("testdata", dirname))
        data = projectdata.get_data(directory)
        return rate(data, skip_tests)

    def test_complete(self):
        rating = self._get_file_rating("complete")
        # Should have a perfect score
        self.assertEqual(rating, (10, []))

    def test_setup_config(self):
        rating = self._get_file_rating("setup_config")
        self.assertEqual(
            rating,
            (
                9,
                [
                    "Your project does not have a pyproject.toml file, which is highly recommended.\n"
                    "You probably want to create one with the following configuration:\n\n"
                    "    [build-system]\n"
                    '    requires = ["setuptools>=42"]\n'
                    '    build-backend = "setuptools.build_meta"\n',
                ],
            ),
        )

    def test_only_config(self):
        # In version 5, this is now an error, as there is no legacy setup.py,
        # nor a modern pyproject.toml.
        rating = self._get_file_rating("only_config")

        self.assertEqual(
            rating,
            (
                5,
                [
                    "You seem to neither have a setup.py, nor a pyproject.toml, only setup.cfg.\n"
                    "This makes it unclear how your project should be built, and some packaging "
                    "tools may fail.",
                    "Your project does not have a pyproject.toml file, which is highly "
                    "recommended.\n"
                    "You probably want to create one with the following configuration:\n\n"
                    "    [build-system]\n"
                    '    requires = ["setuptools>=42"]\n'
                    '    build-backend = "setuptools.build_meta"\n',
                    "Specifying both a License-Expression and license classifiers is ambiguous, "
                    "deprecated, and may be rejected by package indices.",
                    "Check-manifest returned errors",
                ],
            ),
        )

    def test_skip_tests(self):
        # Find all errors
        all_errors = self._get_file_rating("lacking")[1]

        fewer_errors = self._get_file_rating(
            "lacking", skip_tests=["PythonRequiresVersion", "Description", "Summary", "Classifiers"]
        )[1]

        self.assertEqual(len(all_errors), 13)
        # Errors have been skipped!
        self.assertEqual(len(fewer_errors), 9)

    def test_pep517(self):
        rating = self._get_file_rating("pep517")
        self.assertEqual(
            rating,
            (
                10,
                [],
            ),
        )

    def test_pep621(self):
        rating = self._get_file_rating("pep621")
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
                    "The package's Summary should be longer than 10 characters.",
                    "The package's Description is quite short.",
                    "Your package does not have classifier data.",
                    "The classifiers should specify what Python versions you support.",
                    "You should specify what Python versions you support with " "the 'Requires-Python' metadata.",
                    "Your package does not have keywords data.",
                    "Your package does not have author data.",
                    "Your package does not have author-email data.",
                    "Your package should have a 'url' field with a link to the project home page, or a "
                    "'project_urls' field, with a dictionary of links, or both.",
                    "Your package does neither have a license field nor any license classifiers.",
                    "Specifying a development status in the classifiers gives users "
                    "a hint of how stable your software is.",
                    "Check-manifest returned errors",
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
                    "Your project does not have a pyproject.toml file, which is highly recommended.\n"
                    "You probably want to create one with the following configuration:\n\n"
                    "    [build-system]\n"
                    '    requires = ["setuptools>=42"]\n'
                    '    build-backend = "setuptools.build_meta"\n',
                    "The package had no Summary!",
                    "The package's Description is quite short.",
                    "Your package does not have classifier data.",
                    "The classifiers should specify what Python versions you support.",
                    "You should specify what Python versions you support with " "the 'Requires-Python' metadata.",
                    "Your package does not have keywords data.",
                    "Your package does not have author data.",
                    "Your package does not have author-email data.",
                    "Your package should have a 'url' field with a link to the project home page, or a "
                    "'project_urls' field, with a dictionary of links, or both.",
                    "Your package does neither have a license field nor any license classifiers.",
                    "Your Description is not valid ReST: \n<string>:1: (WARNING/2) Inline literal "
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
                3,
                [
                    "The package's Summary should be longer than 10 characters.",
                    "The package's Description is quite short.",
                    "Your package does not have classifier data.",
                    "The classifiers should specify what Python versions you support.",
                    "You should specify what Python versions you support with " "the 'Requires-Python' metadata.",
                    "Your package does not have keywords data.",
                    "Your package does not have author data.",
                    "Your package does not have author-email data.",
                    "Your package should have a 'url' field with a link to the project home page, or a "
                    "'project_urls' field, with a dictionary of links, or both.",
                    "Your package does neither have a license field nor any license classifiers.",
                    "Specifying a development status in the classifiers gives users "
                    "a hint of how stable your software is.",
                ],
            ),
        )

    def test_private_classifier(self):
        rating = self._get_file_rating("private_classifier")
        self.assertEqual(rating, (10, []))

    def test_markdown(self):
        # Markdown and text shouldn't get ReST errors
        testdata = COMPLETE.copy()
        testdata["description"] = "# Broken ReST\n\n``Valid  Markdown\n"
        testdata["description-content-type"] = "text/markdown"

        rating = rate(testdata)
        self.assertEqual(rating, (9, ["The package's Description is quite short."]))

        testdata["description-content-type"] = "text/plain"
        rating = rate(testdata)
        self.assertEqual(rating, (9, ["The package's Description is quite short."]))


class PyPITest(unittest.TestCase):
    maxDiff = None

    @unittest.mock.patch("xmlrpc.client.ServerProxy", proxystub)
    @unittest.mock.patch("pyroma.pypidata._get_project_data")
    @unittest.mock.patch("requests.get")
    def test_complete(self, requestmock, projectdatamock):
        datafile = resource_filename(__name__, os.path.join("testdata", "jsondata", "complete.json"))
        with open(datafile, encoding="UTF-8") as file:
            projectdatamock.return_value = json.load(file)

        srcfile = resource_filename(__name__, os.path.join("testdata", "distributions", "complete-1.0.dev1.tar.gz"))
        with open(srcfile, "rb") as file:
            requestmock.return_value = unittest.mock.Mock()
            requestmock.return_value.content = file.read()

        proxystub.set_debug_context("completedata.py", xmlrpclib.ServerProxy, False)
        data = pypidata.get_data("complete")
        rating = rate(data)

        self.assertEqual(rating, (10, []))


class ProjectDataTest(unittest.TestCase):
    maxDiff = None

    def test_complete(self):
        directory = resource_filename(__name__, os.path.join("testdata", "complete"))

        data = projectdata.get_data(directory)
        del data["_path"]  # This changes, so I just ignore it
        self.assertEqual(data, COMPLETE)

    def test_installed(self):
        # pyroma must be installed in the test environment.
        data = projectdata.installed_metadata("pyroma")

        # Verify some key metadata
        self.assertEqual(data["name"], "pyroma")
        self.assertEqual(data["summary"], "Test your project's packaging friendliness")
        self.assertEqual(data["classifier"], [
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Programming Language :: Python :: 3.13",
            "Programming Language :: Python :: 3.14",
            "Programming Language :: Python :: 3 :: Only",
            "Programming Language :: Python :: Implementation :: CPython",
            "Programming Language :: Python :: Implementation :: PyPy",
        ])
        self.assertEqual(data["keywords"], "pypi,quality,testing")
        self.assertEqual(data["author"], "Lennart Regebro")
        self.assertEqual(data["author-email"], "regebro@gmail.com")
        self.assertEqual(data["home-page"], "https://github.com/regebro/pyroma")
        self.assertEqual(data["license"], "MIT")
        self.assertEqual(data["license-file"], "LICENSE.txt")
        self.assertEqual(data["project-url"], "Source Code, https://github.com/regebro/pyroma")
        self.assertEqual(data["provides-extra"], "test")
        self.assertEqual(data["requires-python"], ">=3.9")


class DistroDataTest(unittest.TestCase):
    maxDiff = None

    def test_complete(self):
        directory = resource_filename(__name__, os.path.join("testdata", "distributions"))

        for filename in os.listdir(directory):
            if filename.startswith("complete"):
                data = distributiondata.get_data(os.path.join(directory, filename))
                self.assertEqual(data, COMPLETE)
