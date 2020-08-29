#!/usr/bin/env python3

import os
import subprocess
import glob
import logging

import dblib

from flask import Flask, request, render_template, g
app = Flask("Display Server")
db = dblib.DB(app)

@app.teardown_appcontext
def teardown(exception):
    db.teardown()

def run_command(command, args):
    app.logger.info("running %s %s" % (command, args))
    try:
        subprocess.check_output(["env", "DISPLAY=:0", command, *args])
    except:
        return False
    return True

@app.route('/')
def root():
    return 'running'

@app.route('/notify/<title>')
def notify(title):
    message = request.args.get('message', '')
    icon = request.args.get('icon', '')
    timeout = request.args.get('timeout', '5000')
    urgency = request.args.get('urgency', '')

    if icon != '':
        files = glob.glob("/usr/share/icons/oxygen/*/*/%s.*" % icon)
        found = False
        for filename in files:
            if 'scalable' in filename:
                icon = filename
                found = True
                break
        if not found:
            if len(files) > 0: icon = files[0]

    args = [title, message, '-t', timeout]
    if icon:
        args.append('-i')
        args.append(icon)
    if urgency:
        args.append('-u')
        args.append(urgency)

    if run_command("notify-send", args):
        return 'sent'
    else:
        return 'error'

@app.route('/page')
def page():
    autorefresh = request.args.get('autorefresh', 'true')

    items = []
    for item in db.query_db("select * from items"):
        items.append(item)
    return render_template('page.html', items=items, autorefresh=autorefresh)

@app.route('/additem')
def additem():
    title = request.args.get('title', '')
    content = request.args.get('content', '')
    if not title and not content:
        return 'error: nothing to add'
    if not title: title = '<no title>'
    db.execute_db("insert into items (title, content) values (?, ?)", [title, content])
    return 'added'

@app.route('/delitem/<int:index>')
def delitem(index):
    if not index:
        return 'error: nothing to delete'
    db.execute_db("delete from items where idx = ?", [index])
    return 'deleted'
