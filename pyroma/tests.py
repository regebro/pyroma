import unittest
import os
from pyroma.packagedata import get_data
from pyroma.ratings import rate
from pkg_resources import resource_filename, resource_string

class PackageDataTest(unittest.TestCase):
    
    def test_complete(self):
        directory = resource_filename(
            __name__, os.path.join('testdata', 'complete'))
        long_description = resource_string(
            __name__, os.path.join('testdata', 'complete', 'README.txt'))
        
        data = get_data(directory)
        target = {'name': 'complete',
                  'version': '1.0',
                  'description': 'This is a test package for pyroma.',
                  'long_description': long_description,
                  'classifiers': ['Development Status :: 6 - Mature',
                                  'Operating System :: OS Independent',
                                  'Programming Language :: Python :: 2.6',],
                  'keywords': 'pypi quality example',
                  'author': 'Lennart Regebro',
                  'author_email': 'regebro@gmail.com',
                  'url': 'http://colliberty.com',
                  'license': 'MIT',
                  'packages': ['complete'],
                  'install_requires': ['setuptools', 'external1'],
                  'test_requires': ['external2'], 
                  'setup_requires': ['external3'],
                  'extras_require': dict(test=['external4','external5']),                          
                  'include_package_data': True,
                  'zip_safe': True,
                  'test_suite': "complete",
                  '_imports': set(['unittest', 'external5', 'external2',
                                   'external3', 'external1', 'external4',]
                                  ),
                  }
        self.assertEqual(data, target)

class RatingsTest(unittest.TestCase):
    
    def test_complete(self):
        directory = resource_filename(
            __name__, os.path.join('testdata', 'complete'))
        data = get_data(directory)
        rating = rate(data)
        
        # Should have a perfect score
        self.assertEqual(rating, (10, []))

    def test_minimal(self):
        directory = resource_filename(
            __name__, os.path.join('testdata', 'minimal'))
        data = get_data(directory)
        rating = rate(data)
        
        # Should have a perfect score
        self.assertEqual(rating, (1, [
            'The packages description should be longer than 10 characters', 
            'The packages long_description is quite short', 
            'Your package does not have classifiers data', 
            'You should specify what Python versions you support', 
            'Your package does not have keywords data', 
            'Your package does not have author data', 
            'Your package does not have author_email data', 
            'Your package does not have url data', 
            'Your package does not have license data', 
            "It's not specified if this package is zip_safe or not, which is usually an oversight. You should specify it, as it defaults to True, which you probably do not want.",
            "Setuptools and Distribute support running tests. By specifying a test suite, it's easy to find and run tests both for automated tools and humans.",
            'You did not declare the following dependencies: external1',
        ]))
