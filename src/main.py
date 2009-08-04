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

import friendfeed

class RoomHandler(webapp.RequestHandler): 
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        if self.request.get('room') is None:
            self.response.out.write(template.render(path,{"body":"Need a room name"}))

        roomname = self.request.get('roomname')
        api = friendfeed.FriendAPI()
        values = { 'body' : '', 'subtitle' : "And the winner is..." }


        room = api.get_room_profile(roomname)
        public = []
        for m in room.members:
            try: 
                api.update_user_profile(m)
                public += [m]
            except HTTPError:
                pass
        nicks = [ m.nickname for m in public ] 
        for m in pubic:




        path = os.path.join(os.path.dirname(__file__), 'index.html') 
        self.response.out.write(template.render(path, values))





def main():
  application = webapp.WSGIApplication([('/', IndexHandler)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
