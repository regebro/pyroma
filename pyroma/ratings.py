# -*- coding: UTF-8 -*-
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

import sys, os
from docutils.core import publish_parts
from docutils.utils import SystemMessage

LEVELS = ["I don't think that's really cheese",
          "Vieux Bologne",
          "Limburger",
          "Gorgonzola",
          "Stilton",
          "Brie",
          "Compté",
          "Jarlsberg",
          "Philadelphia",
          "Cottage Cheese",
          "Your cheese is so fresh most people think it's a cream: Mascarpone"]

class BaseTest(object):
    fatal = False
    
class FieldTest(BaseTest):
    """Tests that a specific field is in the data and is not empty or False"""
    
    def test(self, data):
        return bool(data.get(self.field))
    
    def message(self):
        return ("Your package does not have %s data" % self.field) + (self.fatal and '!' or '.')

class Name(FieldTest):
    fatal = True
    field = 'name'

class Version(FieldTest):    
    fatal = True
    field = 'version'
        
class Description(BaseTest):
    weight = 100
    
    def test(self, data):
        description = data.get('description')
        if not description:
            # No description at all. That's fatal.
            self.fatal = True
        return len(description) > 10
    
    def message(self):
        if self.fatal:
            return 'The package had no description!'
        else:
            return 'The packages description should be longer than 10 characters.'

class LongDescription(BaseTest):    
    weight = 50
    
    def test(self, data):
        return len(data.get('long_description')) > 100
    
    def message(self):
        return 'The packages long_description is quite short.'

class Classifiers(FieldTest):
    weight = 100
    field = 'classifiers'

class PythonVersion(BaseTest):

    def test(self, data):
        self._major_version_specified = False
        
        classifiers = data.get('classifiers', [])
        for classifier in classifiers:
            parts = [p.strip() for p in classifier.split('::')]
            if parts[0] == 'Programming Language' and parts[1] == 'Python':
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
            return "The classifiers should specify what minor versions of "\
                   "Python you support as well as what major version."
        return "You should specify what Python versions you support."
        
        
class Keywords(FieldTest):    
    weight = 20
    field = 'keywords'

class Author(FieldTest):    
    weight = 100
    field = 'author'

class AuthorEmail(FieldTest):    
    weight = 100
    field = 'author_email'

class Url(FieldTest):    
    weight = 20
    field = 'url'

class License(FieldTest):    
    weight = 50
    field = 'license'

class ZipSafe(BaseTest):
    weight = 20
    
    def test(self, data):
        return 'zip_safe' in data
    
    def message(self):
        return "It's not specified if this package is zip_safe or not, which "\
               "is usually an oversight. You should specify it, as it "\
               "defaults to True, which you probably do not want."

class TestSuite(FieldTest):
    weight = 50
    field = 'test_suite'
    
    def message(self):
        return "Setuptools and Distribute support running tests. By "\
               "specifying a test suite, it's easy to find and run tests "\
               "both for automated tools and humans."
    
class RunnableTests(BaseTest):
    
    def test(self, data):
        if not '_testresult' in data:
            return None
        
        if data['_testresult']== 'Failure':
            self.weight = 100
            self._msg = "The test suite failed!"
            return False
        if data['_testresult'] == 'WrongPython':
            self.weight = 0
            self._msg = "This project doesn't support this version of Python; tests not run."
            return False
        if data['_testresult'] == 'NoTests':
            self.weight = 0
            self._msg = "This package is not set up to run tests."
            return False
        if data['_testresult'] == 'Success':
            self.weight = 100
            self._msg = ""
            return True
        self.fatal = True
        self._msg = "Uknown error, this is likely a Pyroma bug."
        return False
    
    def message(self):
        return self._msg

class PackageDocs(BaseTest):
    weight = 0 # Just a recommendation
    
    def test(self, data):
        return data.get('_packages_docs')

    def message(self):
        return "The site packages.python.org is a nice place to put your "\
               "documentation that makes it easy to find, and relieves you of "\
               "hosting it. You should consider using it."
    
class ValidREST(BaseTest):
    
    weight = 50
    
    def test(self, data):
        source = data['long_description']
        try:
            parts = publish_parts(source=source, writer_name='html4css1')
        except SystemMessage, e:
            self._message = e.args[0].strip()
            return False
        
        return True
    
    def message(self):
        return 'Your long_description is not valid ReST: ' + self._message
    
class BusFactor(BaseTest):

    
    def test(self, data):
        if not '_owners' in data:
            self.weight = 0
            return None

        if len(data['_owners']) == 1:
            self.weight = 100
            return False
    
        if len(data['_owners']) == 2:
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
    Description(),
    LongDescription(),
    Classifiers(),
    PythonVersion(),
    Keywords(),
    Author(),
    AuthorEmail(),
    Url(),
    License(),
    ZipSafe(),
    TestSuite(),
    RunnableTests(),
    PackageDocs(),
    ValidREST(),
    BusFactor(),
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
            if test.fatal:
                fatality = True
            else:
                bad += test.weight
                fails.append(test.message())
        elif res is True:
            if not test.fatal:
                good += test.weight
    # If res is None, it's ignored. 
    if fatality:
        # A fatal tests failed. That means we give a 0 rating:
        return 0, fails
    # Multiply good by 9, and add 1 to get a rating between 
    # 1: All non-fatal tests failed.
    # 10: All tests succeeded.
    return (good*9)//(good+bad)+1, fails
