#!/usr/bin/env python3

import sys
import urllib.request
import urllib.parse

base_url = "http://dew/"

def call(url, args={}):
    first = True
    if args: url += '?' + urllib.parse.urlencode(args)
    full_url = base_url + url
    print(full_url)
    print(urllib.request.urlopen(full_url).read())

def notify(args):
    title = args[0]
    call_args = {}
    if len(args) > 1:
        call_args['message'] = args[1]
    call('notify/%s' % title, call_args)

def additem(args):
    call('additem', {'title': args[0], 'content': args[1]})

def delitem(args):
    idx = int(args[0])
    call('delitem/%s' % idx)

cmd = sys.argv[1]
args = sys.argv[2:]
if cmd == 'notify':
    notify(args)
if cmd == 'add':
    additem(args)
if cmd == 'delete':
    delitem(args)
