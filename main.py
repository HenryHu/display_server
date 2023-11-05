#!/usr/bin/env python3

import os
import subprocess
import glob
import logging
import collections
import time
import datetime

import feedparser

import dblib

from flask import Flask, request, render_template, g
app = Flask("Display Server")
db = dblib.DB(app)

RELAX_MARK = "/tmp/relax_inhibit"

host_info = {}


@app.teardown_appcontext
def teardown(exception):
    db.teardown()


def get_output(command, args, line_limit=None):
    app.logger.info("running %s %s" % (command, args))
    try:
        result = subprocess.check_output(["env", "DISPLAY=:0",
                                          command, *args]).decode('utf-8')
        if line_limit:
            return '\n'.join(result.split('\n')[:line_limit])
        return result
    except Exception as e:
        app.logger.error(e)
        return 'error: %r' % e


def run_command(command, args):
    app.logger.info("running %s %s" % (command, args))
    try:
        subprocess.check_output(["env", "DISPLAY=:0", command, *args])
    except:
        return False
    return True


@app.route('/')
def root():
    return render_template('index.html')


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
            if len(files) > 0:
                icon = files[0]

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
        if ' ' not in line:
            continue
        if line[:1] == '#':
            continue
        (name, target) = line.split(' ')
        targets[name] = target
        if len(name) > maxlen:
            maxlen = len(name)

    hosts = []
    for name, target in targets.items():
        if name not in host_info:
            host_info[name] = {"succ": 0, "total": 0, "history": []}

        conn = "?"
        info = host_info[name]
        info["total"] += 1
        if run_command("ping", ["-c", "1", "-W", "1", target]):
            info["succ"] += 1
            info["history"].append(1)

            color = 'lightgreen'
            if sum(info["history"]) != len(info['history']):
                color = "yellow"
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
    feed = feedparser.parse("https://hnrss.org/frontpage?count=3")
    news = []
    for item in feed['items']:
        news.append({'title': item['title'], 'link': item['link'],
                     'content': ''})
    return news


def collect_time():
    local = time.localtime()
    pactime = datetime.datetime.now(datetime.timezone(datetime.timedelta(
        seconds=local.tm_gmtoff - 3*3600)))
    return {"date": time.strftime("%Y/%m/%d %a"),
            "time": time.strftime("%I:%M:%S"),
            "pactime": pactime.strftime("%H:%M:%S")}


def collect_dhcp():
    leases = get_output('cat', ['/var/lib/misc/dnsmasq.leases'])
    if leases is None:
        return ''
    return "DHCP leases: %d" % len(leases.split('\n'))


def collect_msg():
    msg = []

    now = time.localtime()
    if now.tm_hour >= 0 and now.tm_hour <= 5:
        msg.append('<div class="warning">SLEEP!!!</div>')

    return ''.join(msg)


def should_notify_relax():
    if not os.path.exists(RELAX_MARK):
        return True
    st = os.stat(RELAX_MARK)
    if st.st_mtime > time.time() - 300:
        return False
    return True


def work_time(localtime):
    if localtime.tm_hour >= 10 and localtime.tm_hour <= 19:
        if localtime.tm_wday >= 0 and localtime.tm_wday <= 4:
            return True
    return False


def collect_timer():
    now = time.localtime()
    if work_time(now):
        if now.tm_min >= 55 and now.tm_min <= 59:
            timer = {'state': "RELAX"}
            if should_notify_relax():
                get_output("espeak-ng", ["relax"])
                timer['style'] = "relax"
            else:
                timer['style'] = "relax-inhibit"
        else:
            timer = {'state': "WORK", 'style': "work"}
    elif (now.tm_hour >= 1 and now.tm_hour <= 8 or
          now.tm_hour >= 0 and now.tm_hour <= 1 and now.tm_min >= 30):
        timer = {'state': "SLEEP", 'style': "sleep"}
    else:
        timer = {'state': "PLAY", 'style': "play"}
    return timer

def collect_music():
    title = get_output('mpc', ['-f', '%title%'], line_limit=1)
    artist = get_output('mpc', ['-f', '%artist%'], line_limit=1)
    album = get_output('mpc', ['-f', '%album%'], line_limit=1)
    return {'title': title, 'artist': artist, 'album': album}

def get_kasa_state(name):
    return get_output("/home/henryhu/proj/kasa/bin/python3",
                        ["/home/henryhu/proj/kasa/bin/state.py", name])

def get_tplink_state(name):
    ret = get_output("python3",
                        ["/home/henryhu/proj/tplink/cli.py", name, "state"])
    ret = ret.split('\n')
    if len(ret) == 1:
        return "unknown"
    else:
        return ret[1]

def get_tuya_state(name):
    return get_output("/home/henryhu/proj/tuya/bin/python3",
                        ["/home/henryhu/proj/tuya/state.py", name])

def get_buttons():
    buttons = []
    buttons.append({"id": "rabbit", "class": "home", "img": "rabbit.png",
                    "text": "rabbit: %s" % get_kasa_state("rabbit") })
    buttons.append({"id": "fire", "text": "fire: %s" % get_tplink_state("fire"), "class": "home",
                    "img": "fire.png"})
    buttons.append({"id": "candle", "text": "candle: %s" % get_tplink_state("candle"), "class": "home",
                    "img": "candle.png"})
    buttons.append({"id": "sunny", "text": "sunny: %s" % get_tuya_state("sunny"), "class": "home",
                    "img": "sunny.png"})
    return buttons

@app.route('/page')
def page():
    autorefresh = request.args.get('autorefresh', 'true')

    hosts = collect_hosts()
    news = collect_news()
    time = collect_time()
    items = []
    dhcp = collect_dhcp()
    for item in db.query_db("select * from items"):
        items.append(item)
    msg = collect_msg()
    timer = collect_timer()
    music = collect_music()
    buttons = get_buttons()
    if timer['state'] == 'SLEEP':
        return render_template('page_night.html', items=items, hosts=hosts,
                               news=news, time=time,
                               dhcp=dhcp, msg=msg, timer=timer, music=music,
                               autorefresh=autorefresh)

    return render_template('page.html', items=items, hosts=hosts, news=news, time=time,
                           dhcp=dhcp, msg=msg, timer=timer, music=music, buttons=buttons,
                           autorefresh=autorefresh)


@app.route('/additem')
def additem():
    title = request.args.get('title', '')
    content = request.args.get('content', '')
    if not title and not content:
        return 'error: nothing to add'
    if not title:
        title = '<no title>'
    db.execute_db(
        "insert into items (title, content) values (?, ?)", [title, content])
    return 'added'


@app.route('/delitem/<int:index>')
def delitem(index):
    if not index:
        return 'error: nothing to delete'
    db.execute_db("delete from items where idx = ?", [index])
    return 'deleted'

@app.route('/button_click/<string:id>', methods = ['POST'])
def button_click(id):
    if id == "rabbit":
        output = get_output("/home/henryhu/proj/kasa/bin/python3",
                            ["/home/henryhu/proj/kasa/bin/toggle.py", "rabbit"])
    if id == "fire":
        output = get_output("python3",
                            ["/home/henryhu/proj/tplink/cli.py", "fire", "toggle"])
    if id == "candle":
        output = get_output("python3",
                            ["/home/henryhu/proj/tplink/cli.py", "candle", "toggle"])
    if id == "sunny":
        output = get_output("/home/henryhu/proj/tuya/bin/python3",
                            ["/home/henryhu/proj/tuya/toggle.py", "sunny"])

    return output
