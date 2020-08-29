from flask import g

import sqlite3

app = None
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

def teardown():
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


