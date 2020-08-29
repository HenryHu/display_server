#!/usr/bin/env python3

import sys
import urllib.request

base_url = "http://dew/"

def call(url, args={}):
    first = True
    for key, value in args.items():
        if first:
            url += '?'
        else:
            url += '&'
        url += '%s=%s' % (key, value)
    full_url = base_url + url
    print(full_url)
    print(urllib.request.urlopen(full_url).read())

def notify(args):
    title = args[0]
    call('notify/%s' % title)

def additem(args):
    call('additem', {'title': args[0]})

def additem(args):
    idx = args[0]
    call('delitem/%s' % idx)

cmd = sys.argv[1]
args = sys.argv[2:]
if cmd == 'notify':
    notify(args)
if cmd == 'add':
    additem(args)
if cmd == 'delete':
    delitem(args)
