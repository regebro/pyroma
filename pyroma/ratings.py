# This is a collection of "tests" done on the package data. The resut of the
# tests is used to give the package a rating.
#
# Each test has a couple of attributes. Both attributes are checked only after
# the test is performed so the test can choose to set the attributes dependning
# on the severity of the failure.
#
#     fatal:    If set to True, the failure of this test will cause the
#               package to achieve the rating of 1, which is minimum
#     weight:   The relative importance of the test.
#               If the test has fatal set to True this is ignored.
#
# Tests have two methods:
#     test(data): Performs the test on the given data. Returns True for pass
#                 False for fail and None for not applicable (meaning it will
#                 not be counted).
import io
import re
from docutils.core import publish_parts
from docutils.utils import SystemMessage
from pyroma.classifiers import CLASSIFIERS, CODE_LICENSES

LEVELS = [
    "This cheese seems to contain no dairy products",
    "Vieux Bologne",
    "Limburger",
    "Gorgonzola",
    "Stilton",
    "Brie",
    "Comté",
    "Jarlsberg",
    "Philadelphia",
    "Cottage Cheese",
    "Your cheese is so fresh most people think it's a cream: Mascarpone",
]


class BaseTest:
    fatal = False


class FieldTest(BaseTest):
    """Tests that a specific field is in the data and is not empty or False"""

    def test(self, data):
        return bool(data.get(self.field))

    def message(self):
        return (f"Your package does not have {self.field} data") + (
            self.fatal and "!" or "."
        )


class Name(FieldTest):
    fatal = True
    field = "name"


class Version(FieldTest):
    fatal = True
    field = "version"


class VersionIsString(BaseTest):
    weight = 50

    def test(self, data):
        # Check that the version is a string
        version = data.get("version")
        return isinstance(version, str)

    def message(self):
        return "The version number should be a string."


PEP386_RE = re.compile(
    r"""
    ^
    (?P<version>\d+\.\d+)          # minimum 'N.N'
    (?P<extraversion>(?:\.\d+)*)   # any number of extra '.N' segments
    (?:
        (?P<prerel>[abc]|rc)       # 'a'=alpha, 'b'=beta, 'c'=release candidate
                                   # 'rc'= alias for release candidate
        (?P<prerelversion>\d+(?:\.\d+)*)
    )?
    (?P<postdev>(\.post(?P<post>\d+))?(\.dev(?P<dev>\d+))?)?
    $""",
    re.VERBOSE | re.IGNORECASE,
)


PEP440_RE = re.compile(
    r"""^
    v?
    (?:
        (?:(?P<epoch>[0-9]+)!)?                           # epoch
        (?P<release>[0-9]+(?:\.[0-9]+)*)                  # release segment
        (?P<pre>                                          # pre-release
            [-_\.]?
            (?P<pre_l>(a|b|c|rc|alpha|beta|pre|preview))
            [-_\.]?
            (?P<pre_n>[0-9]+)?
        )?
        (?P<post>                                         # post release
            (?:-(?P<post_n1>[0-9]+))
            |
            (?:
                [-_\.]?
                (?P<post_l>post|rev|r)
                [-_\.]?
                (?P<post_n2>[0-9]+)?
            )
        )?
        (?P<dev>                                          # dev release
            [-_\.]?
            (?P<dev_l>dev)
            [-_\.]?
            (?P<dev_n>[0-9]+)?
        )?
    )
    (?:\+(?P<local>[a-z0-9]+(?:[-_\.][a-z0-9]+)*))?       # local version
$""",
    re.VERBOSE | re.IGNORECASE,
)


class PEPVersion(BaseTest):
    weight = 50
    pep386 = False

    def test(self, data):
        # Check that the version number complies to PEP-386:
        version = data.get("version")
        self.pep386 = False
        if PEP386_RE.search(str(version)) is not None:
            # Matches the old PEP386
            self.weight = 10
            self.pep386 = True
        match = PEP440_RE.search(str(version))
        return match is not None

    def message(self):
        if self.pep386:
            return "The package's version number complies only with PEP-386 and not PEP-440."
        return "The package's version number does not comply with PEP-386 or PEP-440."


class Description(BaseTest):
    weight = 100

    def test(self, data):
        description = data.get("description")
        if not description:
            # No description at all. That's fatal.
            self.fatal = True
            return False
        self.fatal = False
        return len(description) > 10

    def message(self):
        if self.fatal:
            return "The package had no description!"
        else:
            return "The package's description should be longer than " "10 characters."


class LongDescription(BaseTest):
    weight = 50

    def test(self, data):
        long_description = data.get("long_description", "")
        if not isinstance(long_description, str):
            long_description = ""
        return len(long_description) > 100

    def message(self):
        return "The package's long_description is quite short."


class Classifiers(FieldTest):
    weight = 100
    field = "classifiers"


class ClassifierVerification(BaseTest):
    weight = 20

    def test(self, data):
        self._incorrect = []
        classifiers = data.get("classifiers", [])
        for classifier in classifiers:
            if classifier not in CLASSIFIERS:
                self._incorrect.append(classifier)
        if self._incorrect:
            return False
        return True

    def message(self):
        err = "\n".join(self._incorrect)
        return "Some of your classifiers are not standard classifiers:\n" + err


class PythonVersion(BaseTest):
    def test(self, data):
        self._major_version_specified = False

        classifiers = data.get("classifiers", [])
        for classifier in classifiers:
            parts = [p.strip() for p in classifier.split("::")]
            if parts[0] == "Programming Language" and parts[1] == "Python":
                if len(parts) == 2:
                    # Specified Python, but no version.
                    continue
                version = parts[2]
                try:
                    float(version)
                except ValueError:
                    # Not a proper Python version
                    continue
                try:
                    int(version)
                except ValueError:
                    # It's a valid float, but not a valid int. Hence it's
                    # something like "2.7" or "3.3" but not just "2" or "3".
                    # This is a good specification, and we only need one.
                    # Set weight to 100 and finish.
                    self.weight = 100
                    return True

                # It's a valid int, meaning it specified "2" or "3".
                self._major_version_specified = True

        # There was some sort of failure:
        if self._major_version_specified:
            # Python 2 or 3 was specified but no more detail than that:
            self.weight = 25
        else:
            # No Python version specified at all:
            self.weight = 100
        return False

    def message(self):
        if self._major_version_specified:
            return (
                "The classifiers should specify what minor versions of "
                "Python you support as well as what major version."
            )
        return "You should specify what Python versions you support."


class Keywords(FieldTest):
    weight = 20
    field = "keywords"


class Author(FieldTest):
    weight = 100
    field = "author"


class AuthorEmail(FieldTest):
    weight = 100
    field = "author_email"


class Url(BaseTest):
    weight = 20

    def test(self, data):
        return bool(data.get("url")) or bool(data.get("project_urls"))

    def message(self):
        return (
            "Your package should have a 'url' field with a link to the "
            "project home page, or a 'project_urls' field, with a "
            "dictionary of links, or both."
        )


class Licensing(BaseTest):
    weight = 50

    def test(self, data):
        license = data.get("license")
        classifiers = data.get("classifiers", [])
        licenses = set()
        for classifier in classifiers:
            parts = [p.strip() for p in classifier.split("::")]
            if parts[0] == "License":
                # license classifier exist
                licenses.add(classifier)

        if not license and not licenses:
            self._message = (
                "Your package does neither have a license field "
                "nor any license classifiers."
            )
            return False

        if license in CODE_LICENSES:
            if not CODE_LICENSES[license].intersection(licenses):
                self._message = (
                    f"The license '{license}' specified is not listed in "
                    "your classifiers."
                )
                return False

        return True

    def message(self):
        return self._message


class DevStatusClassifier(BaseTest):
    weight = 20

    def test(self, data):
        classifiers = data.get("classifiers", [])
        for classifier in classifiers:
            parts = [p.strip() for p in classifier.split("::")]
            if parts[0] == "Development Status":
                # license classifier exist
                return True
        return False

    def message(self):
        return (
            "Specifying a development status in the classifiers gives "
            "users a hint of how stable your software is."
        )


class SDist(BaseTest):
    weight = 100

    def test(self, data):
        if "_has_sdist" not in data:
            # We aren't checking on PyPI
            self.weight = 0
            return None
        return data["_has_sdist"]

    def message(self):
        return (
            "You have no source distribution on the Cheeseshop. "
            "Uploading the source distribution to the Cheeseshop ensures "
            "maximum availability of your package."
        )


class ValidREST(BaseTest):

    weight = 50

    def test(self, data):
        content_type = data.get("long_description_content_type", None)
        if content_type in ("text/plain", "text/markdown"):
            # These can't fail. Markdown will just assume everything
            # it doesn't understand is plain text.
            return True

        # This should be ReStructuredText
        source = data.get("long_description", "")
        stream = io.StringIO()
        settings = {"warning_stream": stream}

        try:
            publish_parts(
                source=source, writer_name="html4css1", settings_overrides=settings
            )
        except SystemMessage as e:
            self._message = e.args[0]
        errors = stream.getvalue().strip()
        if not errors:
            return True

        self._message = "\n" + errors
        return False

    def message(self):
        return "Your long_description is not valid ReST: " + self._message


class BusFactor(BaseTest):
    def test(self, data):
        if "_owners" not in data:
            self.weight = 0
            return None

        if len(data.get("_owners", [])) == 1:
            self.weight = 100
            return False

        if len(data.get("_owners", [])) == 2:
            self.weight = 50
            return False

        # Three or more, that's good.
        self.weight = 100
        return True

    def message(self):
        return "You should have three or more owners of the project on PyPI."


ALL_TESTS = [
    Name(),
    Version(),
    VersionIsString(),
    PEPVersion(),
    Description(),
    LongDescription(),
    Classifiers(),
    ClassifierVerification(),
    PythonVersion(),
    Keywords(),
    Author(),
    AuthorEmail(),
    Url(),
    Licensing(),
    SDist(),
    ValidREST(),
    BusFactor(),
    DevStatusClassifier(),
]


def rate(data):
    if not data:
        # No data was gathered. Fail:
        return (0, ["I couldn't find any package data"])
    fails = []
    good = 0
    bad = 0
    fatality = False
    for test in ALL_TESTS:
        res = test.test(data)
        if res is False:
            fails.append(test.message())
            if test.fatal:
                fatality = True
            else:
                bad += test.weight
        elif res is True:
            if not test.fatal:
                good += test.weight
    # If res is None, it's ignored.
    if fatality:
        # A fatal test failed. That means we give a 0 rating:
        return 0, fails
    # Multiply good by 9, and add 1 to get a rating between
    # 1: All non-fatal tests failed.
    # 10: All tests succeeded.
    return (good * 9) // (good + bad) + 1, fails
