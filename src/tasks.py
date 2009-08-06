#!/usr/bin/env python
# vim: et ts=4 sw=4 smarttab

import wsgiref.handlers
from google.appengine.ext import db
from google.appengine.api.labs.taskqueue  import Task

from google.appengine.ext import webapp
#from google.appengine.ext.webapp import template

from data import Job, Batch, User

import random
import logging

class RunBatchHandler(webapp.RequestHandler):
    def get(self): 
        batchid = self.request.get('batchid') 
        batch = db.get(batchid) 

        uobjects = []
        for user in batch.users:
            if User.all().filter("nickname=", user).count() > 0:
                continue
            #TODO query FF for the users prescriptions
            n = random.randint(1,10)
            friends = [ ("user%02d" % (random.randint(0,19))) for i in range(n)]
            u = User( nickname = user, friends = friends)
            uobjects += [ u ] 
        db.put(uobjects)
        batch.done = True 
        key = db.Key( str(batch.parent_key() ))
        batch.delete()
        #nbatches = Batch.all().ancestor( key ).filter("done=", True).count() 
        nbatches = Batch.all(keys_only=True)
        nbatches = nbatches.ancestor( key ) 
        nbatches = nbatches.count() 
        logging.info("nbatches=%d" % nbatches)
        if nbatches == 0: 
            job = db.get( key )
            job.done = True 
            job.put() 
            t = Task(method="GET", url="/tasks/FinishJob?jobid=%s" % job.key())
            t.add()
    
class FinishJobHandler(webapp.RequestHandler):
    def get(self): 
        jobid = self.request.get('jobid') 
        job = db.get(jobid) 
        job.ready = True
        users = User.all().filter("nickname IN", job.users)
        job.scores = [ 0. ] * len(job.users)
        for user in users:
            name = user.nickname
            idx = job.users.index(name)
            #TODO: calculate scores another way
            n = len(filter(lambda x: job.users.count(name)>0, user.friends))
            job.scores[idx] = float(n)
            #TODO: don't delete if caching
            user.delete()
        job.put() 
        

def main(): 
    application = webapp.WSGIApplication([ 
        ### QUEUE Handlers 
        ('/tasks/RunBatch', RunBatchHandler),
        ('/tasks/FinishJob', FinishJobHandler),
      ], debug=True) 
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()
