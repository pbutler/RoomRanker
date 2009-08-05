# vim: tabstop=4 shiftwidth=4 softtabstop=4 et

from google.appengine.ext import db


class InProgress(db.Model):
    roomname = db.StringProperty()
    done     = db.BooleanProperty()
    users    = db.StringListProperty()
    scores   = db.ListProperty(int)

class Batch(db.Model):
    users = db.StringListProperty()
    done     = db.BooleanProperty()

