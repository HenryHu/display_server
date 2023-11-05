#!/bin/sh

cd `dirname $0`

pkill -f flask
env FLASK_APP=main.py nohup flask run --host=0.0.0.0 &
