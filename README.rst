pyroma
======

Pyroma rhymes with aroma, and is a product aimed at giving a rating of how well
a Python project complies with the best practices of the Python packaging
ecosystem, primarily PyPI, pip, Distribute etc, as well as a list of issues that
could be improved.

The aim of this is both to help people make a project that is nice and usable,
but also to improve the quality of Python third-party software, making it easier
and more enjoyable to use the vast array of available modules for Python.

It's written so that there are a library with methods to call from Python, as
well as a script, also called pyroma.

It can be run on a project directory before making a release:

    $ pyroma .

On a distribution before uploading it to the CheeseShop:

    $ pyroma pyroma-1.0.tar.gz

Or you can give it a package name on CheeseShop:

    $ pyroma pyroma

Giving it a name on CheeseShop is the most extensive test, as it will
test for several things isn't otherwise tested.

In all cases the output is similar::

    ------------------------------
    Checking .
    Found pyroma
    ------------------------------
    The packages long_description is quite short.
    ------------------------------
    Final rating: 9/10
    Cottage Cheese
    ------------------------------

Tests
-----

This is the list of checks that are currently performed:

* The package should have a name, a version and a Description.
  If it does not, it will receive a rating of 0.

* The version number should be a string. A floating point number will
  work with distutils, but most other tools will fail.

* The version number should comply to PEP386.

* The long_description should be over a 100 characters.

* Pyroma will convert your long_description to HTML using Docutils, to
  verify that it is possible. This guarantees pretty formatting of your
  description on PyPI. As long as Docutils can convert it, this passes,
  even if there are warnings or error in the conversion. These warnings
  and errors are printed to stdout so you will see them.

* You should have a the following meta data fields filled in:
  classifiers, keywords, author, author_email, url and license.

* You should have classifiers specifying the sypported Python versions.

* If you are using setuptools or distribute you should specify zip_safe,
  as it defaults to "true" and that's probably not what you want.

* If you are using setuptools or distribute you can specify a test_suite
  to run tests with 'setup.py test'. This makes it easy to run tests for
  both humans and automated tools.

* If you are checking on a PyPI package, and not a local directory or
  local package, pyroma will check the number of owners the package has
  on PyPI. It should be three or more, to minimize the "Bus factor",
  the risk of the index owners suddenly going off-line for whatever reason.

* If you are checking on a PyPI package, and not a local directory or
  local package, Pyroma will look for documentation for your package at
  pythonhosted.org and readthedocs.org. If it can't find it, it prints out
  a message to that effect. However, since you may have documentation
  elsewhere, this does not affect your rating.

Credits
-------

The project was created by Lennart Regebro, regebro@gmail.com

The name "Pyroma" was coined by Wichert Akkerman, wichert@wiggy.net

Contributors:

  * Godefroid Chapelle
  * Dmitry Vakhrushev
  * hugovk
  * Jeff Quast
  * Maurits van Rees
