# vim: tabstop=4 shiftwidth=4 softtabstop=4 et

from google.appengine.ext import db


class Job(db.Model):
    """
    Fields:
    roomname: the roomname being processed
    done:     are the individual batches done?
    ready:    are we ready to display the results?
    users:    list of users in room
    scores:   a list of scores ordered the same as users
    """
    roomname = db.StringProperty()
    done     = db.BooleanProperty()
    ready    = db.BooleanProperty()
    users    = db.StringListProperty()
    scores   = db.ListProperty(float)
    created  = db.DateTimeProperty(auto_now_add=True)

class Batch(db.Model):
    """
    Fields:
    users: list of users to process in a batch
    done:  have we gotten our yummies yet?
    """
    users    = db.StringListProperty()
    done     = db.BooleanProperty()
    created  = db.DateTimeProperty(auto_now_add=True)

class User(db.Model):
    """
    Fields:
    nickname: username
    friends:  people following this newb
    """
    nickname = db.StringProperty()
    friends  = db.StringListProperty() 
    created  = db.DateTimeProperty(auto_now_add=True)
