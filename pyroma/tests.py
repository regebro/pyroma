import io

import json
import os
import unittest

import unittest.mock
from pathlib import Path

import pyroma
from xmlrpc import client as xmlrpclib

from pyroma import projectdata, distributiondata, pypidata
from pyroma.ratings import rate

TESTDATA_DIR = Path(__file__).parent / "testdata"
long_description = (TESTDATA_DIR / "complete" / "README.txt").read_text(encoding="UTF-8")
# Translate newlines to universal format
long_description = io.StringIO(long_description, newline=None).read()

COMPLETE = {
    "metadata-version": "2.4",
    "name": "complete",
    "version": "1.0.dev1",
    "summary": "This is a test package for pyroma.",
    "description": long_description,
    "description-content-type": "text/plain",
    "classifier": [
        "Development Status :: 6 - Mature",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
    ],
    "dynamic": "license-file",
    "keywords": "pypi,quality,example",
    "author-email": "Lennart Regebro <regebro@gmail.com>",
    "project-url": [
        "repository, https://github.com/regebro/pyroma",
        "homepage, https://github.com/regebro/pyroma",
    ],
    "requires-dist": "zope.event",
    "requires-python": ">=2.6",
    "license-expression": "MIT",
    "license-file": "LICENSE.txt",
}


class ProxyStub:
    def set_debug_context(self, dataname, real_class, developmode):
        filename = TESTDATA_DIR / "xmlrpcdata" / dataname
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
        directory = TESTDATA_DIR / dirname
        data = projectdata.get_data(directory)
        return rate(data, skip_tests)

    def test_complete(self):
        data = projectdata.get_data(TESTDATA_DIR / "complete")
        rating = rate(data)
        # Should have a perfect score
        self.assertEqual(rating, (10, []))

    def test_setup_config(self):
        rating = self._get_file_rating("setup_config")
        self.assertEqual(
            rating,
            (
                8,
                [
                    "Your project does not have a pyproject.toml file, which is highly recommended.\n"
                    "You probably want to create one with the following configuration:\n\n"
                    "    [build-system]\n"
                    '    requires = ["setuptools>=42"]\n'
                    '    build-backend = "setuptools.build_meta"\n'
                    "See https://packaging.python.org for more information on how to package your project.",
                    "Using license classifiers is deprecated in favour of the license-expression field.",
                    "The metadata field 'home-page' is deprecated; use 'project-url' instead.",
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
                    "tools may fail."
                    "See https://packaging.python.org for more information on how to package your project.",
                    "Your project does not have a pyproject.toml file, which is highly "
                    "recommended.\n"
                    "You probably want to create one with the following configuration:\n\n"
                    "    [build-system]\n"
                    '    requires = ["setuptools>=42"]\n'
                    '    build-backend = "setuptools.build_meta"\n'
                    "See https://packaging.python.org for more information on how to package your project.",
                    "Specifying both a License-Expression and license classifiers is ambiguous, "
                    "deprecated, and may be rejected by package indices.",
                    "The metadata field 'home-page' is deprecated; use 'project-url' instead.",
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
        self.assertGreaterEqual(rating[0], 9)

    def test_pep621(self):
        rating = self._get_file_rating("pep621")
        self.assertGreaterEqual(rating[0], 9)

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
                    "The classifiers should specify what Python versions you support."
                    "You can find the list of standard classifiers here: https://pypi.org/classifiers/",
                    "You should specify what Python versions you support with " "the 'Requires-Python' metadata.",
                    "Your package does not have keywords data.",
                    "Your package does not have author data.",
                    "Your package does not have author-email data.",
                    "Your package should have a 'url' field with a link to the project home page, or a "
                    "'project_urls' field, with a dictionary of links, or both.",
                    "You should specify a license for your package with the 'License-Expression' field. See "
                    "https://packaging.python.org/en/latest/specifications/core-metadata/#license-expression "
                    "for more information.",
                    "Specifying a development status in the classifiers gives users "
                    "a hint of how stable your software is. See https://pypi.org/classifiers/",
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
                    '    build-backend = "setuptools.build_meta"\n'
                    "See https://packaging.python.org for more information on how to package your project.",
                    "The package had no Summary!",
                    "The package's Description is quite short.",
                    "Your package does not have classifier data.",
                    "The classifiers should specify what Python versions you support."
                    "You can find the list of standard classifiers here: https://pypi.org/classifiers/",
                    "You should specify what Python versions you support with " "the 'Requires-Python' metadata.",
                    "Your package does not have keywords data.",
                    "Your package does not have author data.",
                    "Your package does not have author-email data.",
                    "Your package should have a 'url' field with a link to the project home page, or a "
                    "'project_urls' field, with a dictionary of links, or both.",
                    "You should specify a license for your package with the 'License-Expression' field. See "
                    "https://packaging.python.org/en/latest/specifications/core-metadata/#license-expression "
                    "for more information.",
                    "Your Description is not valid ReST: \n<string>:1: (WARNING/2) Inline literal "
                    "start-string without end-string.",
                    "Specifying a development status in the classifiers gives users "
                    "a hint of how stable your software is. See https://pypi.org/classifiers/",
                ],
            ),
        )

    def test_custom_test(self):
        rating = self._get_file_rating("custom_test")

        self.assertEqual(
            rating,
            (
                4,
                [
                    "The package's Summary should be longer than 10 characters.",
                    "The package's Description is quite short.",
                    "Your package does not have classifier data.",
                    "The classifiers should specify what Python versions you support."
                    "You can find the list of standard classifiers here: https://pypi.org/classifiers/",
                    "You should specify what Python versions you support with " "the 'Requires-Python' metadata.",
                    "Your package does not have keywords data.",
                    "Your package does not have author data.",
                    "Your package does not have author-email data.",
                    "Your package should have a 'url' field with a link to the project home page, or a "
                    "'project_urls' field, with a dictionary of links, or both.",
                    "You should specify a license for your package with the 'License-Expression' field. See "
                    "https://packaging.python.org/en/latest/specifications/core-metadata/#license-expression "
                    "for more information.",
                    "Specifying a development status in the classifiers gives users "
                    "a hint of how stable your software is. See https://pypi.org/classifiers/",
                ],
            ),
        )

    def test_private_classifier(self):
        rating = self._get_file_rating("private_classifier")
        self.assertGreaterEqual(rating[0], 9)

    def test_invalid_pyproject(self):
        # Use valid metadata so we exercise the rating check itself,
        # then point _path to a fixture with an invalid pyproject.toml.
        testdata = COMPLETE.copy()
        testdata["_path"] = TESTDATA_DIR / "invalid_pyproject"

        rating = rate(testdata)
        self.assertLess(rating[0], 10)
        self.assertTrue(any("pyproject.toml is invalid" in msg for msg in rating[1]))

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

    def test_deprecated_metadata_field_warning(self):
        testdata = COMPLETE.copy()
        testdata.pop("project-url", None)
        testdata["home-page"] = "https://example.com"

        rating = rate(testdata)

        self.assertTrue(
            any("The metadata field 'home-page' is deprecated; use 'project-url' instead." in msg for msg in rating[1])
        )

    def test_deprecated_license_warning_respects_metadata_version(self):
        old_metadata = COMPLETE.copy()
        old_metadata["metadata-version"] = "2.3"
        old_metadata["license"] = "MIT"
        old_metadata.pop("license-expression", None)

        old_rating = rate(old_metadata)
        self.assertFalse(any("The metadata field 'license' is deprecated" in msg for msg in old_rating[1]))

        new_metadata = COMPLETE.copy()
        new_metadata["metadata-version"] = "2.4"
        new_metadata["license"] = "MIT"
        new_metadata.pop("license-expression", None)

        new_rating = rate(new_metadata)
        self.assertTrue(any("The metadata field 'license' is deprecated" in msg for msg in new_rating[1]))


class PyPITest(unittest.TestCase):
    maxDiff = None

    @unittest.mock.patch("xmlrpc.client.ServerProxy", proxystub)
    @unittest.mock.patch("pyroma.pypidata._get_project_data")
    @unittest.mock.patch("requests.get")
    def test_complete(self, requestmock, projectdatamock):
        datafile = TESTDATA_DIR / "jsondata" / "complete.json"
        with open(datafile, encoding="UTF-8") as file:
            projectdatamock.return_value = json.load(file)

        srcfile = TESTDATA_DIR / "distributions" / "complete-1.0.dev1.tar.gz"
        with open(srcfile, "rb") as file:
            requestmock.return_value = unittest.mock.Mock()
            requestmock.return_value.content = file.read()

        proxystub.set_debug_context("completedata.py", xmlrpclib.ServerProxy, False)
        data = pypidata.get_data("complete")
        rating = rate(data)

        self.assertEqual(rating, (10, []))

    @unittest.mock.patch("pyroma.pypidata.requests.get")
    def test_get_project_data_custom_index_url(self, requestmock):
        requestmock.return_value = unittest.mock.Mock()
        requestmock.return_value.ok = True
        requestmock.return_value.status_code = 200
        requestmock.return_value.json.return_value = {}

        pypidata._get_project_data("internalpkg", index_url="https://packages.example.com")

        requestmock.assert_called_once_with("https://packages.example.com/pypi/internalpkg/json")

    @unittest.mock.patch("pyroma.pypidata.requests.get")
    def test_get_project_data_custom_index_url_with_pypi_path(self, requestmock):
        requestmock.return_value = unittest.mock.Mock()
        requestmock.return_value.ok = True
        requestmock.return_value.status_code = 200
        requestmock.return_value.json.return_value = {}

        pypidata._get_project_data("internalpkg", index_url="https://packages.example.com/pypi")

        requestmock.assert_called_once_with("https://packages.example.com/pypi/internalpkg/json")

    @unittest.mock.patch("pyroma.pypidata.xmlrpc.client.ServerProxy")
    @unittest.mock.patch("pyroma.pypidata._get_project_data")
    def test_get_data_custom_index_url_uses_xmlrpc_endpoint(self, projectdatamock, proxymock):
        projectdatamock.return_value = {
            "info": {"name": "internalpkg", "version": "1.2.3"},
            "releases": {"1.2.3": []},
        }

        proxymock.return_value.__enter__.return_value.package_roles.return_value = [("Owner", "dev1")]

        data = pypidata.get_data("internalpkg", index_url="https://packages.example.com")

        self.assertEqual(data["_owners"], ["dev1"])
        proxymock.assert_called_once_with("https://packages.example.com/pypi")

    @unittest.mock.patch("pyroma.ratings.rate")
    @unittest.mock.patch("pyroma.pypidata.get_data")
    def test_run_forwards_custom_index_url(self, datamock, ratemock):
        datamock.return_value = {"name": "internalpkg"}
        ratemock.return_value = (10, [])

        result = pyroma.run("pypi", "internalpkg", quiet=True, index_url="https://packages.example.com")

        self.assertEqual(result, 10)
        datamock.assert_called_once_with("internalpkg", index_url="https://packages.example.com")


class ProjectDataTest(unittest.TestCase):
    maxDiff = None

    def test_complete(self):
        directory = TESTDATA_DIR / "complete"

        data = projectdata.get_data(directory)
        del data["_path"]  # This changes, so I just ignore it

        self.assertEqual(data, COMPLETE)


class DistroDataTest(unittest.TestCase):
    maxDiff = None

    def test_complete(self):
        directory = TESTDATA_DIR / "distributions"

        for filename in os.listdir(directory):
            if filename.startswith("complete"):
                data = distributiondata.get_data(directory / filename)
                self.assertEqual(data, COMPLETE)
