#!/bin/sh

pkill flask
env FLASK_APP=main.py nohup flask run --host=0.0.0.0 &
