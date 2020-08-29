#!/usr/bin/env python3

import os
import subprocess
import glob
import logging

from flask import Flask, request
app = Flask("Display Server")

logger = logging.getLogger("main")

def run_command(command, args):
    logger.info("running %s %s" % (command, args))
    try:
        subprocess.check_output(["env", "DISPLAY=:0", command, *args])
    except:
        return False
    return True

@app.route('/')
def hello_world():
    return 'hello world'

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
    return 'page'
