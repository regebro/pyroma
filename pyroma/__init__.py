import logging
import os
import sys
from argparse import ArgumentParser, ArgumentTypeError
from pyroma import projectdata, distributiondata, pypidata, ratings

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format="%(message)s")


def zester(data):
    main_files = set(os.listdir(data["workingdir"]))
    config_files = {"setup.py", "setup.cfg", "pyproject.toml"}

    # If there are no standard Python config files in the main files
    # it's likely not a Python project, so just return.
    if not config_files & main_files:
        return

    from zest.releaser.utils import ask

    if ask("Run pyroma on the package before tagging?"):
        rating = run("directory", os.path.abspath(data["workingdir"]), skip_tests="CheckManifest")
        if rating < 8:
            if not ask("Continue?"):
                sys.exit(1)


def min_argument(arg):
    try:
        f = int(arg)
    except ValueError:
        raise ArgumentTypeError("Must be an integer between 1 and 10")
    if f < 0:
        raise ArgumentTypeError("Oh, it's not THAT bad, trust me.")
    if f < 1:
        raise ArgumentTypeError("Why run pyroma if you intend it to always pass?")
    if f > 10:
        raise ArgumentTypeError("Why run pyroma if you intend it to never pass?")
    return f


def get_all_tests():
    return [x.__class__.__name__ for x in ratings.ALL_TESTS]


def parse_tests(arg):
    if not arg:
        return

    arg = [arg]
    for sep in " ,;":
        skips = []
        for t in arg:
            skips.extend(t.split(sep))
        arg = skips

    tests = get_all_tests()
    for skip in arg:
        if skip not in tests:
            return

    return skip


def skip_tests(arg):
    test_to_skip = parse_tests(arg)
    if test_to_skip:
        return test_to_skip

    tests = ", ".join(get_all_tests())
    message = f"Invalid tests listed. Available tests: {tests}"
    raise ArgumentTypeError(message)


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "package", help="A python package, can be a directory, a distribution file or a PyPI package name."
    )
    parser.add_argument(
        "-n",
        "--min",
        dest="min",
        default=8,
        action="store",
        type=min_argument,
        help="Minimum rating for clean return between 1 and 10, inclusive.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-a",
        "--auto",
        dest="mode",
        action="store_const",
        const="auto",
        help="Select mode automatically (default)",
    )
    group.add_argument(
        "-d",
        "--directory",
        dest="mode",
        action="store_const",
        const="directory",
        help="Run pyroma on a module in a project directory",
    )
    group.add_argument(
        "-f",
        "--file",
        dest="mode",
        action="store_const",
        const="file",
        help="Run pyroma on a distribution file",
    )
    group.add_argument(
        "-p",
        "--pypi",
        dest="mode",
        action="store_const",
        const="pypi",
        help="Run pyroma on a package on PyPI",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        dest="quiet",
        action="store_true",
        default=False,
        help="Output only the rating",
    )
    parser.add_argument(
        "--skip-tests",
        type=skip_tests,
        help="Skip the named tests",
    )

    args = parser.parse_args()

    mode = args.mode
    if args.mode is None or args.mode == "auto":
        if os.path.isdir(args.package):
            mode = "directory"
        elif os.path.isfile(args.package):
            mode = "file"
        else:
            mode = "pypi"

    rating = run(mode, args.package, args.quiet, args.skip_tests)
    if rating < args.min:
        sys.exit(2)
    sys.exit(0)


def run(mode, argument, quiet=False, skip_tests=None):
    if quiet:
        logger = logging.getLogger()
        logger.disabled = True

    logging.info("-" * 30)
    logging.info("Checking " + argument)

    if mode == "directory":
        data = projectdata.get_data(os.path.abspath(argument))
        logging.info("Found " + data.get("name", "nothing"))
    elif mode == "file":
        data = distributiondata.get_data(os.path.abspath(argument))
        logging.info("Found " + data.get("name", "nothing"))
    else:
        # It's probably a package name
        data = pypidata.get_data(argument)
        logging.info("Found " + data.get("name", "nothing"))

    rating = ratings.rate(data, skip_tests)

    logging.info("-" * 30)
    for problem in rating[1]:
        # XXX It would be nice with a * pointlist instead, but that requires
        # that we know how wide the terminal is and nice word-breaks, so that's
        # for later.
        logging.info(problem)
    if rating[1]:
        logging.info("-" * 30)
    logging.info("Final rating: " + str(rating[0]) + "/10")
    logging.info(ratings.LEVELS[rating[0]])
    logging.info("-" * 30)

    if quiet:
        logger.disabled = False
        logging.info(rating[0])

    return rating[0]
