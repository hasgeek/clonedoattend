import unicodecsv
import sys
import random
import string
from collections import OrderedDict

def csv2obj(path):
    f = open(path, 'rU')
    obj = OrderedDict()
    csv = unicodecsv.reader(f, delimiter=",", quotechar='"')
    for row in csv:
        if(len(row)):
            obj[row[0]] = dict(data=row[1], helper=row[2] if len(row) >= 3 else "")
    return obj

def obj2csv(path, obj):
    f = open(path, 'w')
    csv = unicodecsv.writer(f, delimiter=",", quotechar='"')
    for key, data in enumerate(obj):
        csv.writerow([key, data['data'], data['helper']])

def yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes":True,   "y":True,  "ye":True,
             "no":False,     "n":False}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "\
                             "(or 'y' or 'n').\n")

def title(t, hr='=', hr_size = 50):
    print hr * hr_size
    print t
    print hr * hr_size

def random_discount_code():
    return ''.join(random.choice(string.letters + string.digits) for i in range(8))

def levenshtein(a,b):
    "Calculates the Levenshtein distance between a and b."
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a,b = b,a
        n,m = m,n
        
    current = range(n+1)
    for i in range(1,m+1):
        previous, current = current, [i]+[0]*n
        for j in range(1,n+1):
            add, delete = previous[j]+1, current[j-1]+1
            change = previous[j-1]
            if a[j-1] != b[i-1]:
                change = change + 1
            current[j] = min(add, delete, change)
            
    return current[n]
