import unittest
import os
import xmlrpclib

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
            'install_requires': ['external1', 'external2'],
            'tests_require': ['external3'], 
            'setup_requires': ['setuptools', ],
            'extras_require': dict(test=['external4','external5']),                          
            'include_package_data': True,
            'zip_safe': True,
            'test_suite': "complete",
            #'_imports': set(['unittest', 'external5', 'external2',
                             #'external3', 'external1', 'external4',]
                            #),
            }


_RECORD = True # Set this to true, and it will use the real 

real_server_proxy = xmlrpclib.ServerProxy
    
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
        ]))

    def test_distribute(self):
        try:
            xmlrpclib.ServerProxy = ProxyStub('distributedata.py',
                                              xmlrpclib.ServerProxy,
                                              False)
            
            data = pypidata.get_data('distribute')
            rating = rate(data)
            
            self.assertEqual(rating, (9, [
                'The classifiers should specify what minor versions of Python you support as well as what major version',
            ]))
        finally:
            xmlrpclib.ServerProxy = real_server_proxy
        
class ProjectDataTest(unittest.TestCase):
    
    def test_complete(self):
        directory = resource_filename(
            __name__, os.path.join('testdata', 'complete'))
        
        data = projectdata.get_data(directory)
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

