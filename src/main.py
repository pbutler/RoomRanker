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


from google.appengine.ext import webapp
import os
from google.appengine.ext.webapp import template

class IndexHandler(webapp.RequestHandler): 
    def get(self):
        values = { 'body' :
        """ 
<form action="/room" method="get"> 
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

#import friendfeed
import roomranker

class RoomHandler(webapp.RequestHandler): 
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        if self.request.get('room') is None:
            self.response.out.write(template.render(path,{"body":"Need a room name"}))

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
    ('/room', RoomHandler)
  ],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
