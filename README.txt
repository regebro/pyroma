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

In all cases the output is similar::

    ------------------------------
    Checking .
    Found pyroma
    ------------------------------
    Did you forget to declare the following dependencies?: setup
    ------------------------------
    Final rating: 9/10
    Cottage Cheese
    ------------------------------

TODO
----

 * Figure out why the long_description doesn't render to HTML properly.

 * Add a test for that.
 
 * Figure out how to stop ast from failing on perfectly valid code.
 
 * Discuss whether to check for missing imports at all, since so many
   packages seem to break this. 
 
 * More verification tests?
 
 * More unit tests! Many more unit tests!!! And mock PyPI instead of using it.

Credits
-------

The project was created by Lennart Regebro, regebro@gmail.com
The name "Pyroma" was coined by Wichert Akkerman, wichert@wiggy.net
