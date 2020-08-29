#!/usr/bin/env python3

import os
import subprocess
import glob
import logging

import sqlite3
from flask import Flask, request, render_template, g
app = Flask("Display Server")

PAGE_DB = 'db/page.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(PAGE_DB)
        db.row_factory = sqlite3.Row

        with app.open_resource('schema.sql', mode='r') as schema:
            db.cursor().executescript(schema.read())
        db.commit()
    return db

def execute_db(query, args=()):
    db = get_db()
    db.execute(query, args)
    db.commit()

def query_db(query, args=()):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return rv

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

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
    for item in query_db("select * from items"):
        items.append(item)
    return render_template('page.html', items=items, autorefresh=autorefresh)

@app.route('/additem')
def additem():
    title = request.args.get('title', '')
    content = request.args.get('content', '')
    if not title and not content:
        return 'error: nothing to add'
    if not title: title = '<no title>'
    execute_db("insert into items (title, content) values (?, ?)", [title, content])
    return 'added'

@app.route('/delitem/<int:index>')
def delitem(index):
    if not index:
        return 'error: nothing to delete'
    execute_db("delete from items where idx = ?", [index])
    return 'deleted'
