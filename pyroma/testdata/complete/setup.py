from setuptools import setup, find_packages
import sys, os

version = '1.0'

setup(name='complete',
      version=version,
      description="This is a test package for pyroma.",
      long_description=open("README.txt").read(),
      classifiers=['Development Status :: 6 - Mature',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2.6',],
      keywords='pypi quality example',
      author='Lennart Regebro',
      author_email='regebro@gmail.com',
      url='http://colliberty.com',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      install_requires=['external1', 'external2'],
      tests_require=['external3'],
      setup_requires=['setuptools'],
      extras_require=dict(test=['external4','external5']),
      zip_safe=True,
      test_suite="complete",
      )
