#!/usr/bin/env python
#
# Copyright (c) 2008 FriendFeed
# Copyright (c) 2008 Chris Lasher
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Methods to interact with the FriendFeed API

Detailed documentation is available at http://friendfeed.com/api/.

Many parts of the FriendFeed API require authentication. To support
authentication, FriendFeed gives users a "remote key" that they give to
third party applications to access FriendFeed. The user's nickname and that
remote key are passed as arguments to the constructor of the FriendFeed class,
and the credentials are automatically passed to all called methods. For
example:

    session = friendfeed.FriendFeedAPI(nickname, remote_key)
    entry = session.publish_message("Testing the FriendFeed API")

Users can get their remote key from http://friendfeed.com/remotekey. You
should direct users who don't know their remote key to that page.
For guidelines on user interface and terminology, check out
http://friendfeed.com/api/guidelines.
"""

import base64
import datetime
import pprint
import time
import urllib
import urllib2

# We require a JSON parsing library. These seem to be the most popular.
try:
    import json
    parse_json = lambda s: json.loads(s.decode('utf-8'))
except ImportError:
    try:
        import simplejson
        parse_json = lambda s: simplejson.loads(s.decode('utf-8'))
    except ImportError:
        import cjson
        parse_json = lambda s: cjson.decode(s.decode('utf-8'), True)

# This library relies on the poster library for pushing files to the
# FriendFeed server
# http://atlee.ca/software/poster/
try:
    import poster
    poster.streaminghttp.register_openers()
except ImportError:
    pass


# Exceptions to raise for returned FriendFeed errors.
class FriendFeedException(Exception):
    """A FriendFeed exception."""
    pass


class BadIdFormatError(FriendFeedException):
    """Raised for an incorrectly formatted UUID."""
    pass


class BadUrlFormatError(FriendFeedException):
    """Raised for an incorrectly formatted URL."""
    pass


class EntryNotFoundError(FriendFeedException):
    """Raised when no entry matches a given UUID."""
    pass


class EntryRequiredError(FriendFeedException):
    """Raised when an entry UUID is not provided."""
    pass


class ForbiddenError(FriendFeedException):
    """
    Raised for insufficient credentials to access an entry, room, or
    other FriendFeed entity.

    """
    pass


class ImageFormatNotSupportedError(FriendFeedException):
    """Raised for an unsupported image format."""
    pass


class InternalServerErrorError(FriendFeedException):
    """Raised upon an internal FriendFeed server error."""
    pass


class LimitExceededError(FriendFeedException):
    """Raised when requests to FriendFeed have exceeded limit."""
    pass


class RoomNotFoundError(FriendFeedException):
    """Raised when no room of specified name is found."""
    pass


class RoomRequiredError(FriendFeedException):
    """Raised when a room name is not provided."""
    pass


class TitleRequiredError(FriendFeedException):
    """Raised when an entry title is not provided."""
    pass


class UnauthorizedError(FriendFeedException):
    """Raised when the request requires authentication."""
    pass


class UserNotFoundError(FriendFeedException):
    """Raised when no user of specified nickname exists."""
    pass


class UserRequiredError(FriendFeedException):
    """Raised when a user nickname is not provided."""
    pass


class FriendFeedError(FriendFeedException):
    """An unspecified error returned from FriendFeed."""
    pass


# a mapping of error codes to exceptions
FF_ERROR_MAPPING = {
        'bad-id-format': BadIdFormatError,
        'bad-url-format': BadUrlFormatError,
        'entry-not-found': EntryNotFoundError,
        'entry-required': EntryRequiredError,
        'forbidden': ForbiddenError,
        'image-format-not-supported': ImageFormatNotSupportedError,
        'internal-server-error': InternalServerErrorError,
        'limit-exceeded': LimitExceededError,
        'room-not-found': RoomNotFoundError,
        'room-required': RoomRequiredError,
        'title-required': TitleRequiredError,
        'unauthorized': UnauthorizedError,
        'user-not-found': UserNotFoundError,
        'user-required': UserRequiredError,
        'error': FriendFeedError
        }


class EqualityMixin(object):
    """
    A Mixin class to allow custom objects to support the equivalence
    operators __eq__ and __ne__.

    """

    def __eq__(self, other):
        return isinstance(other, self.__class__)\
                and self.__dict__ == other.__dict__


    def __ne__(self, other):
        return not self.__eq__(other)


class TruncateTextMixin(object):
    """
    A class to provide a simple method to truncate strings.

    """

    def truncate_text(self, text, length, suffix='...'):
        """
        Truncate text, appending an suffix to the end if necessary.

        :Parameters:
        - `text`: string to truncate
        - `length`: desired length of string (including suffix)
        - `suffix`: desired suffix for a truncated string

        """

        if len(text) <= length:
            return text
        else:
            return text[:length-len(suffix)].rsplit(' ', 1)[0] + suffix


class User(EqualityMixin):
    """
    A FriendFeed user.

    :Parameters:
    - `nickname`: the user's FriendFeed account name (e.g., "gotgenes")
        [REQUIRED]
    - `id`: the user's ID (e.g., "ae0a07fe-2768-11dd-a306-003048343a40")
    - `name`: the user's full name  (e.g., "Chris Lasher")
    - `profile_url`: the user's profile URL (e.g.,
            "http://friendfeed.com/gotgenes")
    - `private`: whether or not the profile is private [default: False]
    - `services`: a list of services connected to the user's account
    - `subscriptions`: the users a user subscribes to
    - `rooms`: rooms in which the user is a member
    - `lists`: lists a user is a member of [only available if
        authenticated as the user]

    """

    def __init__(
            self,
            nickname,
            id=None,
            name=None,
            profile_url=None,
            private=False,
            services=[],
            subscriptions=[],
            rooms=[],
            lists=[]
            ):

        if not nickname:
            raise ValueError("A nickname must be provided.")
        self.nickname = unicode(nickname)
        self.id = unicode(id)
        self.name = unicode(name)
        self.profile_url = unicode(profile_url)
        self.private = private
        self.services = services
        self.subscriptions = subscriptions
        self.rooms = rooms
        self.lists = lists


    def __repr__(self):

        return "<User %s>" % self.nickname


class ImaginaryFriend(EqualityMixin):
    """
    A class for an "imaginary friend" subscription.

    :Parameters:
    - `id`: the FriendFeed ID
    - `name`: the name of the imaginary friend
    - `profile_url`: the URL of the profile

    """

    def __init__(self, id, name, profile_url):
        self.id = id
        self.name = name
        self.profile_url = profile_url


    def __repr__(self):

        return "<ImaginaryFriend %s>" % self.name


class Service(EqualityMixin):
    """
    A service subscribed to in FriendFeed.

    :Parameters:
    - `id`: FriendFeed ID of the service (e.g., "picasa")
    - `name`: name of the service (e.g., "Picasa Web Albums")
    - `url`: the URL of the service (e.g.,
        "http://picasaweb.google.com/")
    - `icon_url`: the URL of the favicon for the service
    - `profile_url`: the URL of the user's profile on this service
    - `username`: the user's username for this service
    - `entry_type`: an undocumented attribute

    """

    def __init__(
            self,
            id,
            name,
            url=None,
            icon_url=None,
            profile_url=None,
            username=None,
            entry_type=None
        ):

        self.id = id
        self.name = name
        self.url = url
        self.icon_url = icon_url
        self.profile_url = profile_url
        self.username = username
        self.entry_type = entry_type


    def __repr__(self):

        return "<Service %s>" % self.name


class Room(EqualityMixin):
    """
    A FriendFeed room.

    :Parameters:
    - `nickname`: the room's FriendFeed nickname (e.g.,
        "the-life-scientists") [REQUIRED]
    - `id`: the room's FriendFeed ID (e.g.,
        "fedb6e36-e4a9-11dc-b594-003048343a40")
    - `name`: the room's full name (e.g., "The Life Scientists")
    - `url`: the room's URL
    - `private`: the room's privacy status (False if 'public', True if
        'private') [default: False]
    - `description`: a brief room summary
    - `members`: a list of members of the room
    - `administrators`: a list of administrators of the room

    """

    def __init__(
            self,
            nickname,
            id=None,
            name=None,
            url=None,
            private=False,
            description=None,
            members=[],
            administrators=[]
        ):

        if not nickname:
            raise ValueError("A nickname must be provided.")
        self.nickname = nickname
        self.id = id
        self.name = name
        self.url = url
        self.private = private
        self.description = description
        self.members = members
        self.administrators = administrators


    def __repr__(self):

        return "<Room %s>" % self.nickname


class SubscriptionList(EqualityMixin):
    """
    A FriendFeed list.

    NOTE: This will only be available for the authenticated user.

    :Parameters:
    - `nickname`: the list's FriendFeed nickname [REQUIRED]
    - `id`: the list's ID
    - `name`: the list's full name
    - `url`: the list's FriendFeed URL
    - `users`: a list of users belonging to the FriendFeed list
    - `rooms`: a list of rooms belonging to the FriendFeed list

    """

    def __init__(
            self,
            nickname,
            id=None,
            name=None,
            url=None,
            users=[],
            rooms=[]
        ):

        if not nickname:
            raise ValueError("A nickname must be provided.")
        self.nickname = nickname
        self.id = id
        self.name = name
        self.url = url
        self.users = users
        self.rooms = rooms


    def __repr__(self):

        return "<SubscriptionList %s>" % self.nickname


class Comment(EqualityMixin, TruncateTextMixin):
    """
    A comment to a FriendFeed entry.

    :Parameters:
    - `date`: date and time of the comment
    - `id`: the comment ID
    - `user`: the user the comment belongs to
    - `body`: the text of the comment
    - `via`: the FriendFeed client used to post the comment

    """

    def __init__(
            self,
            id,
            date=None,
            user=None,
            body=None,
            via={}
            ):

        if not id:
            raise ValueError("id must be provided.")
        self.id = id
        self.date = date
        self.user = user
        self.body = body
        self.via = via


    def __repr__(self):

        if self.body:
            body = self.truncate_text(self.body, 50)
        else:
            body = self.body
        return "<Comment %s>" % pprint.pformat({
                'body': self.body,
                'id': self.id,
                'user': self.user
                })


class Media(EqualityMixin):
    """
    A piece of media for a FriendFeed entry.

    :Parameters:
    - `title`: the title
    - `player`: media player
    - `link`: original link for the media
    - `thumbnails`: a list of thumbnails
    - `content`: a list of versions of the media
    - `enclosures`: a list of enclosuers for the media

    """

    def __init__(
            self,
            title=None,
            player=None,
            link=None,
            thumbnails=[],
            content=[],
            enclosures=[]
            ):

        self.title = title
        self.player = player
        self.link = link
        self.thumbnails = thumbnails
        self.content = content
        self.enclosures = enclosures


    def __repr__(self):

        return "<Media %s>" % self.title


class Entry(EqualityMixin, TruncateTextMixin):
    """
    A FriendFeed entry.

    :Parameters:
    - `id`: the entry ID [REQUIRED]
    - `title`: entry title
    - `link`: link for the entry (usually linking to the service entry)
    - `published`: date and time the entry was published
    - `updated`: date and time the entry was last updated
    - `hidden`: whether the entry is hidden [True or False]
    - `anonymous`: whether the entry is anonymous [True or False]
    - `user`: the user who posted this entry
    - `service`: the service the entry originated from
    - `comments`: a list of comments on the entry
    - `likes`: a list of "likes" for the entry
    - `media`: a list of media associated with the entry
    - `via`: the FriendFeed client used to post the entry
    - `room`: the room the entry is in (if posted in a room)
    - `geo`: latitude and longitude coordinates (provided by services
        such as Brightkite)

    """

    def __init__(
            self,
            id,
            title=None,
            link=None,
            published=None,
            updated=None,
            hidden=False,
            anonymous=False,
            user=None,
            service=None,
            comments=[],
            likes=[],
            media=[],
            via={},
            room=None,
            friend_of=None,
            geo={}
            ):

        self.id = id
        self.title = title
        self.link = link
        self.published = published
        self.updated = updated
        self.hidden = hidden
        self.anonymous = anonymous
        self.user = user
        self.service = service
        self.comments = comments
        self.likes = likes
        self.media = media
        self.via = via
        self.room = room
        self.friend_of = friend_of
        self.geo = geo


    def __repr__(self):

        if self.title:
            title = self.truncate_text(self.title, 50)
        else:
            title = self.title
        return "<Entry %s>" % pprint.pformat({
                'id': self.id,
                'likes': self.likes,
                'title': title,
                'user': self.user,
                'updated': self.updated,
                'hidden': self.hidden,
                })


class FriendFeedAPI(EqualityMixin):
    """
    A Python interface to the FriendFeed API.

    The credentials of `auth_nickname` and `auth_key` are optional for
    some operations, but required for private feeds and all operations
    that write data, like publish_link.

    :Parameters:
    - `auth_nickname`: the user name of the FriendFeed to
        authenticate
    - `auth_key`: the remote key of the FriendFeed account to
        authenticate (See http://friendfeed.com/account/api for more
        detail)
    - `via`: a string specifying the client [DEFAULT:
        'python-friendfeed']
    - `api_key`: a private FriendFeed API key
    - `urlopen`: function to retrieve HTTP streams
    - `HTTPError`: an exception thrown when an HTTP error occurs

    """

    # a series of maps to help dictate parsing behavior
    _comment_attr_map = {
            'id': 'id',
            'body': 'body',
            'via': 'via'
    }

    _entry_attr_map = {
            'anonymous': 'anonymous',
            'geo': 'geo',
            'hidden': 'hidden',
            'id': 'id',
            'title': 'title',
            'link': 'link',
            'via': 'via'
    }

    _list_attr_map = {
            'id': 'id',
            'name': 'name',
            'nickname': 'nickname',
            'url': 'url'
    }

    _media_attr_map = {
            'title': 'title',
            'player': 'player',
            'link': 'link',
            'thumbnails': 'thumbnails',
            'content': 'content'
    }

    _room_attr_map = {
            'description': 'description',
            'id': 'id',
            'name': 'name',
            'nickname': 'nickname',
            'url': 'url',
    }

    _service_attr_map = {
            'entryType': 'entry_type',
            'iconUrl': 'icon_url',
            'id': 'id',
            'name': 'name',
            'profileUrl': 'profile_url',
            'url': 'url',
            'username': 'username'
    }

    _user_attr_map = {
            'id': 'id',
            'name': 'name',
            'nickname': 'nickname',
            'profileUrl': 'profile_url',
    }


    def __init__(
            self,
            auth_nickname=None,
            auth_key=None,
            via='python-friendfeed',
            api_key=None,
            urlopen=urllib2.urlopen,
            HTTPError=urllib2.HTTPError
            ):

        self.auth_nickname = auth_nickname
        self.auth_key = auth_key
        self.via = via
        self.api_key = api_key
        self.urlopen = urlopen
        self.HTTPError = HTTPError

        if self.auth_nickname and self.auth_key:
            self._validate_authentication()

        self._comment_method_map = {
                'date': ('date', self._parse_date),
                'user': ('user', self._parse_user),
        }

        self._entry_method_map = {
                'comments': ('comments', self._parse_comments),
                'friendof': ('friend_of', self._parse_user),
                'likes': ('likes', self._parse_likes),
                'media': ('media', self._parse_media_files),
                'published': ('published', self._parse_date),
                'room': ('room', self._parse_room),
                'service': ('service', self._parse_service),
                'updated': ('updated', self._parse_date),
                'user': ('user', self._parse_user),
        }

        self._like_method_map = {
                'date': ('date', self._parse_date),
                'user': ('user', self._parse_user),
        }

        self._list_method_map = {
                'users': ('users', self._parse_users),
                'rooms': ('rooms', self._parse_rooms),
        }

        self._media_method_map = {
                'enclosures': ('enclosures', self._parse_enclosures),
        }

        self._room_method_map = {
                'administrators': ('administrators',
                    self._parse_users),
                'members': ('members', self._parse_users),
                'status': ('private', self._parse_privacy),
        }

        self._user_method_map = {
                'lists': ('lists', self._parse_sub_lists),
                'rooms': ('rooms', self._parse_rooms),
                'services': ('services', self._parse_services),
                'status': ('private', self._parse_privacy),
                'subscriptions': ('subscriptions',
                    self._parse_subscriptions),
        }


    def __repr__(self):

        return "<FriendFeedAPI nickname: %s, key: %s>" % (
                self.auth_nickname,
                self.auth_key
                )


    def _make_attrs_dict(
            self,
            struct,
            attr_map={},
            func_map={},
            *addtl_func_maps
            ):
        """
        Helper method to parse out dictionary structures to appropriate
        attributes for constructing class instances.

        :Parameters:
        - `struct`: a dictionary structure for parsing
        - `attr_map`: a mapping from the structure keys to attributes of
            the class
        - `func_map`: a mapping from structure keys to appropriate
            functions to process nested structures
        - `addtl_func_maps`: additional function maps

        IMPORTANT NOTE: the last definition for a function mapping will
        be the one used. That is, if `func_map` and a mapping in
        `addtl_func_maps` both have definitions (values) for the same
        key (e.g., 'users'), the last definition will be used.

        """

        attrs = {}
        if addtl_func_maps:
            for mapping in addtl_func_maps:
                func_map.update(mapping)
        for key, value in struct.items():
            if key in attr_map:
                attrs[attr_map[key]] = value
            elif key in func_map:
                attr, func = func_map[key]
                result = func(value)
                attrs[attr] = result
            else:
                raise KeyError("No mapping available for %s." % (key))
        return attrs


    def _parse_comment(self, comment):
        """
        Parses a comment dictionary and returns a `Comment` instance.

        :Parameters:
        - `comment`: a comment

        """

        attrs = self._make_attrs_dict(
                comment,
                self._comment_attr_map,
                self._comment_method_map
                )
        return Comment(**attrs)


    def _parse_comments_iter(self, comments):
        """
        Parses a list of comments and yields a `Comment` instance for
        each.

        NOTE: Returns an iterator.

        :Parameters:
        - `comments`: a list of comments

        """

        for comment in comments:
            yield self._parse_comment(comment)


    def _parse_comments(self, comments):
        """
        Parses a list of comments and returns a list of `Comment`
        instances.

        :Parameters:
        - `comments`: a list of comments

        """

        return list(self._parse_comments_iter(comments))


    def _parse_date(self, date_str):
        """
        Parse a date string into a `datetime` instance.

        :Parameters:
        - `date_str`: a date string

        """

        rfc3339_date = "%Y-%m-%dT%H:%M:%SZ"
        return datetime.datetime(
                *time.strptime(date_str, rfc3339_date)[:6]
        )


    def _parse_enclosures(self, enc_struct):
        """
        Parse an enclosures structure.

        :Parameters:
        - `enc_struct`: an enclosures structure

        NOTE: This method is in place because currently (2008-12-28) the
        FriendFeed API returns `null` if there are no enclosures, rather
        than an empty list.

        """

        if enc_struct is None:
            return []
        else:
            return enc_struct


    def _parse_entry(self, entry):
        """
        Parse an entry structure and return an `Entry` instance.

        :Parameters:
        - `entry`: an entry structure

        """

        attrs = self._make_attrs_dict(
                entry,
                self._entry_attr_map,
                self._entry_method_map
                )
        return Entry(**attrs)


    def _parse_entries_iter(self, entries):
        """
        Parse a list of entry structures and yield an `Entry` instance
        for each.

        NOTE: Returns an iterator.

        :Parameters:
        - `entries`: a list of entry structures

        """

        for entry in entries:
            yield self._parse_entry(entry)


    def _parse_entries(self, entries):
        """
        Parse a list of entry structures and return a list of `Entry`
        instances.

        :Parameters:
        - `entries`: a list of entry structures

        """

        return list(self._parse_entries_iter(entries))


    def _parse_like(self, like):
        """
        Parse a "like".

        :Parameters:
        - `like`: a like dictionary

        """

        parsed_like = self._make_attrs_dict(
                like,
                func_map=self._like_method_map
                )
        return parsed_like


    def _parse_likes_iter(self, likes):
        """
        Parses several "like"s and yields each parsed one.

        NOTE: Returns an iterator.

        :Parameters:
        - `likes`: a list of likes

        """

        for like in likes:
            yield self._parse_like(like)


    def _parse_likes(self, likes):
        """
        Returns a list of parsed "like"s.

        :Parameters:
        - `likes`: a list of likes

        """

        return list(self._parse_likes_iter(likes))


    def _parse_media_file(self, media_file):
        """
        Parse a media file and return a `Media` instance.

        :Parameters:
        - `media_file`: a media file structure

        """

        attrs = self._make_attrs_dict(
                media_file,
                self._media_attr_map,
                self._media_method_map
                )
        return Media(**attrs)


    def _parse_media_files_iter(self, media_files):
        """
        Parse a list of media files and yield a `Media` instance for
        each.

        NOTE: Returns an iterator.

        :Parameters:
        - `media_files`: a list of media file structures

        """

        for media_file in media_files:
            yield self._parse_media_file(media_file)


    def _parse_media_files(self, media_files):
        """
        Parse a list of media files and return a list of `Media`
        instances.

        :Parameters:
        - `media_files`: a list of media file structures

        """

        return list(self._parse_media_files_iter(media_files))


    def _parse_room(self, room_profile):
        """
        Parse a room dictionary and return a `Room` instance.

        :Parameters:
        - `room_profile`: a room profile dictionary

        """

        attrs = self._make_attrs_dict(
                room_profile,
                self._room_attr_map,
                self._room_method_map
                )
        return Room(**attrs)


    def _parse_rooms_iter(self, room_profiles):
        """
        Parses multiple room dictionaries and yields a `Room` instance for
        each.

        NOTE: Returns an iterator.

        :Parameters:
        - `room_profiles`: a room profile dictionary

        """

        for room_profile in room_profiles:
            yield self._parse_room(room_profile)


    def _parse_rooms(self, room_profiles):
        """
        Parses multiple room dictionaries and returns a list of `Room`
        instances.

        :Parameters:
        - `room_profiles`: a room profile dictionary

        """

        return list(self._parse_rooms_iter(room_profiles))


    def _parse_service(self, service_struct):
        """
        Parse a service dictionary and return a `Service` instance.

        :Parameters:
        - `service_struct`: a service dictionary

        """

        attrs = self._make_attrs_dict(
                service_struct,
                self._service_attr_map
                )
        service = Service(**attrs)
        return service


    def _parse_services_iter(self, service_structs):
        """
        Parse several service dictionaries and yield each as a `Service`
        instance.

        NOTE: Returns an iterator.

        :Parameters:
        - `service_structs`: dictionaries of services

        """

        for service_struct in service_structs:
            yield self._parse_service(service_struct)


    def _parse_services(self, service_structs):
        """
        Parse several service dictionaries and return a list of
        `Service` instances.

        :Parameters:
        - `service_structs`: dictionaries of services

        """

        return list(self._parse_services_iter(service_structs))


    def _parse_privacy(self, status):
        """
        Parses status to determine privacy.

        Returns `True` if the status is 'private' and `False` if status
        is 'public'.

        :Parameters:
        - `status`: either 'public' or 'private'

        """

        status = status.lower()
        if status == 'private':
            return True
        elif status == 'public':
            return False
        else:
            raise ValueError("Status should be either private or public.")


    def _parse_sub_list(self, sub_list):
        """
        Parse a subscription list dictionary and return a
        `SubscrptionList` instance.

        :Parameters:
        - `sub_list`: a subscription list dictionary

        """

        attrs = self._make_attrs_dict(
                sub_list,
                self._list_attr_map,
                self._list_method_map
                )
        return SubscriptionList(**attrs)


    def _parse_sub_lists_iter(self, sub_lists):
        """
        Parses subscription list dictionaries and yields
        `SubscriptionList` instances.

        NOTE: Returns an iterator.

        :Parameters:
        - `sub_lists`: a list of subscription list dictionaries

        """

        for sub_list in sub_lists:
            yield self._parse_sub_list(sub_list)


    def _parse_sub_lists(self, sub_lists):
        """
        Parses subscription list dictionaries and returns
        a list of `SubscriptionList` instances.

        :Parameters:
        - `sub_lists`: a list of subscription list dictionaries

        """

        return list(self._parse_sub_lists_iter(sub_lists))


    def _parse_subscriptions_iter(self, subscriptions):
        """
        Parses user subscriptions and yields a `User` instance for each
        user, and an `ImaginaryFriend` instance for each "imaginary
        friend".

        NOTE: Returns an iterator.

        :Parameters:
        - `subscriptions`: a list of subscriptions

        """

        for subscription in subscriptions:
            attrs = self._make_attrs_dict(
                    subscription,
                    self._user_attr_map,
                    self._user_method_map
                    )
            if attrs['nickname'] is None:
                del attrs['nickname']
                yield ImaginaryFriend(**attrs)
            else:
                yield User(**attrs)


    def _parse_subscriptions(self, subscriptions):
        """
        Parses user subscriptions and returs a list of a `User`
        instances for each user and `ImaginaryFriend` instances for each
        "imaginary friend".

        :Parameters:
        - `subscriptions`: a list of subscriptions

        """

        return list(self._parse_subscriptions_iter(subscriptions))


    def _parse_user(self, profile):
        """
        Parse a user dictionary and return a `User` instance.

        :Parameters:
        - `profile`: a user profile dictionary

        """

        attrs = self._make_attrs_dict(
                profile,
                self._user_attr_map,
                self._user_method_map
                )
        return User(**attrs)


    def _parse_users_iter(self, profiles):
        """
        Parses multiple user dictionaries and yields a `User` instance
        for each.

        NOTE: Returns an iterator.

        :Parameters:
        - `profiles`: a user profile dictionary

        """

        for profile in profiles:
            yield self._parse_user(profile)


    def _parse_users(self, profiles):
        """
        Parses multiple user dictionaries and return a list of `User`
        instances.

        :Parameters:
        - `profiles`: a user profile dictionary

        """

        return list(self._parse_users_iter(profiles))


    def _check_for_error(self, response):
        """
        Checks to see if an error was returned in the server repsonse,
        and raises the appropriate error if one is found.

        :Parameters:
        - `response`: the parsed JSON response

        """

        if 'errorCode' in response:
            error_code = response['errorCode']
            if error_code in FF_ERROR_MAPPING:
                raise FF_ERROR_MAPPING[error_code]
            else:
                raise KeyError("Error '%s' unknown." % error_code)


    def _urlencode(self, args):
        """
        Allows for posting unicode in headers.

        """

        unicode_args = []
        for k, v in args.items():
            unicode_args.append(
                    u'%s=%s' % (
                        urllib.quote(k.encode('utf-8')),
                        urllib.quote(v.encode('utf-8'))
                    )
            )
        return u'&'.join(unicode_args)


    def _make_auth_headers(self):
        """
        Set HTTP request headers based on authentication.

        """

        headers = {}
        # If we have enough information from the user, we can
        # authenticate
        if self.auth_nickname and self.auth_key:
            pair = '%s:%s' % (self.auth_nickname, self.auth_key)
            token = base64.b64encode(pair)
            headers['Authorization'] = 'Basic %s' % token
        return headers


    def _fetch(
            self,
            resource,
            post_args={},
            url_args={},
            files=[]
            ):
        """
        Makes a request and returns the JSON output.

        :Parameters:
        - `resource`: the API resource (location) requested
        - `post_args`: a dictionary of arguments if this is a POST
            request
        - `url_args`: extra arguments for the URI string
        - `files`: files for uploading

        `files` should be a list of dictionaries of the form
        `{'file': <FILE_HANDLE>, 'link': 'http://example.com/'}`
        where the key/value pair of `'link'` is optional.

        """

        # Make sure we request JSON formatting
        url_args['format'] = 'json'
        uri = self.make_uri(resource, url_args)
        headers = self._make_auth_headers()
        # We have two forms of POST requests possible: those with files,
        # and those without.
        # First, handle the case with files.
        if files:
            # We need the poster package to upload files
            if poster:
                for i, fdict in enumerate(files):
                    # add a file "name" and associated file handle to
                    # post_args
                    fname = 'file%d' % i
                    fileh = fdict['file']
                    post_args[fname] = fileh
                    if 'link' in fdict:
                        flink = '%s_link' % fname
                        post_args[flink] = fdict['link']
                datagen, data_headers = poster.encode.multipart_encode(
                        post_args)
                headers.update(data_headers)
                request = urllib2.Request(uri, datagen, headers)
            else:
                raise ImportError("The poster package is required for"
                    " uploading files.")
        # Here we handle a simpler POST request with no files
        elif post_args:
            request = urllib2.Request(
                    uri,
                    self._urlencode(post_args),
                    headers
                    )
        # Otherwise, this is a GET request
        else:
            request = urllib2.Request(uri, headers=headers)
        stream = self.urlopen(request)
        data = stream.read()
        stream.close()
        response = parse_json(data)
        self._check_for_error(response)
        return response


    #def _fetch_feed(self, uri, post_args={}, **kwargs):
        #"""Publishes to the given URI and parses the returned JSON feed."""

        ## Parse all the dates in the result JSON
        #result = self._fetch(uri, post_args, **kwargs)
        #date_properties = frozenset(("updated", "published"))
        #for entry in result.get("entries", []):
            #entry["updated"] = self._parse_date(entry["updated"])
            #entry["published"] = self._parse_date(entry["published"])
            #for comment in entry.get("comments", []):
                #comment["date"] = self._parse_date(comment["date"])
            #for like in entry.get("likes", []):
                #like["date"] = self._parse_date(like["date"])
        #return result


    def _check_start_arg(self, start):
        """Checks that start is a non-negative integer."""

        if (not isinstance(start, int) or int < 0):
            MSG = "start must be a non-negative integer"
            raise ValueError(MSG)


    def _check_num_arg(self, num):
        """Checks that num is a positive integer."""

        if (not isinstance(num, int) or int < 1):
            MSG = "num must be a positive integer"
            raise ValueError(MSG)


    def _make_feed_args_dict(self, service=None, start=None, num=None):
        """
        Takes the standard query arguments for a feed and returns a
        dictionary containing the arguments.

        :Parameters:
        - `service`: retrieve only entries for this service [should be a
            `Service` instance or a string]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        url_args = {}
        if service:
            if isinstance(service, Service):
                service = service.id
            elif not isinstance(service, (str, (str, unicode))):
                MSG = "service should be a Service instance or string"
                raise ValueError(MSG)
            url_args['service'] = service
        if start is not None:
            self._check_start_arg(start)
            url_args['start'] = start
        if num is not None:
            url_args['num'] = num
        return url_args


    def _get_comment_id(self, comment):
        """
        Obtains an id from a `Comment` instance or a string; otherwise
        raises a `ValueError`.

        :Parameters:
        - `comment`: a `Comment` instance or a string

        """

        if isinstance(comment, Comment):
            comment_id = comment.id
        elif isinstance(comment, (str, unicode)):
            comment_id = comment
        else:
            MSG = "comment must be a Comment instance or string"
            raise ValueError(MSG)
        return comment_id


    def _get_entry_id(self, entry):
        """
        Obtains an id from an `Entry` instance or a string; otherwise
        raises a `ValueError`.

        :Parameters:
        - `entry`: an `Entry` instance or a string

        """

        if isinstance(entry, Entry):
            entry_id = entry.id
        elif isinstance(entry, (str, unicode)):
            entry_id = entry
        else:
            MSG = "entry must be an Entry instance or string"
            raise ValueError(MSG)
        return entry_id


    def _get_user_nickname(self, user):
        """
        Obtains a nickname from a `User` instance or a string; otherwise
        raises a `ValueError`.

        :Parameters:
        - `user`: a `User` instance or a string

        """

        if isinstance(user, User):
            nickname = user.nickname
        elif isinstance(user, (str, unicode)):
            nickname = user
        else:
            raise ValueError("user must be a User instance or string")
        return nickname


    def _get_service_id(self, service):
        """
        Obtains the id of a service from a `Service` instance or a
        string; otherwise raises a `ValueError`.

        :Parameters:
        - `service`: a `Service` instance or a string.

        """

        if isinstance(service, Service):
            sid = service.id
        elif isinstance(service, (str, unicode)):
            sid = service
        else:
            MSG = "service must be a Service instance or string"
            raise ValueError(MSG)
        return sid


    def _get_service_name(self, service):
        """
        Obtains the name of a service from a `Service` instance or a
        string; otherwise raises a `ValueError`.

        :Parameters:
        - `service`: a `Service` instance or a string.

        """

        if isinstance(service, Service):
            name = service.name
        elif isinstance(service, (str, unicode)):
            name = service
        else:
            MSG = "service must be a Service instance or string"
            raise ValueError(MSG)
        return name


    def _get_room_nickname(self, room):
        """
        Obtains the nickname of a room from a `Room` instance or a
        string; otherwise raises a `ValueError`.

        :Parameters:
        - `room`: a `Room` instance or a string.

        """

        if isinstance(room, Room):
            nickname = room.nickname
        elif isinstance(room, (str, unicode)):
            nickname = room
        else:
            MSG = "room must be a Room instance or string"
            raise ValueError(MSG)
        return nickname


    def _get_list_name(self, subscription_list):
        """
        Obtains the name of a list from a `SubscriptionList` instance or
        a string; otherwise raises a `ValueError`.

        :Parameters:
        - `subscription_list`: a `SubscriptionList` instance or a
          string.

        """

        if isinstance(subscription_list, SubscriptionList):
            name = subscription_list.nickname
        elif isinstance(subscription_list, (str, unicode)):
            name = subscription_list
        else:
            MSG = ("subscription_list must be a SubscriptionList"
                    " instance or string")
            raise ValueError(MSG)
        return name


    def _update_user_from_profile(self, user, profile):
        """
        Updates a `User` instances attributes.

        :Parameters:
        - `user`: a `User` instance
        - `profile`: a user profile dictionary

        """

        attrs = self._make_attrs_dict(
                profile,
                self._user_attr_map,
                self._user_method_map
                )
        assert user.nickname == attrs['nickname']
        for attr, value in attrs.items():
            setattr(user, attr, value)


    def _ensure_authenticated(self):
        """
        Checks to make sure the session is authenticated, and raises an
        `UnauthorizedError` if not.

        """

        if not (self.auth_nickname and self.auth_key):
            MSG = ("Requires authentication. Instantiate with auth_name"
                    " and auth_key.")
            raise UnauthorizedError(MSG)


    def _ensure_api_key(self):
        """
        Checks to make sure the session has an API key, and raises an
        `UnauthorizedError` if not.

        """

        if not (self.api_key):
            MSG = ("Requires an API key. Instantiate with api_key.")
            raise UnauthorizedError(MSG)


    def _ensure_api_key_authenticated(self):
        """
        Checks to make sure the session has user credentials and an API
        key, and raises an `UnauthorizedError` if not.

        """

        self._ensure_authenticated()
        self._ensure_api_key()


    def _validate_authentication(self):
        """
        Checks to see if the authentication credentials provided are
        valid.

        Raises an `UnauthorizedError` if authentication is invalid.

        :Parameters:
        - `nickname`: a user nickname
        - `key`: a remote key

        """

        self._ensure_authenticated()
        try:
            self._fetch('/validate')
        except self.HTTPError, error:
            if error.code == 401:
                MSG = ("Could not authenticate with provided name and"
                        " key.")
                raise UnauthorizedError(MSG)
            else:
                raise error


    def make_uri(self, resource, parameters={}):
        """
        Makes a full URI for the location.

        :Parameters:
        - `resource`: The resource (location) of interest
        - `parameters`: a dictionary of parameters for the request
          (e.g., query parameters)

        """

        DOMAIN = 'http://friendfeed.com'
        API_LOC = '/api'
        if parameters:
            uri = "%s%s%s?%s" % (DOMAIN, API_LOC, resource,
                    urllib.unquote(self._urlencode(parameters))
        )
        else:
            uri = "%s%s%s" % (DOMAIN, API_LOC, resource)
        return uri


    def fetch_public_feed_iter(self, service=None, start=None, num=None):
        """
        Yields an `Entry` instance for each entry in the public feed.

        NOTE: Returns an iterator.

        :Parameters:
        - `service`: retrieve only entries for this service [should be a
            `Service` instance or a string]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        url_args = self._make_feed_args_dict(service, start, num)
        response = self._fetch('/feed/public', url_args=url_args)
        entries = self._parse_entries_iter(response['entries'])
        return entries


    def fetch_public_feed(self, service=None, start=None, num=None):
        """
        Returns a list of `Entry` instances for each entry in the public
        feed.

        :Parameters:
        - `service`: retrieve only entries for this service [should be a
            `Service` instance or a string]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        return list(self.fetch_public_feed_iter(service, start, num))


    def fetch_user_feed_iter(
            self,
            user,
            service=None,
            start=None,
            num=None
            ):
        """
        Yields an `Entry` instance for each entry in the user's feed.

        Authentication is required if the user's feed is not public.

        NOTE: Returns an iterator.

        :Parameters:
        - `user`: a `User` instance, or the nickname of a user
        - `service`: retrieve only entries for this service [should be a
            `Service` instance or a string]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        url_args = self._make_feed_args_dict(service, start, num)
        nickname = self._get_user_nickname(user)
        response = self._fetch('/feed/user/%s' % nickname,
                url_args=url_args)
        entries = self._parse_entries_iter(response['entries'])
        return entries


    def fetch_user_feed(
            self,
            user,
            service=None,
            start=None,
            num=None
            ):
        """
        Returns a list of an `Entry` instances for each entry in the
        user's feed.

        Authentication is required if the user's feed is not public.

        :Parameters:
        - `user`: a `User` instance, or the nickname of a user
        - `service`: retrieve only entries for this service [should be a
            `Service` instance or a string]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        return list(self.fetch_user_feed_iter(
                user, service, start, num))


    def fetch_user_comments_feed_iter(
            self,
            user,
            service=None,
            start=None,
            num=None
            ):
        """
        Yields an `Entry` instance for each entry on which a user has
        commented.

        Authentication is required if the user's feed is not public.

        NOTE: Returns an iterator.

        :Parameters:
        - `user`: a `User` instance, or the nickname of a user
        - `service`: retrieve only entries for this service [should be a
            `Service` instance or a string]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        url_args = self._make_feed_args_dict(service, start, num)
        nickname = self._get_user_nickname(user)
        response = self._fetch('/feed/user/%s/comments' % nickname,
                url_args=url_args)
        entries = self._parse_entries_iter(response['entries'])
        return entries


    def fetch_user_comments_feed(
            self,
            user,
            service=None,
            start=None,
            num=None
            ):
        """
        Returns a list of `Entry` instances for each entry on which a user
        has commented.

        Authentication is required if the user's feed is not public.

        :Parameters:
        - `user`: a `User` instance, or the nickname of a user
        - `service`: retrieve only entries for this service [should be a
            `Service` instance or a string]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        return list(self.fetch_user_comments_feed_iter(
                user, service, start, num))


    def fetch_user_likes_feed_iter(
            self,
            user,
            service=None,
            start=None,
            num=None
            ):
        """
        Yields an `Entry` instance for each entry a user has "liked".

        Authentication is required if the user's feed is not public.

        NOTE: Returns an iterator.

        :Parameters:
        - `user`: a `User` instance, or the nickname of a user
        - `service`: retrieve only entries for this service [should be a
            `Service` instance or a string]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        url_args = self._make_feed_args_dict(service, start, num)
        nickname = self._get_user_nickname(user)
        response = self._fetch('/feed/user/%s/likes' % nickname,
                url_args=url_args)
        entries = self._parse_entries_iter(response['entries'])
        return entries


    def fetch_user_likes_feed(
            self,
            user,
            service=None,
            start=None,
            num=None
            ):
        """
        Returns a list of `Entry` instances for each entry a user has
        "liked".

        Authentication is required if the user's feed is not public.

        :Parameters:
        - `user`: a `User` instance, or the nickname of a user
        - `service`: retrieve only entries for this service [should be a
            `Service` instance or a string]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        return list(self.fetch_user_likes_feed_iter(
                user, service, start, num))


    def fetch_user_discussion_feed_iter(
            self,
            user,
            service=None,
            start=None,
            num=None
            ):
        """
        Yields an `Entry` instance for each entry on which a user has
        commented or "liked".

        Authentication is required if the user's feed is not public.

        NOTE: Returns an iterator.

        :Parameters:
        - `user`: a `User` instance, or the nickname of a user
        - `service`: retrieve only entries for this service [should be a
            `Service` instance or a string]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        url_args = self._make_feed_args_dict(service, start, num)
        nickname = self._get_user_nickname(user)
        response = self._fetch('/feed/user/%s/discussion' % nickname,
                url_args=url_args)
        entries = self._parse_entries_iter(response['entries'])
        return entries


    def fetch_user_discussion_feed(
            self,
            user,
            service=None,
            start=None,
            num=None
            ):
        """
        Returns a list of `Entry` instances for each entry on which a user
        has commented or "liked".

        Authentication is required if the user's feed is not public.

        :Parameters:
        - `user`: a `User` instance, or the nickname of a user
        - `service`: retrieve only entries for this service [should be a
            `Service` instance or a string]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        return list(self.fetch_user_discussion_feed_iter(
                user, service, start, num))


    def fetch_friends_feed_iter(
            self,
            user,
            service=None,
            start=None,
            num=None
            ):
        """
        Yields an `Entry` instance for each entry from a user's friends
        feed.

        Authentication is required if the user's feed is not public.

        NOTE: Returns an iterator.

        :Parameters:
        - `user`: a `User` instance, or the nickname of a user
        - `service`: retrieve only entries for this service [should be a
            `Service` instance or a string]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        url_args = self._make_feed_args_dict(service, start, num)
        nickname = self._get_user_nickname(user)
        response = self._fetch('/feed/user/%s/friends' % nickname,
                url_args=url_args)
        entries = self._parse_entries_iter(response['entries'])
        return entries


    def fetch_friends_feed(
            self,
            user,
            service=None,
            start=None,
            num=None
            ):
        """
        Returns a list of `Entry` instances for each entry from a user's
        friends feed.

        Authentication is required if the user's feed is not public.

        :Parameters:
        - `user`: a `User` instance, or the nickname of a user
        - `service`: retrieve only entries for this service [should be a
            `Service` instance or a string]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        return list(self.fetch_friends_feed_iter(
                user, service, start, num))


    def fetch_multi_user_feed_iter(
            self,
            users,
            service=None,
            start=None,
            num=None
            ):
        """
        Yields an `Entry` instance for each entry in the given users'
        feeds.

        Authentication is required if any one of the users' feed is not
        public.

        NOTE: Returns an iterator.

        :Parameters:
        - `users`: a list of `User` instances, or the nicknames of users
        - `service`: retrieve only entries for this service [should be a
            `Service` instance or a string]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        url_args = self._make_feed_args_dict(service, start, num)
        nicknames = []
        for user in users:
            nickname = self._get_user_nickname(user)
            nicknames.append(nickname)
        url_args['nickname'] = ','.join(nicknames)
        response = self._fetch('/feed/user', url_args=url_args)
        entries = self._parse_entries_iter(response['entries'])
        return entries


    def fetch_multi_user_feed(
            self,
            users,
            service=None,
            start=None,
            num=None
            ):
        """
        Returns a list of an `Entry` instances for each entry in the
        users' feeds.

        Authentication is required if the user's feed is not public.

        :Parameters:
        - `users`: a list of `User` instances, or the nicknames of users
        - `service`: retrieve only entries for this service [should be a
            `Service` instance or a string]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        return list(self.fetch_multi_user_feed_iter(
                users, service, start, num))


    def fetch_home_feed_iter(
            self,
            service=None,
            start=None,
            num=None
            ):
        """
        Yields an `Entry` instance for each entry in the home feed of the
        authenticated user.

        NOTE: AUTHENTICATION IS REQUIRED.

        NOTE: Returns an iterator.

        :Parameters:
        - `service`: retrieve only entries for this service [should be a
            `Service` instance or a string]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        url_args = self._make_feed_args_dict(service, start, num)
        self._ensure_authenticated()
        response = self._fetch('/feed/home', url_args=url_args)
        entries = self._parse_entries_iter(response['entries'])
        return entries


    def fetch_home_feed(
            self,
            service=None,
            start=None,
            num=None
            ):
        """
        Returns a list of an `Entry` instances for each entry in the
        authenticated user's home feed.

        NOTE: AUTHENTICATION IS REQUIRED.

        :Parameters:
        - `service`: retrieve only entries for this service [should be a
            `Service` instance or a string]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        return list(self.fetch_home_feed_iter(service, start, num))


    def fetch_rooms_feed_iter(
            self,
            service=None,
            start=None,
            num=None
            ):
        """
        Yields an `Entry` instance for each entry in the rooms feed of the
        authenticated user.

        NOTE: AUTHENTICATION IS REQUIRED.

        NOTE: Returns an iterator.

        :Parameters:
        - `service`: retrieve only entries for this service [should be a
            `Service` instance or a string]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        url_args = self._make_feed_args_dict(service, start, num)
        self._ensure_authenticated()
        response = self._fetch('/feed/rooms', url_args=url_args)
        entries = self._parse_entries_iter(response['entries'])
        return entries


    def fetch_rooms_feed(
            self,
            service=None,
            start=None,
            num=None
            ):
        """
        Returns a list of an `Entry` instances for each entry in the
        authenticated user's rooms feed.

        NOTE: AUTHENTICATION IS REQUIRED.

        :Parameters:
        - `service`: retrieve only entries for this service [should be a
            `Service` instance or a string]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        return list(self.fetch_rooms_feed_iter(service, start, num))


    def fetch_url_feed_iter(
            self,
            url,
            users=None,
            rooms=None,
            subscribed=False,
            start=None,
            num=None
            ):
        """
        Yields an `Entry` instance for each entry linking to the given
        URL. The search can be restricted to entries by users or rooms.
        If authenticated, entries can be restricted to those belonging
        to the authenticated user's subscriptions by setting
        `subscribed` to `True`.

        If authenticated, private entries will be fetched; otherwise,
        returns entries in the public feed.

        NOTE: Returns an iterator.

        :Parameters:
        - `url`: the URL of interest
        - `users`: a list of `User` instances, or the nicknames of users
        - `rooms`: a list of `Room` instances, or the nicknames of rooms
        - `subscribed`: return only entries in subscriptions [Default:
            `False`] [NOTE: AUTHENTICATION REQUIRED WHEN SET TO `True`]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        url_args = self._make_feed_args_dict(start=start, num=num)

        if subscribed is True:
            try:
                self._ensure_authenticated()
            except UnauthorizedError:
                MSG = ("Authentication name and key required to use "
                        "subscription parameter.")
                raise UnauthorizedError(MSG)
            url_args['subscribed'] = 1

        if users or rooms:
            nicknames = []
            if users:
                for user in users:
                    nickname = self._get_user_nickname(user)
                    nicknames.append(nickname)
            if rooms:
                for room in rooms:
                    nickname = self._get_room_nickname(room)
                    nicknames.append(nickname)
            url_args['nickname'] = ','.join(nicknames)

        url_args['url'] = url
        response = self._fetch('/feed/url', url_args=url_args)
        entries = self._parse_entries_iter(response['entries'])
        return entries


    def fetch_url_feed(
            self,
            url,
            users=None,
            rooms=None,
            subscribed=False,
            start=None,
            num=None
            ):
        """
        Returns a list of `Entry` instances for each entry linking to the
        given URL. The search can be restricted to entries by users or
        rooms. If authenticated, the search can be restricted to entries
        belonging to the authenticated user's subscriptions by setting
        `subscribed` to `True`.

        If authenticated, private entries will be fetched; otherwise,
        returns entries in the public feed.

        :Parameters:
        - `url`: the URL of interest
        - `users`: a list of `User` instances, or the nicknames of users
        - `rooms`: a list of `Room` instances, or the nicknames of rooms
        - `subscribed`: return only entries in subscriptions [Default:
            `False`] [NOTE: AUTHENTICATION REQUIRED WHEN SET TO `True`]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        return list(self.fetch_url_feed_iter(
                url, users, rooms, subscribed, start, num))


    def fetch_domains_feed_iter(
            self,
            domains,
            users=None,
            rooms=None,
            subscribed=False,
            inexact=False,
            start=None,
            num=None
            ):
        """
        Yields an `Entry` instance for each entry linking to a domain in
        the given domains URL. The search can be restricted to entries
        by users or rooms. If authenticated, entries can be restricted
        to those belonging to the authenticated user's subscriptions by
        setting `subscribed` to `True`. The search may be broadened by
        setting `inexact` to `True`.

        If authenticated, private entries will be fetched; otherwise,
        returns entries in the public feed.

        NOTE: Returns an iterator.

        :Parameters:
        - `domains`: a list of domains of interest
        - `users`: a list of `User` instances, or the nicknames of users
        - `rooms`: a list of `Room` instances, or the nicknames of rooms
        - `subscribed`: return only entries in subscriptions [Default:
            `False`] [NOTE: AUTHENTICATION REQUIRED WHEN SET TO `True`]
        - `inexact`: allow matching of subdomains [Default: False]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        url_args = self._make_feed_args_dict(start=start, num=num)

        if subscribed is True:
            try:
                self._ensure_authenticated()
            except UnauthorizedError:
                MSG = ("Authentication name and key required to use "
                        "subscription parameter.")
                raise UnauthorizedError(MSG)
            url_args['subscribed'] = 1

        if users or rooms:
            nicknames = []
            if users:
                for user in users:
                    nickname = self._get_user_nickname(user)
                    nicknames.append(nickname)
            if rooms:
                for room in rooms:
                    nickname = self._get_room_nickname(room)
                    nicknames.append(nickname)
            url_args['nickname'] = ','.join(nicknames)

        if inexact is True:
            url_args['inexact'] = 1

        url_args['domain'] = ','.join(domains)
        response = self._fetch('/feed/domain', url_args=url_args)
        entries = self._parse_entries_iter(response['entries'])
        return entries


    def fetch_domains_feed(
            self,
            domains,
            users=None,
            rooms=None,
            subscribed=False,
            inexact=False,
            start=None,
            num=None
            ):
        """
        Returns a list of `Entry` instances for each entry linking to a
        domain in the given domains URL. The search can be restricted to
        entries by users or rooms. If authenticated, entries can be
        restricted to those belonging to the authenticated user's
        subscriptions by setting `subscribed` to `True`. The search may
        be broadened by setting `inexact` to `True`.

        If authenticated, private entries will be fetched; otherwise,
        returns entries in the public feed.

        :Parameters:
        - `domains`: a list of domains of interest
        - `users`: a list of `User` instances, or the nicknames of users
        - `rooms`: a list of `Room` instances, or the nicknames of rooms
        - `subscribed`: return only entries in subscriptions [Default:
            `False`] [NOTE: AUTHENTICATION REQUIRED WHEN SET TO `True`]
        - `inexact`: allow matching of subdomains [Default: False]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        return list(self.fetch_domains_feed_iter(
                domains, users, rooms, subscribed, inexact, start, num))


    def fetch_room_feed_iter(
            self,
            room,
            service=None,
            start=None,
            num=None
            ):
        """
        Yields an `Entry` instance for each entry in the room's feed.

        Authentication is required if the room's feed is not public.

        NOTE: Returns an iterator.

        :Parameters:
        - `room`: a `Room` instance, or the nickname of a room
        - `service`: retrieve only entries for this service [should be a
            `Service` instance or a string]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        url_args = self._make_feed_args_dict(service, start, num)
        nickname = self._get_room_nickname(room)
        response = self._fetch('/feed/room/%s' % nickname,
                url_args=url_args)
        entries = self._parse_entries_iter(response['entries'])
        return entries


    def fetch_room_feed(
            self,
            room,
            service=None,
            start=None,
            num=None
            ):
        """
        Returns a list of `Entry` instances for each entry in the room's
        feed.

        Authentication is required if the room's feed is not public.

        :Parameters:
        - `room`: a `Room` instance, or the nickname of a room
        - `service`: retrieve only entries for this service [should be a
            `Service` instance or a string]
        - `start`: retrieve entries starting from this index [should be
            a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
            integer]

        """

        return list(self.fetch_room_feed_iter(
                room, service, start, num))


    def fetch_entry(self, entry_id):
        """
        Fetches the entry of the specified entry ID.

        Authentication is required if the entry is private.

        :Parameters:
        - `entry_id`: the UUID of the entry to fetch

        """

        response = self._fetch('/feed/entry/%s' % entry_id)
        return self._parse_entry(response['entries'][0])


    def search_iter(
            self,
            terms=[],
            excl_terms=[],
            users=[],
            excl_users=[],
            rooms=[],
            excl_rooms=[],
            services=[],
            excl_services=[],
            friends_of=[],
            excl_friends_of=[],
            in_title=[],
            excl_in_title=[],
            in_comment=[],
            excl_in_comment=[],
            comments_by=[],
            excl_comments_by=[],
            liked_by=[],
            excl_liked_by=[],
            min_comments=None,
            max_comments=None,
            min_likes=None,
            max_likes=None,
            start=None,
            num=None
            ):
        """
        Searches over entries in FriendFeed and yields an `Entry` instance
        for each entry matching the search specifications.

        If an authentication name and key is provided, the default scope
        is over all of the entries in the authenticated user's Friends
        Feed. If authentication credentials were not provided, the
        default scope is over all public entries.

        Many of the search parameters for refining the search space have
        complementary parameters for excluding entries; for example,
        `users` which restricts entries returned to only those from this
        list of users, has a complementary parameter `excl_users`, which
        will exclude all entries from this list of users.

        NOTE: Returns an iterator.

        :Parameters:
        - `terms`: a list of terms; restrict entries to those containing
          any of these terms in entry titles or comments
        - `users`: a list of users (user names or `User` instances);
          restrict entries to those from these users' feeds
        - `excl_users`: exclude entries by these users
        - `rooms`: a list of rooms (room names or `Room` instances);
          restrict entries to those from these rooms' feeds
        - `excl_rooms`: exclude entries in these rooms
        - `services`: a list of services (service names or `Service`
          instances); restrict entries to those from these services
        - `excl_services`: exclude entries from these services
        - `friends_of`: a list of users; include entries from friends of
          these users
        - `excl_friends_of`: exclude entries from friends of these users
        - `in_title`: a list of terms to search for only in entry titles
        - `excl_in_title`: exclude entries with these terms in titles
        - `in_comment`: a list of terms to search for only in comments
        - `excl_in_comment`: exclude entries with these terms in
          comments
        - `comments_by`: a list of users, to include entries commented
          on by
        - `excl_comments_by`: exclude entries with comments by these
          users
        - `liked_by`: a list of users; include entries "liked" by these
          users
        - `excl_liked_by`: exclude entries liked by these users
        - `min_comments`: return entries with specified minimum number
          of comments [should be a positive integer]
        - `max_comments`: return entries with specified maximum number
          of comments [should be a positive integer]
        - `min_likes`: return entries with specified minimum number of
          "likes" [should be a positive integer]
        - `max_likes`: return entries with specified maximum number of
          "likes" [should be a positive integer]
        - `start`: retrieve entries starting from this index [should be
          a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
          integer]

        """

        # We need to send None as the service, because we handle
        # services differently here, since we can include multiple
        url_args = self._make_feed_args_dict(None, start, num)
        query = []
        if terms:
            query.extend(terms)
        if excl_terms:
            query.extend(('-' + term for term in excl_terms))

        users_args_mapping = (
            ('users', 'from'),
            ('excl_users', '-from'),
            ('friends_of', 'friends'),
            ('excl_friends_of', '-friends'),
            ('comments_by', 'comment'),
            ('excl_comments_by', '-comment'),
            ('liked_by', 'like'),
            ('excl_liked_by', '-like')
        )
        rooms_args_mapping = (
            ('rooms', 'room'),
            ('excl_rooms', '-room'),
        )
        services_args_mapping = (
            ('services', 'service'),
            ('excl_services', '-service'),
        )
        args_mapping = (
            ('in_title', 'intitle'),
            ('excl_in_title', '-intitle'),
            ('in_comment', 'incomment'),
            ('excl_in_comment', '-incomment'),
        )
        min_mapping = (
            ('min_comments', 'comments'),
            ('min_likes', 'likes')
        )
        max_mapping = (
            ('max_comments', '-comments'),
            ('max_likes', '-likes')
        )

        lcls = locals()

        for arg, query_op in users_args_mapping:
            value = lcls[arg]
            if value:
                nicknames = (self._get_user_nickname(user) for user in
                        value)
                query_piece = '%s:%s' % (
                    query_op,
                    ','.join(nicknames)
                )
                query.append(query_piece)

        for arg, query_op in rooms_args_mapping:
            value = lcls[arg]
            if value:
                nicknames = (self._get_room_nickname(room) for room in
                        value)
                query_piece = '%s:%s' % (
                    query_op,
                    ','.join(nicknames)
                )
                query.append(query_piece)

        for arg, query_op in services_args_mapping:
            value = lcls[arg]
            if value:
                nicknames = (self._get_service_id(service) for
                        service in value)
                query_piece = '%s:%s' % (
                    query_op,
                    ','.join(nicknames)
                )
                query.append(query_piece)

        for arg, query_op in args_mapping:
            value = lcls[arg]
            if value:
                query_piece = '%s:%s' % (
                    query_op,
                    ','.join(value)
                )
                query.append(query_piece)

        for arg, query_op in min_mapping:
            value = lcls[arg]
            if value is not None:
                if not isinstance(value, int) or value <= 0:
                    raise ValueError("%s must be a positive "
                        "integer." % arg)
                query_piece = '%s:%d' % (query_op, value)
                query.append(query_piece)

        for arg, query_op in max_mapping:
            value = lcls[arg]
            if value is not None:
                if not isinstance(value, int) or value <= 0:
                    raise ValueError("%s must be a positive "
                        "integer." % arg)
                # We need to increment by one so that the cutoff for
                # getting a maximum of, say, 2 likes, is given
                # appropriately as -likes:3
                query_piece = '%s:%d' % (query_op, value+1)
                query.append(query_piece)

        url_args['q'] = '+'.join(query)
        response = self._fetch('/feed/search', url_args=url_args)
        entries = self._parse_entries_iter(response['entries'])
        return entries


    def search(
            self,
            terms=[],
            excl_terms=[],
            users=[],
            excl_users=[],
            rooms=[],
            excl_rooms=[],
            services=[],
            excl_services=[],
            friends_of=[],
            excl_friends_of=[],
            in_title=[],
            excl_in_title=[],
            in_comment=[],
            excl_in_comment=[],
            comments_by=[],
            excl_comments_by=[],
            liked_by=[],
            excl_liked_by=[],
            min_comments=None,
            max_comments=None,
            min_likes=None,
            max_likes=None,
            start=None,
            num=None
            ):
        """
        Searches over entries in FriendFeed and yields an `Entry` instance
        for each entry matching the search specifications.

        If an authentication name and key is provided, the default scope
        is over all of the entries in the authenticated user's Friends
        Feed. If authentication credentials were not provided, the
        default scope is over all public entries.

        Many of the search parameters for refining the search space have
        complementary parameters for excluding entries; for example,
        `users` which restricts entries returned to only those from this
        list of users, has a complementary parameter `excl_users`, which
        will exclude all entries from this list of users.

        NOTE: Returns an iterator.

        :Parameters:
        - `terms`: a list of terms; restrict entries to those containing
          any of these terms in entry titles or comments
        - `users`: a list of users (user names or `User` instances);
          restrict entries to those from these users' feeds
        - `excl_users`: exclude entries by these users
        - `rooms`: a list of rooms (room names or `Room` instances);
          restrict entries to those from these rooms' feeds
        - `excl_rooms`: exclude entries in these rooms
        - `services`: a list of services (service names or `Service`
          instances); restrict entries to those from these services
        - `excl_services`: exclude entries from these services
        - `friends_of`: a list of users; include entries from friends of
          these users
        - `excl_friends_of`: exclude entries from friends of these users
        - `in_title`: a list of terms to search for only in entry titles
        - `excl_in_title`: exclude entries with these terms in titles
        - `in_comment`: a list of terms to search for only in comments
        - `excl_in_comment`: exclude entries with these terms in
          comments
        - `comments_by`: a list of users, to include entries commented
          on by
        - `excl_comments_by`: exclude entries with comments by these
          users
        - `liked_by`: a list of users; include entries "liked" by these
          users
        - `excl_liked_by`: exclude entries liked by these users
        - `min_comments`: return entries with specified minimum number
          of comments [should be a positive integer]
        - `max_comments`: return entries with specified maximum number
          of comments [should be a positive integer]
        - `min_likes`: return entries with specified minimum number of
          "likes" [should be a positive integer]
        - `max_likes`: return entries with specified maximum number of
          "likes" [should be a positive integer]
        - `start`: retrieve entries starting from this index [should be
          a non-negative integer]
        - `num`: retrieve this many entries [should be a positive
          integer]

        """

        return list(self.search_iter(
            terms,
            excl_terms,
            users,
            excl_users,
            rooms,
            excl_rooms,
            services,
            excl_services,
            friends_of,
            excl_friends_of,
            in_title,
            excl_in_title,
            in_comment,
            excl_in_comment,
            comments_by,
            excl_comments_by,
            liked_by,
            excl_liked_by,
            min_comments,
            max_comments,
            min_likes,
            max_likes,
            start,
            num
        ))


    def get_user_profile(self, nickname):
        """
        Returns a `User` instance for a user of the given nickname.

        :Parameters:
        - `nickname`: nickname of the user

        """

        profile = self._fetch('/user/%s/profile' % nickname)
        return self._parse_user(profile)


    def update_user_profile(self, user):
        """
        Updates a `User` instance by retrieving the user's full profile.

        This method is handy if you have only a partial user profile, as
        is returned by methods fetching entries or room profiles.

        :Parameters:
        - `user`: a `User` instance

        """

        if not isinstance(user, User):
            raise ValueError("user must be a User instance")
        profile = self._fetch('/user/%s/profile' % user.nickname)
        self._update_user_from_profile(user, profile)


    def get_multi_user_profiles(self, nicknames):
        """
        Returns a list of `User` instances for each nickname.

        :Parameters:
        - `nicknames`: a list of nicknames of the users

        """

        url_args = {'nickname': ','.join(nicknames)}
        response = self._fetch('/profiles', url_args=url_args)
        return self._parse_users(response['profiles'])


    def update_multi_user_profiles(self, users):
        """
        Updates `User` instances with the users' full profiles.

        :Parameters:
        - `users`: a list of `User` instances

        """

        users_dict = {}
        for user in users:
            users_dict[user.nickname] = user
        url_args = {'nickname': ','.join(users_dict.keys())}
        response = self._fetch('/profiles', url_args=url_args)
        for profile in response['profiles']:
            user = users_dict[profile['nickname']]
            self._update_user_from_profile(user, profile)


    def get_room_profile(self, room):
        """
        Returns a `Room` instance for a room of the given nickname.

        :Parameters:
        - `nickname`: nickname of the room

        """

        nickname = self._get_room_nickname(room)
        profile = self._fetch('/room/%s/profile' % nickname)
        return self._parse_room(profile)


    def update_room_profile(self, room):
        """
        Updates a `Room` instance by retrieving the room's full profile.

        This method is handy if you have only a partial room profile, as
        is returned by methods fetching entries or user profiles.

        :Parameters:
        - `room`: a `Room` instance

        """

        if not isinstance(room, Room):
            raise ValueError("room must be a Room instance")
        profile = self._fetch('/room/%s/profile' % room.nickname)
        attrs = self._make_attrs_dict(
                profile,
                self._room_attr_map,
                self._room_method_map
                )
        for attr, value in attrs.items():
            setattr(room, attr, value)


    def get_list_profile(self, subscription_list):
        """
        Given a list nickname or a `SubscriptionList` instance, returns
        a full profile as a `SubscriptionList` instance.

        NOTE: AUTHENTICATION IS REQUIRED.

        :Parameters:
        - `subscription_list`: a `SubscriptionList` instance or nickname
          of a list

        """

        nickname = self._get_list_name(subscription_list)
        profile = self._fetch('/list/%s/profile' % nickname)
        return self._parse_sub_list(profile)


    def publish(
            self,
            title,
            link=None,
            comment=None,
            image_urls=[],
            images_and_links=[],
            image_files=[],
            audio_urls=[],
            audio=[],
            room=None
            ):
        """
        Workhorse function to publish a an entry to the authenticated
        user's feed.

        Returns an `Entry` instance.

        NOTE: AUTHENTICATION IS REQUIRED.

        NOTE: This method is for advanced use; the other available
        `publish` methods provide simpler usage.

        Some distinction between the image options follows: `image_urls`
        is a list of URLs that will be downloaded and included as
        thumbnails beneath the link. The thumbnails will all link to the
        destination link. If you would prefer that the images link
        somewhere else, you can specify `images_and_links` instead.
        `images_and_links` should be a list of dicts of the form
        `{"url": ..., "link": ...}`. The thumbnail located at the given
        URL will link to the specified link. Lastly, if you need to
        upload any images to FriendFeed, you should use `image_files`,
        which is a list or iterable of file handles to images.

        Audio works similarly to images. `audio_urls` is a list of URLs
        to audio files (e.g., MP3 files) that will show up as a play
        button beneath the link. If you would like to define the titles
        that appear along with the audio media, you can supply `audio`
        instead, which should be a list of dicts of the form `{"url":
        ..., "title": ...}`. The given title will appear when the audio
        file is played.

        Returns an `Entry` instance representing the published entry.

        :Parameters:
        - `title`: the title text of the entry
        - `link`: a URL to link to
        - `comment`: text for a comment on the entry
        - `image_urls`: a list of URLs to images to use as thumbnails
            for the entry
        - `images_and_links`: a list of dictionaries of the form
            `{'url': ..., 'link': ...}`
        - `image_files`: a list of dictionaries of the form
            `{'file': `<file-like instance>`, 'link': ...}` where `link`
            is optional
        - `audio_urls`: a list of URLs to audio files to show with a
            media play button underneath
        - `audio`: a list of dictionaries of the form {'url': ...,
            'title': ...}; the given title will be displayed when the
            audio file is played
        - `room`: posts the entry to this room, if specified [should be
            a `Room` instance or a room nickname]

        Example:

            session = friendfeed.FriendFeedAPI(nickname, remote_key)
            entry = session.publish(
                title="Testing the FriendFeed API",
                link="http://friendfeed.com/",
                image_urls=[
                    "http://friendfeed.com/static/images/jim-superman.jpg",
                    "http://friendfeed.com/static/images/logo.png",
                ],
            )
            print "Posted images at http://friendfeed.com/e/%s" % entry.id

        """

        post_args = {'title': title}
        if link:
            post_args['link'] = link
        if comment:
            post_args['comment'] = comment
        if self.via:
            post_args['via'] = self.via
        for image_url in image_urls:
            images_and_links.append({'url': image_url})
        for i, image in enumerate(images_and_links):
            post_args['image%d_url' % i] = image['url']
            if 'link' in image:
                post_args['image%d_link' % i] = image['link']
        # The line below should be unneccesary. --CDL
        #audio = audio[:]
        for audio_url in audio_urls:
            audio.append({'url': audio_url})
        for i, clip in enumerate(audio):
            post_args['audio%d_url' % i] = clip['url']
            if 'title' in clip:
                post_args['audio%d_title' % i] = clip['title']
        if room:
            post_args['room'] = self._get_room_nickname(room)
        response = self._fetch(
                '/share',
                post_args=post_args,
                files=image_files
                )
        return self._parse_entry(response['entries'][0])


    def publish_message(
            self,
            message,
            room=None
            ):
        """
        Publish a message to the authenticated user's feed.

        Returns an `Entry` instance representing the posted entry.

        NOTE: AUTHENTICATION IS REQUIRED.

        :Parameters:
        - `message`: a text message
        - `room`: posts the entry to this room, if specified [should be
            a `Room` instance or a room nickname]

        """

        return self.publish(title=message, room=room)


    def publish_link(
            self,
            title,
            link,
            room=None
            ):
        """
        Publish a link to the authenticated user's feed.

        Returns an `Entry` instance representing the posted entry.

        NOTE: AUTHENTICATION IS REQUIRED.

        :Parameters:
        - `title`: the title text of the entry
        - `link`: a URL to link to
        - `room`: posts the entry to this room, if specified [should be
            a `Room` instance or a room nickname]

        """

        return self.publish(title=title, link=link, room=room)


    def publish_image(
            self,
            title,
            image,
            link=None,
            room=None
            ):
        """
        Publish an image to the authenticated user's feed.

        Returns an `Entry` instance representing the posted entry.

        NOTE: AUTHENTICATION IS REQUIRED.

        :Parameters:
        - `title`: the title text of the entry
        - `image`: an image file or a URL to an image
        - `link`: a URL to link to
        - `room`: posts the entry to this room, if specified [should be
            a `Room` instance or a room nickname]

        """

        # check to see if we were passed a URL
        if isinstance(image, (str, unicode)):
            return self.publish(
                    title=title,
                    link=link,
                    image_urls=[image],
                    room=room
            )
        # if not, check to see if it was a file (a `read()` method
        # should be sufficient)
        elif hasattr(image, 'read'):
            return self.publish(
                    title=title,
                    link=link,
                    image_files=[{'file': image}],
                    room=room
            )
        else:
            raise ValueError("image should be a file handle or URL")


    def delete_entry(self, entry):
        """
        Deletes an entry.

        Returns `True` if successful; otherwise returns `False`.

        NOTE: AUTHENTICATION IS REQUIRED.

        :Parameters:
        - `entry`: an `Entry` instance or the ID of the entry to delete

        """

        entry_id = self._get_entry_id(entry)
        post_args = {'entry': entry_id}
        response = self._fetch('/entry/delete', post_args=post_args)
        return response['success']


    def undelete_entry(self, entry):
        """
        Restores a deleted entry.

        Returns `True` if successful; otherwise returns `False`.

        NOTE: AUTHENTICATION IS REQUIRED.

        :Parameters:
        - `entry`: an `Entry` instance or the ID of the entry to restore

        """

        entry_id = self._get_entry_id(entry)
        post_args = {'entry': entry_id, 'undelete': 1}
        response = self._fetch('/entry/delete', post_args=post_args)
        return response['success']


    def hide_entry(self, entry):
        """
        Hides an entry.

        Returns `True` if successful; otherwise returns `False`.

        NOTE: AUTHENTICATION IS REQUIRED.

        :Parameters:
        - `entry`: an `Entry` instance or the ID of the entry to restore

        """

        entry_id = self._get_entry_id(entry)
        post_args = {'entry': entry_id}
        response = self._fetch('/entry/hide', post_args=post_args)
        return response['success']


    def unhide_entry(self, entry):
        """
        Unhides an entry.

        Returns `True` if successful; otherwise returns `False`.

        NOTE: AUTHENTICATION IS REQUIRED.

        :Parameters:
        - `entry`: an `Entry` instance or the ID of the entry to restore

        """

        entry_id = self._get_entry_id(entry)
        post_args = {'entry': entry_id, 'unhide': 1}
        response = self._fetch('/entry/hide', post_args=post_args)
        return response['success']


    def add_comment(self, entry, body):
        """
        Adds a comment to the entry of the specified entry ID.

        Returns a `Comment` instance representing the posted comment.

        :Parameters:
        - `entry`: an `Entry` instance or the ID of the entry on which
            to comment
        - `body`: the text of comment

        """

        return self.edit_comment(entry, body)


    def edit_comment(self, entry, body, comment=None):
        """
        Updates the comment of a given comment ID with new text.

        Returns a `Comment` instance representing the updated comment.

        :Parameters:
        - `entry`: an `Entry` instance or the ID of the entry to which
            the comment belongs
        - `comment`: the comment instance or ID of the comment to edit
        - `body`: the text of comment

        """

        entry_id = self._get_entry_id(entry)
        if comment:
            comment_id = self._get_comment_id(comment)
            post_args = {
                    'entry': entry_id,
                    'comment': comment_id,
                    'body': body
                    }
        else:
            post_args = {
                'entry': entry_id,
                'body': body
            }
        if self.via:
            post_args['via'] = self.via
        response = self._fetch('/comment', post_args=post_args)
        return self._parse_comment(response)


    def _comment_deletion(self, entry, comment, undelete=False):
        """
        Helper function for controlling delition/undelition of comments.

        Returns a `Comment` instance representing the deleted/undeleted
        comment.

        :Parameters:
        - `entry`: an `Entry` instance or the ID of the entry to which
            the comment belongs
        - `comment`: the `Comment` instance or ID of the comment to edit

        """

        entry_id = self._get_entry_id(entry)
        comment_id = self._get_comment_id(comment)
        post_args = {
                'entry': entry_id,
                'comment': comment_id,
                }
        if undelete:
            post_args['undelete'] = 1
        response = self._fetch("/comment/delete",
                post_args=post_args)
        return self._parse_comment(response)


    def delete_comment(self, entry, comment):
        """
        Deletes a comment of a given ID.

        Returns a `Comment` instance representing the deleted comment.

        :Parameters:
        - `entry`: an `Entry` instance or the ID of the entry to which
            the comment belongs
        - `comment`: the `Comment` instance or ID of the comment to edit

        """

        return self._comment_deletion(entry, comment)


    def undelete_comment(self, entry, comment):
        """
        Restores a deleted comment of a given ID.

        Returns a `Comment` instance representing the restored comment.

        :Parameters:
        - `entry`: an `Entry` instance or the ID of the entry to which
            the comment belongs
        - `comment`: the `Comment` instance or ID of the comment to edit

        """

        return self._comment_deletion(entry, comment, undelete=True)


    def add_like(self, entry):
        """
        "Likes" an entry.

        Returns `True` if successful; otherwise returns `False`.

        NOTE: AUTHENTICATION IS REQUIRED.

        :Parameters:
        - `entry`: an `Entry` instance or entry ID

        """

        entry_id = self._get_entry_id(entry)
        post_args = {'entry': entry_id}
        response = self._fetch('/like', post_args=post_args)
        return response['success']


    def delete_like(self, entry):
        """
        Removes a "like" for an entry

        Returns `True` if successful; otherwise returns `False`.

        NOTE: AUTHENTICATION IS REQUIRED.

        :Parameters:
        - `entry`: an `Entry` instance or entry ID

        """

        entry_id = self._get_entry_id(entry)
        post_args = {'entry': entry_id}
        response = self._fetch("/like/delete", post_args=post_args)
        return response['success']


    def _user_subscription(self, user, unsubscribe=False):
        """
        Helper method to handle user subscriptions.

        :Parameters:
        - `user`: a `User` instance, or the nickname of a user
        - `unsubscribe`: if `True`, unsubscribes from the `user`
            [default: `False`]

        """

        self._ensure_api_key_authenticated()
        post_args = {'apikey': self.api_key}
        nickname = self._get_user_nickname(user)
        if unsubscribe:
            url_args = {'unsubscribe': 1}
        else:
            url_args = {}
        response = self._fetch(
                '/user/%s/subscribe' % nickname,
                post_args=post_args,
                url_args=url_args)
        return response['status']


    def subscribe_user(self, user):
        """
        Subscribe's the authenticated account to a given user.

        Returns `True` if successful; otherwise returns `False`.

        NOTE: AUTHENTICATION IS REQUIRED.

        :Parameters:
        - `user`: a `User` instance, or the nickname of a user

        """

        return self._user_subscription(user)


    def unsubscribe_user(self, user):
        """
        Unsubscribe's the authenticated account from a given user.

        Returns `True` if successful; otherwise returns `False`.

        NOTE: AUTHENTICATION IS REQUIRED.

        :Parameters:
        - `user`: a `User` instance, or the nickname of a user

        """

        return self._user_subscription(user, True)


    def _room_subscription(self, room, unsubscribe=False):
        """
        Helper method to handle room subscriptions.

        :Parameters:
        - `room`: a `Room` instance, or the nickname of a room
        - `unsubscribe`: if `True`, unsubscribes from the `room`
            [default: `False`]

        """

        self._ensure_api_key_authenticated()
        post_args = {'apikey': self.api_key}
        nickname = self._get_room_nickname(room)
        if unsubscribe:
            url_args = {'unsubscribe': 1}
        else:
            url_args = {}
        response = self._fetch(
                '/room/%s/subscribe' % nickname,
                post_args=post_args,
                url_args=url_args)
        return response['status']


    def subscribe_room(self, room):
        """
        Subscribe's the authenticated account to a given room.

        Returns `True` if successful; otherwise returns `False`.

        NOTE: AUTHENTICATION IS REQUIRED.

        :Parameters:
        - `room`: a `Room` instance, or the nickname of a room

        """

        return self._room_subscription(room)


    def unsubscribe_room(self, room):
        """
        Unsubscribe's the authenticated account from a given room.

        Returns `True` if successful; otherwise returns `False`.

        NOTE: AUTHENTICATION IS REQUIRED.

        :Parameters:
        - `room`: a `Room` instance, or the nickname of a room

        """

        return self._room_subscription(room, True)


    def _fetch_image(
            self,
            resource,
            parameters=None
            ):
        """
        Fetch an image.

        :Parameters:
        - `resource`: the API resource (location) requested
        - `parameters`: a dictionary of parameters for the request
          (e.g., query parameters)

        """

        if parameters:
            uri = "http://friendfeed.com/%s?%s" % (resource,
                    urllib.unquote(self._urlencode(parameters))
            )
        else:
            uri = u'http://friendfeed.com/%s' % resource
        headers = self._make_auth_headers()
        request = urllib2.Request(uri, headers=headers)
        stream = self.urlopen(request)
        data = stream.read()
        return data


    def get_user_picture(self, user, pic_fileh, size='large'):
        """
        Get a user's profile picture.

        :Parameters:
        - `user`: a `User` instance, or the nickname of a user
        - `pic_fileh`: a file handle or file-like object to write to
        - `size`: either 'large' [default], 'medium', or 'small'

        """

        size = size.lower()
        if size not in ('large', 'medium', 'small'):
            raise ValueError("size must be 'large', 'medium', or "
                    "'small'")
        nickname = self._get_user_nickname(user)
        resource = '%s/picture' % nickname
        data = self._fetch_image(resource, {'size': size})
        pic_fileh.write(data)


    def get_room_picture(self, room, pic_fileh, size='large'):
        """
        Get a room's profile picture.

        :Parameters:
        - `room`: a `Room` instance, or the nickname of a room
        - `pic_fileh`: a file handle or file-like object to write to
        - `size`: either 'large' [default], 'medium', or 'small'

        """

        size = size.lower()
        if size not in ('large', 'medium', 'small'):
            raise ValueError("size must be 'large', 'medium', or "
                    "'small'")
        nickname = self._get_room_nickname(room)
        resource = '%s/picture' % nickname
        data = self._fetch_image(resource, {'size': size})
        pic_fileh.write(data)

