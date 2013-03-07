import sys
import os
from pyroma import projectdata, distributiondata, pypidata, ratings

def zester(data):
    from zest.releaser.utils import ask
    if ask("Run pyroma on the package before uploading?"):
        result = run(data['tagdir'])
        if result != 10:
            if not ask("Continue?"):
                sys.exit(1)
    
    
def run(argument):
    print('-'*30)
    print('Checking ' + argument)
    
    if os.path.isdir(argument):
        data = projectdata.get_data(os.path.abspath(argument))
        print('Found ' + data.get('name', 'nothing'))
    
    elif os.path.isfile(argument):
        data = distributiondata.get_data(os.path.abspath(argument))
        print('Found ' + data.get('name', 'nothing'))
        
    else:
        # It's probably a package name
        data = pypidata.get_data(argument)
        print('Found ' + data.get('name', 'nothing'))
    rating = ratings.rate(data)
        
    print('-'*30)
    for problem in rating[1]:
        # XXX It would be nice with a * pointlist instead, but that requires
        # that we know how wide the terminal is and nice word-breaks, so that's
        # for later.
        print(problem)
    if rating[1]:
        print('-'*30)
    print('Final rating: ' + str(rating[0]) + '/10')
    print(ratings.LEVELS[rating[0]])
    print('-'*30)
    return rating[0]

def main():
    if len(sys.argv) < 2:
        print("Usage: pyroma <project directory|file|project name>")
        sys.exit(1)
        
    run(sys.argv[1])

