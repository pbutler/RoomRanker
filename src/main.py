#!/usr/bin/env python
# vim: et ts=4 sw=4 smarttab
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import wsgiref.handlers
from google.appengine.ext import db
from google.appengine.api.labs.taskqueue  import Task

from google.appengine.ext import webapp
import os
from google.appengine.ext.webapp import template

from data import InProgress, Batch

class IndexHandler(webapp.RequestHandler): 
    """
    Handles the welcome screen and presenting a form
    """
    def get(self):
        values = { 'body' :
        """ 
<form action="/prepare" method="get"> 
<div>
<label style="font-weight: bold;">FriendFeed Room:</label>
<input type="text" name="room" value="" />
&nbsp; &nbsp;
<input type="submit" value="Who's The Fairest of Them All?"></div> 
</form>
        """, 
        'subtitle' : "Welcome" }
        path = os.path.join(os.path.dirname(__file__), 'index.html') 
        self.response.out.write(template.render(path, values))

class WaitHandler(webapp.RequestHandler):
    """
    After we submit a job
    """
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'index.html') 
        values = { 'body':'', 'subtitle' : "And now we wait..."}
        if self.request.get('jobid') is None:
            values['body'] = "We need a job to wait on, try again...."
            self.response.out.write(template.render(path, values))
            return
        jobid = self.request.get('jobid')
        job = db.get(jobid)
        if job == None:
            values['body'] = "The jobid you gave me was invalid what's wrong with you?!?"
            self.response.out.write(template.render(path, values))
            return
        if not job.done:
            values["script"] = "function delayer(){ document.location = window.location.href=window.location.href;}"
            values["onLoad"] = "setTimeout('delayer()', 5000)"
            values['body'] = "And now we wait some more (5 seconds)...."
            self.response.out.write(template.render(path, values))
            return
        values['body'] = "OH MY WE'RE DONE!!! ONE MORE SECOND OKAY!?!?!"
        self.response.out.write(template.render(path, values))
        self.redirect("/roomrank?jobid=\"%s\"" % jobid)
        return

class PrepareHandler(webapp.RequestHandler): 
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        room = self.request.get('room') 
        if room is None:
            self.response.out.write(template.render(path,{"body":"Need a room name"}))

        users = [ ('user%02d' % (i)) for i in range(20)]
        ip = InProgress(roomname=room, done=False, users = users, score = [])
        BATCHSIZE = 4
        for i in range(0,len(users),BATCHSIZE):
            b = Batch(users=users[i:i + BATCHSIZE], done = False)
            b.put()
            t = Task(method="get", url="/RunBatch?batchid=%s" % b.key());
            t.add()


class RunBatchHandler(webapp.RequestHandler): 
    def get(self):
        batchid = self.request.get('batchid')
        batch = db.get(batchid)
        batch.done = True
        batch.put()
        batch.delete()


class RoomHandler(webapp.RequestHandler): 
   def get(self):
        values = { 'body':'', 'subtitle' : 'And the Winner is ...'}
        #roomranker.generate_rankings(users)
        rankings = [ ("alpha",  10), ("beta", 5), ("omega", 1)]
        values['body'] += "<table><tr><th>Rank</th><th>Name</th><th>Fans</th></tr>"
        for i in range(len(rankings)):
            values['body'] += "<tr><td>#%d:</td><td>%s</td><td>%d</td>" % (i+1, rankings[i][0], rankings[i][1])
        values['body'] += "</table>"
        self.response.out.write(template.render(path, values))
        return



def main():
  application = webapp.WSGIApplication([
    ('/', IndexHandler),
    ('/prepare', PrepareHandler),
    ('/wait', WaitHandler),
    #('/done', DoneHandler),
    ('/roomrank', RoomHandler),

### QUEUE Handlers
    ('/RunBatch', RunBatchHandler),
  ],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
