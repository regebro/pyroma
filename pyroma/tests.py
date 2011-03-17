import unittest
import os
import xmlrpclib
import urlparse
import urllib
import sys

from pyroma import projectdata, distributiondata, pypidata
from pyroma.ratings import rate
from pkg_resources import resource_filename, resource_string

long_description = resource_string(
    __name__, os.path.join('testdata', 'complete', 'README.txt'))
if not isinstance(long_description, str):
    long_description = long_description.decode()

COMPLETE = {'name': 'complete',
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
            'install_requires': ['zope.event'],
            'tests_require': ['six'],
            'setup_requires': ['setuptools'],
            'include_package_data': True,
            'zip_safe': True,
            'test_suite': "complete",
            '_testresult': 'Success',
            }


class FakeResponse(object):
    def __init__(self, responsecode, filename=None):
        self.filename = filename
        if sys.version > '2.5':
            # 2.5 and lower doesn't have the code attribute.
            # The test should fail on Python 2.5.
            self.code = responsecode
            
    def read(self):
        return open(self.filename, 'rb').read()

def urlopenstub(url):
    filename = [x for x in url.split('/') if x][-1]
    if url.startswith('http://packages.python.org/'):
        # Faking the docs:
        if filename in ('distribute', 'complete',):
            return FakeResponse(200)
        else:
            # This package doesn't have docs on packages.python.org:
            return FakeResponse(404)

    if url.startswith('http://pypi.python.org/pypi'):
        # Faking PyPI package
        datafile = resource_filename(
            __name__, os.path.join('testdata', 'xmlrpcdata', filename+'.html'))
        return FakeResponse(200, datafile)
        
        
    if url.startswith('http://pypi.python.org/packages'):
        # Faking PyPI file downloads
        datafile = resource_filename(
            __name__, os.path.join('testdata', 'distributions', filename))
        return FakeResponse(200, datafile)
    
    raise ValueError("Don't know how to stub " + url)

class ProxyStub(object):
    def __init__(self, dataname, real_class, developmode):        
        filename = resource_filename(
            __name__, os.path.join('testdata', 'xmlrpcdata', dataname))
        data = {}
        exec(open(filename, 'rt').read(), None, data)
        self.args = data['args']
        self.kw = data['kw']
        self._data = data['data']

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
                raise AttributeError('ProxyStub unkown method ' + name)
            print
            print "== ProxyStub unknown method =="
            print name, ':', args, kw
            result = getattr(self._real, name)(*args, **kw)
            print "Result :"
            print result
            return result
            
        return _proxy_method

    def __getattr__(self, attr):
        if attr in self._data:
            return self._make_proxy(attr)
        return self._make_unknown_proxy(attr)
    
        
class RatingsTest(unittest.TestCase):
    
    def test_complete(self):
        directory = resource_filename(
            __name__, os.path.join('testdata', 'complete'))
        data = projectdata.get_data(directory)
        rating = rate(data)
        
        # Should have a perfect score
        self.assertEqual(rating, (10, []))

    def test_minimal(self):
        directory = resource_filename(
            __name__, os.path.join('testdata', 'minimal'))
        data = projectdata.get_data(directory)
        rating = rate(data)
        
        self.assertEqual(rating, (1, [
            'The packages description should be longer than 10 characters.', 
            'The packages long_description is quite short.', 
            'Your package does not have classifiers data.', 
            'You should specify what Python versions you support.', 
            'Your package does not have keywords data.', 
            'Your package does not have author data.', 
            'Your package does not have author_email data.', 
            'Your package does not have url data.', 
            'Your package does not have license data.', 
            "It's not specified if this package is zip_safe or not, which is usually an oversight. You should specify it, as it defaults to True, which you probably do not want.",
            "Setuptools and Distribute support running tests. By specifying a test suite, it's easy to find and run tests both for automated tools and humans.",
            'This package is not set up to run tests.',
        ]))

class PyPITest(unittest.TestCase):
        
    def test_distribute(self):
        real_urlopen = urllib.urlopen
        real_server_proxy = xmlrpclib.ServerProxy
        try:
            xmlrpclib.ServerProxy = ProxyStub('distributedata.py',
                                              xmlrpclib.ServerProxy,
                                              False)
            urllib.urlopen = urlopenstub
            data = pypidata.get_data('distribute')
            rating = rate(data)
            
            self.assertEqual(rating, (9, [
                'The classifiers should specify what minor versions of Python you support as well as what major version.',
                "This project doesn't support this version of Python; tests not run.",
                'You should have three or more owners of the project on PyPI.'
            ]))
        finally:
            xmlrpclib.ServerProxy = real_server_proxy
            urllib.urlopen = real_urlopen

    def test_complete(self):
        real_urlopen = urllib.urlopen
        real_server_proxy = xmlrpclib.ServerProxy
        try:
            xmlrpclib.ServerProxy = ProxyStub('completedata.py',
                                              xmlrpclib.ServerProxy,
                                              False)            
            urllib.urlopen = urlopenstub
            data = pypidata.get_data('complete')
            rating = rate(data)
            
            self.assertEqual(rating, (10, []))
        finally:
            xmlrpclib.ServerProxy = real_server_proxy
            urllib.urlopen = real_urlopen
            
class ProjectDataTest(unittest.TestCase):
    
    def test_complete(self):
        directory = resource_filename(
            __name__, os.path.join('testdata', 'complete'))
        
        data = projectdata.get_data(directory)
        # The path is dynamic, and needs not be tested anyway:
        self.assertEqual(data, COMPLETE)


class DistroDataTest(unittest.TestCase):
    
    def test_complete(self):
        directory = resource_filename(
            __name__, os.path.join('testdata', 'distributions'))

        for filename in os.listdir(directory):
            if filename.startswith('complete'):
                data = distributiondata.get_data(os.path.join(directory,
                                                              filename))
                self.assertEqual(data, COMPLETE)
