from setuptools import setup, find_packages

version = '2.1'

setup(name='pyroma',
      version=version,
      description="Test your project's packaging friendliness",
      long_description=open("README.txt", 'rt').read() + "\n" +
      open("HISTORY.txt", 'rt').read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.2",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: Implementation :: PyPy",
          "Programming Language :: Python :: Implementation :: Jython",
      ],
      keywords=['pypi', 'quality', 'testing'],
      author='Lennart Regebro',
      author_email='regebro@gmail.com',
      url='https://bitbucket.org/regebro/pyroma',
      license='MIT',
      packages=find_packages(exclude=['ez_setup']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'docutils',
      ],
      entry_points={
          'console_scripts': [
              'pyroma = pyroma:main',
          ],
          'zest.releaser.prereleaser.before': [
              'pyroma = pyroma:zester',
          ],
      },
      test_suite='pyroma',
      )
