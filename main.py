#!/usr/bin/env python3

import os
import subprocess
import glob
import logging
import collections

import feedparser

import dblib

from flask import Flask, request, render_template, g
app = Flask("Display Server")
db = dblib.DB(app)

host_info = {}

@app.teardown_appcontext
def teardown(exception):
    db.teardown()

def get_output(command, args):
    app.logger.info("running %s %s" % (command, args))
    try:
        return subprocess.check_output(["env", "DISPLAY=:0", command, *args]).decode('utf-8')
    except:
        return None

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

def collect_hosts():
    targets = {}
    maxlen = 0
    for line in open('hosts.txt').read().split('\n'):
        if not ' ' in line: continue
        (name, target) = line.split(' ')
        targets[name] = target
        if len(name) > maxlen: maxlen = len(name)

    hosts = []
    for name, target in targets.items():
        if not name in host_info:
            host_info[name] = {"succ": 0, "total": 0, "history": []}

        conn = "?"
        info = host_info[name]
        info["total"] += 1
        if run_command("ping", ["-c", "1", "-W", "1", target]):
            info["succ"] += 1
            info["history"].append(1)

            color = 'lightgreen'
            if sum(info["history"]) != len(info['history']): color = "yellow"
            conn = '<div style="display: inline; color: %s"> OK</div>' % color
            style = "conn_good"
        else:
            conn = '<div style="display: inline; color: red">ERR</div>'
            style = "conn_bad"
            info["history"].append(0)

        info["history"] = info["history"][-30:]
        host = {
            "name": ('%%-%ds' % maxlen) % name,
            "conn": conn,
            "style": style,
            "rate": 1.0 * sum(info["history"]) / len(info["history"])
        }
        hosts.append(host)
    return hosts

def collect_news():
    feed = feedparser.parse("https://hnrss.org/newest?count=8")
    news = []
    for item in feed['items']:
        news.append({'title': item['title'], 'link': item['link'], 'content': ''})
    return news

@app.route('/page')
def page():
    autorefresh = request.args.get('autorefresh', 'true')

    hosts = collect_hosts()
    news = collect_news()
    items = []
    for item in db.query_db("select * from items"):
        items.append(item)
    return render_template('page.html', items=items, hosts=hosts, news=news, autorefresh=autorefresh)

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
