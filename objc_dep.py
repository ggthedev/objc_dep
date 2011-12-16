#!/usr/bin/python

# Nicolas Seriot
# 2011-01-06 -> 2011-12-16
# https://github.com/nst/objc_dep/

"""
Input: path of an Objective-C project

Output: import dependancies Graphviz format

Typical usage: $ python objc_dep.py /path/to/project > graph.dot

The .dot file can be opened with Graphviz or OmniGraffle.

- red arrows: .pch imports
- blue arrows: two ways imports
"""

import sys
import os
from sets import Set
import re
from os.path import basename

regex_import = re.compile("#import \"(?P<filename>\S*)\.h")

def gen_filenames_imported_in_file(path):
    for line in open(path):
        results = re.search(regex_import, line)
        if results:
            filename = results.group('filename')
            yield filename

def dependancies_in_project(path, ext):
    d = {}
    
    for root, dirs, files in os.walk(path):

        objc_files = (f for f in files if f.endswith(ext))

        for f in objc_files:
            filename = os.path.splitext(f)[0]

            if filename not in d:
                d[filename] = Set()
            
            path = os.path.join(root, f)
            
            for imported_filename in gen_filenames_imported_in_file(path):
                d[filename].add(imported_filename)

    return d

def dependancies_in_project_with_file_extensions(path, exts):

    d = {}
    
    for ext in exts:
        d2 = dependancies_in_project(path, ext)
        for (k, v) in d2.iteritems():
            if not k in d:
                d[k] = Set()
            d[k] = d[k].union(v)

    return d

def two_ways_dependancies(d):

    two_ways = Set()

    # d is {'a1':[b1, b2], 'a2':[b1, b3, b4], ...}

    for a, l in d.iteritems():
        for b in l:
            if b in d and a in d[b]:
                if (a, b) in two_ways or (b, a) in two_ways:
                    continue
                if a != b:
                    two_ways.add((a, b))
                    
    return two_ways
    
def dependancies_in_dot_format(path):

    d = dependancies_in_project_with_file_extensions(path, ['.h', '.m'])
    
    two_ways_set = two_ways_dependancies(d)

    pch_set = dependancies_in_project(path, '.pch')

    #

    l = []
    l.append("digraph G {")
    l.append("\tnode [shape=box];")
    two_ways = Set()

    for k, deps in d.iteritems():
        if deps:
            deps.discard(k)
        
        if len(deps) == 0:
            l.append("\t\"%s\" -> {};" % (k))
        
        for k2 in deps:
            if (k, k2) in two_ways_set or (k2, k) in two_ways_set:
                two_ways.add((k, k2))
            else:
                l.append("\t\"%s\" -> \"%s\";" % (k, k2))

    l.append("\t")
    for (k, v) in pch_set.iteritems():
        l.append("\t\"%s\" [color=red];" % k)
        for x in v:
            l.append("\t\"%s\" -> \"%s\" [color=red];" % (k, x))
    
    l.append("\t")
    l.append("\tedge [color=blue];")

    for (k, k2) in two_ways:
        l.append("\t\"%s\" -> \"%s\";" % (k, k2))
    
    l.append("}\n")
    return '\n'.join(l)

def main():
    if len(sys.argv) != 2 or not os.path.exists(sys.argv[1]):
        print "USAGE: $ python %s PROJECT_PATH" % sys.argv[0]
        exit(0)

    print dependancies_in_dot_format(sys.argv[1])
  
if __name__=='__main__':
    main()