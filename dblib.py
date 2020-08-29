from flask import g

import sqlite3

PAGE_DB = 'db/page.db'

class DB(object):
    def __init__(self, app):
        self.app = app

    def get_db(self):
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = sqlite3.connect(PAGE_DB)
            db.row_factory = sqlite3.Row

            with self.app.open_resource('schema.sql', mode='r') as schema:
                db.cursor().executescript(schema.read())
            db.commit()
        return db

    def execute_db(self, query, args=()):
        db = self.get_db()
        db.execute(query, args)
        db.commit()

    def query_db(self, query, args=()):
        cur = self.get_db().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return rv

    def teardown(self):
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()
