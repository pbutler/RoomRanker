# -*- coding: UTF-8 -*-

"""
Tests for the FriendFeed API.

"""

__author__ = 'Chris Lasher'
__email__ = 'chris DOT lasher <AT> gmail DOT com'


import copy
import datetime
import os
import sys
import unittest

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
parpath = os.path.join(MODULE_DIR, os.pardir)
sys.path.insert(0, os.path.abspath(parpath))
sys.path.insert(1, MODULE_DIR)
import friendfeed
import entry_example

ENTRY_JSON_PATH = os.path.abspath(
    os.path.join(
        MODULE_DIR,
        'entry_example.json'
    )
)

class UserTests(unittest.TestCase):
    """Tests for User."""

    def test_minimal_init(self):
        """minimal __init__()"""

        user = friendfeed.User('gotgenes')
        expected = friendfeed.User(
                nickname='gotgenes',
                id=None,
                profile_url=None,
                private=False,
                services=[],
                subscriptions=[],
                rooms=[],
                lists=[]
                )

        self.assertEqual(user, expected)


class ServiceTests(unittest.TestCase):
    """Tests for Service."""

    def test_minimal_init(self):
        """minimal __init__()"""

        service = friendfeed.Service(
                'twitter',
                'Twitter',
                )
        expected = friendfeed.Service(
                id='twitter',
                name='Twitter',
                url=None,
                icon_url=None,
                profile_url=None,
                username=None,
                entry_type=None,
                )
        self.assertEqual(service, expected)


class RoomTests(unittest.TestCase):
    """Tests for Room."""

    def test_minimal_init(self):
        """minimal __init__()"""

        room = friendfeed.Room('the-life-scientists')
        expected = friendfeed.Room(
                nickname='the-life-scientists',
                id=None,
                name=None,
                url=None,
                private=False,
                description=None,
                members=[],
                administrators=[]
                )
        self.assertEqual(room, expected)


class SubscriptionListTests(unittest.TestCase):
    """Tests for SubscriptionList."""

    def test_minimal_init(self):
        """minimal __init__()"""

        sl = friendfeed.SubscriptionList('personal')
        expected = friendfeed.SubscriptionList(
                nickname='personal',
                id=None,
                name=None,
                url=None,
                users=[],
                rooms=[]
                )
        self.assertEqual(sl, expected)


class CommentTests(unittest.TestCase):
    """Tests for Comment."""

    def test_minimal_init(self):
        """minimal __init__()"""

        comment = friendfeed.Comment(
                '411b7034-da96-496d-bec3-e64e2527a997')
        expected = friendfeed.Comment(
                id='411b7034-da96-496d-bec3-e64e2527a997',
                date=None,
                user=None,
                body=None,
                via={}
                )
        self.assertEqual(comment, expected)


class MediaTests(unittest.TestCase):
    """Tests for Media."""

    def test_minimal_init(self):
        """minimal __init__()"""

        media = friendfeed.Media()
        expected = friendfeed.Media(
                title=None,
                player=None,
                link=None,
                thumbnails=[],
                content=[],
                enclosures=[]
                )
        self.assertEqual(media, expected)


class EntryTests(unittest.TestCase):
    """Tests for Entry."""

    def test_minimal_init(self):
        """minimal __init__()"""

        entry = friendfeed.Entry('6bu83hda-3bc1-55fc-150b-c52c41cd158a')
        expected = friendfeed.Entry(
                id='6bu83hda-3bc1-55fc-150b-c52c41cd158a',
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
                )
        self.assertEqual(entry, expected)


class FriendFeedAPIParseTests(unittest.TestCase):
    """Tests for _parse_*() methods of FriendFeedAPI."""

    def setUp(self):
        self.api = friendfeed.FriendFeedAPI()
        self.user_profile_cases = [
            [
                {
                    'id': 'ae0a07fe-2768-11dd-a306-003048343a40',
                    'nickname': 'gotgenes',
                    'name': 'Chris Lasher',
                    'profileUrl': 'http://friendfeed.com/gotgenes'
                }
            ],
            [
                {
                    'id': '0d320c9d-73bf-40ec-90d8-323a2f70b955',
                    'nickname': 'mndoci',
                    'name': 'Deepak',
                    'profileUrl': 'http://friendfeed.com/mndoci'
                }
            ]
        ]
        for case in self.user_profile_cases:
            profile = case[0]
            expected = friendfeed.User(
                    profile['nickname'],
                    id=profile['id'],
                    name=profile['name'],
                    profile_url=profile['profileUrl']
                    )
            case.append(expected)

        self.imaginary_friend_cases = [
            [
                {
                    'id': 'rah38u0am-848k-j9kv-u02b-o0uhmebuah92',
                    'nickname': None,
                    'name': 'Fakie McFakester',
                    'profileUrl': 'http://friendfeed.com/rah38u0am-848k-j9kv-u02b-o0uhmebuah92',
                }
            ]
        ]
        for case in self.imaginary_friend_cases:
            friend = case[0]
            expected = friendfeed.ImaginaryFriend(
                    id=friend['id'],
                    name=friend['name'],
                    profile_url=friend['profileUrl']
                    )
            case.append(expected)

        self.list_cases = [
            [
                {
                    'nickname': 'professional',
                    'id': 'ahur83eu-5uth-5we5-91ut-9th002bu833b',
                    'name': 'Professional',
                    'url': 'http://friendfeed.com/list/professional'
                }
            ],
            [
                {
                    'nickname': 'personal',
                    'id': 'et98y0eg-90ow-9023-eu9u-be93b13beeq9',
                    'name': 'Personal',
                    'url': 'http://friendfeed.com/list/personal'
                }
            ]
        ]
        for case in self.list_cases:
            sub_list = case[0]
            expected = friendfeed.SubscriptionList(
                    nickname=sub_list['nickname'],
                    id=sub_list['id'],
                    name=sub_list['name'],
                    url=sub_list['url']
                    )
            case.append(expected)

        self.service_cases = [
            [
                {
                    'id': 'twitter',
                    'name': 'Twitter',
                    'url': 'http://twitter.com/',
                    'iconUrl': 'http://friendfeed.com/static/images/icons/twitter.png?v=df0a0affa8100c494df42159627a38b0',
                    'profileUrl': 'http://twitter.com/gotgenes',
                    'username': 'gotgenes'
                }
            ],
            [
                {
                    'id': 'flickr',
                    'name': 'Flickr',
                    'url': 'http://flickr.com/',
                    'iconUrl': 'http://friendfeed.com/static/images/icons/flickr.png?v=77eeaefbcb3644cec0162a0938ec28e2',
                    'profileUrl': 'http://www.flickr.com/photos/30589354%40N03/',
                    'username': 'gotgenes'
                }
            ]
        ]
        for case in self.service_cases:
            service = case[0]
            expected = friendfeed.Service(
                    id=service['id'],
                    name=service['name'],
                    url=service['url'],
                    icon_url=service['iconUrl'],
                    profile_url=service['profileUrl'],
                    username=service['username']
                    )
            case.append(expected)

        self.room_cases = [
            [
                {
                    'description': 'A room for all the life science types.',
                    'id': 'fedb6e36-e4a9-11dc-b594-003048343a40',
                    'name': 'The Life Scientists',
                    'nickname': 'the-life-scientists',
                    'url': 'http://friendfeed.com/rooms/the-life-scientists'
                }
            ],
            [
                {
                    'description': 'The programming language',
                    'id': '37bd843f-6d34-45db-9ff2-fc109370d6bd',
                    'name': 'Python',
                    'nickname': 'python',
                    'url': 'http://friendfeed.com/rooms/python'
                }
            ]
        ]
        for case in self.room_cases:
            room = case[0]
            expected = friendfeed.Room(
                    description=room['description'],
                    id=room['id'],
                    name=room['name'],
                    nickname=room['nickname'],
                    url=room['url']
                    )
            case.append(expected)

        self.like_cases = [
            [
                {
                    'date': '2008-12-18T20:36:49Z',
                    'user': self.user_profile_cases[0][0]
                },
                {
                    'date': datetime.datetime(2008, 12, 18, 20, 36, 49),
                    'user': self.user_profile_cases[0][1]
                }
            ],
            [
                {
                    'date': '2008-12-19T20:00:00Z',
                    'user': self.user_profile_cases[1][0]
                },
                {
                    'date': datetime.datetime(2008, 12, 19, 20, 00, 00),
                    'user': self.user_profile_cases[1][1]
                }
            ]
        ]

        self.comment_cases = [
            [
                {
                    'date': '2008-12-18T20:36:49Z',
                    'id': '411b7034-da96-496d-bec3-e64e2527a997',
                    'user': self.user_profile_cases[0][0],
                    'body': 'Awesome!'
                },
                friendfeed.Comment(
                    id='411b7034-da96-496d-bec3-e64e2527a997',
                    date=datetime.datetime(2008, 12, 18, 20, 36, 49),
                    user=self.user_profile_cases[0][1],
                    body='Awesome!'
                )
            ],
            [
                {
                    'date': '2008-12-28T20:36:49Z',
                    'id': '212b7034-da96-496d-bec3-e64e2527a997',
                    'user': self.user_profile_cases[1][0],
                    'body': 'So awesome!'
                },
                friendfeed.Comment(
                    id='212b7034-da96-496d-bec3-e64e2527a997',
                    date=datetime.datetime(2008, 12, 28, 20, 36, 49),
                    user=self.user_profile_cases[1][1],
                    body='So awesome!'
                )
            ]
        ]

        self.media_cases = [
            [
                {
                    'enclosures': None,
                    'title': 'Reef sharks',
                    'content': [
                        {
                            'url': 'http://www.youtube.com/v/RoNknVnwXTk&f=gdata_user_favorites&c=ytapi-FriendFeed-FriendFeed-8e762i7n-0&d=C3jWYyDXZCPRCne8EtVoKmD9LlbsOl3qUImVMV6ramM',
                            'type': 'application/x-shockwave-flash'
                        },
                        {
                            'url': 'rtsp://rtsp2.youtube.com/CnoLENy73wIacQk5XfBZnWSDRhMYDSANFEImeXRhcGktRnJpZW5kRmVlZC1GcmllbmRGZWVkLThlNzYyaTduLTBIBlIUZ2RhdGFfdXNlcl9mYXZvcml0ZXNyIAt41mMg12Qj0Qp3vBLVaCpg_S5W7Dpd6lCJlTFeq2pjDA==/0/0/0/video.3gp',
                            'type': 'video/3gpp'
                        },
                        {
                            'url': 'rtsp://rtsp2.youtube.com/CnoLENy73wIacQk5XfBZnWSDRhMYESARFEImeXRhcGktRnJpZW5kRmVlZC1GcmllbmRGZWVkLThlNzYyaTduLTBIBlIUZ2RhdGFfdXNlcl9mYXZvcml0ZXNyIAt41mMg12Qj0Qp3vBLVaCpg_S5W7Dpd6lCJlTFeq2pjDA==/0/0/0/video.3gp',
                            'type': 'video/3gpp'
                        }
                    ],
                    'player': 'http://www.youtube.com/watch?v=RoNknVnwXTk',
                    'link': 'http://www.youtube.com/watch?v=RoNknVnwXTk',
                    'thumbnails': [
                        {
                            'url': 'http://i.ytimg.com/vi/RoNknVnwXTk/2.jpg',
                            'width': 130,
                            'height': 97
                        },
                        {
                            'url': 'http://i.ytimg.com/vi/RoNknVnwXTk/1.jpg',
                            'width': 130,
                            'height': 97
                        },
                        {
                            'url': 'http://i.ytimg.com/vi/RoNknVnwXTk/3.jpg',
                            'width': 130,
                            'height': 97
                        },
                        {
                            'url': 'http://i.ytimg.com/vi/RoNknVnwXTk/hqdefault.jpg',
                            'width': 480,
                            'height': 360
                        }
                    ]
                },
                friendfeed.Media(
                    title='Reef sharks',
                    player='http://www.youtube.com/watch?v=RoNknVnwXTk',
                    link='http://www.youtube.com/watch?v=RoNknVnwXTk',
                    thumbnails=[
                        {
                            'url': 'http://i.ytimg.com/vi/RoNknVnwXTk/2.jpg',
                            'width': 130,
                            'height': 97
                        },
                        {
                            'url': 'http://i.ytimg.com/vi/RoNknVnwXTk/1.jpg',
                            'width': 130,
                            'height': 97
                        },
                        {
                            'url': 'http://i.ytimg.com/vi/RoNknVnwXTk/3.jpg',
                            'width': 130,
                            'height': 97
                        },
                        {
                            'url': 'http://i.ytimg.com/vi/RoNknVnwXTk/hqdefault.jpg',
                            'width': 480,
                            'height': 360
                        }
                    ],
                    content=[
                        {
                            'url': 'http://www.youtube.com/v/RoNknVnwXTk&f=gdata_user_favorites&c=ytapi-FriendFeed-FriendFeed-8e762i7n-0&d=C3jWYyDXZCPRCne8EtVoKmD9LlbsOl3qUImVMV6ramM',
                            'type': 'application/x-shockwave-flash'
                        },
                        {
                            'url': 'rtsp://rtsp2.youtube.com/CnoLENy73wIacQk5XfBZnWSDRhMYDSANFEImeXRhcGktRnJpZW5kRmVlZC1GcmllbmRGZWVkLThlNzYyaTduLTBIBlIUZ2RhdGFfdXNlcl9mYXZvcml0ZXNyIAt41mMg12Qj0Qp3vBLVaCpg_S5W7Dpd6lCJlTFeq2pjDA==/0/0/0/video.3gp',
                            'type': 'video/3gpp'
                        },
                        {
                            'url': 'rtsp://rtsp2.youtube.com/CnoLENy73wIacQk5XfBZnWSDRhMYESARFEImeXRhcGktRnJpZW5kRmVlZC1GcmllbmRGZWVkLThlNzYyaTduLTBIBlIUZ2RhdGFfdXNlcl9mYXZvcml0ZXNyIAt41mMg12Qj0Qp3vBLVaCpg_S5W7Dpd6lCJlTFeq2pjDA==/0/0/0/video.3gp',
                            'type': 'video/3gpp'
                        }
                    ],
                    enclosures=[]
                )
            ],
            [
                {
                    'enclosures': None,
                    'title': 'Android dev phone 1',
                    'content': [
                        {
                            'url': 'http://farm4.static.flickr.com/3285/3145097863_cb63fe83d7_o.jpg',
                            'width': 2048,
                            'type': 'image/jpeg',
                            'height':1536
                        }
                    ],
                    'player': None,
                    'link': 'http://www.flickr.com/photos/pansapiens/3145097863/',
                    'thumbnails': [
                        {
                            'url': 'http://farm4.static.flickr.com/3285/3145097863_c9f868991e_s.jpg',
                            'width': 75,
                            'height': 75
                        }
                    ]
                },
                friendfeed.Media(
                    title='Android dev phone 1',
                    link='http://www.flickr.com/photos/pansapiens/3145097863/',
                    player=None,
                    content=[
                        {
                            'url': 'http://farm4.static.flickr.com/3285/3145097863_cb63fe83d7_o.jpg',
                            'width': 2048,
                            'type': 'image/jpeg',
                            'height':1536
                        }
                    ],
                    thumbnails=[
                        {
                            'url': 'http://farm4.static.flickr.com/3285/3145097863_c9f868991e_s.jpg',
                            'width': 75,
                            'height': 75
                        }
                    ],
                    enclosures=[]
                )
            ]
        ]

        self.entry_cases = [
            [
                {
                    'id': '6bu83hda-3bc1-55fc-150b-c52c41cd158a',
                    'title': 'Over 9000!',
                    'link': 'http://itsover9000.com/',
                    'published': '2008-12-28T23:57:09Z',
                    'updated': '2008-12-28T23:57:09Z',
                    'hidden': False,
                    'anonymous': False,
                    'user': self.user_profile_cases[0][0],
                    'service': self.service_cases[0][0],
                    'comments': [self.comment_cases[0][0]],
                    'likes': [self.like_cases[0][0]],
                    'media': [self.media_cases[0][0]],
                    'via': {
                        'name': 'Alert Thingy',
                        'url': 'http://www.alertthingy.com/'
                    },
                    'room': self.room_cases[0][0]
                },
                friendfeed.Entry(
                    id='6bu83hda-3bc1-55fc-150b-c52c41cd158a',
                    title='Over 9000!',
                    link='http://itsover9000.com/',
                    published=datetime.datetime(2008, 12, 28, 23, 57, 9),
                    updated=datetime.datetime(2008, 12, 28, 23, 57, 9),
                    hidden=False,
                    anonymous=False,
                    user=self.user_profile_cases[0][1],
                    service=self.service_cases[0][1],
                    comments=[self.comment_cases[0][1]],
                    likes=[self.like_cases[0][1]],
                    media=[self.media_cases[0][1]],
                    via={
                        'name': 'Alert Thingy',
                        'url': 'http://www.alertthingy.com/'
                    },
                    room=self.room_cases[0][1]
                )
            ],
            [
                {
                    'id': '09chnrip-e091-c9ue-1cg3-rhaboeuh0et9b8c',
                    'title': 'Testing',
                    'link': 'http://friendfeed.com/e/09chnrip-e091-c9ue-1cg3-rhaboeuh0et9b8c',
                    'published': '2008-10-11T11:17:31Z',
                    'updated': '2008-10-11T11:19:08Z',
                    'hidden': True,
                    'anonymous': False,
                    'user': self.user_profile_cases[1][0],
                    'service': self.service_cases[1][0],
                    'comments': [],
                    'likes': [],
                    'media': [],
                },
                friendfeed.Entry(
                    id='09chnrip-e091-c9ue-1cg3-rhaboeuh0et9b8c',
                    title='Testing',
                    link='http://friendfeed.com/e/09chnrip-e091-c9ue-1cg3-rhaboeuh0et9b8c',
                    published=datetime.datetime(2008, 10, 11, 11, 17, 31),
                    updated=datetime.datetime(2008, 10, 11, 11, 19, 8),
                    hidden=True,
                    anonymous=False,
                    user=self.user_profile_cases[1][1],
                    service=self.service_cases[1][1],
                    comments=[],
                    likes=[],
                    media=[],
                    via={},
                    room=None
                )
            ],
        ]

    def separate_cases_and_expected(self, struct):
        """
        Separates a structure that has tuples of (case, expected) into
        two lists, one of cases, the other of expected values.

        """

        cases = []
        expecteds = []
        for case, expected in struct:
            cases.append(case)
            expecteds.append(expected)
        return cases, expecteds


    def test_make_attrs_dict(self):
        """_make_attrs_dict()"""

        case = {
                'a': 1,
                'b': [2, 3]
        }
        attrs_map = {'a': 'other_a'}
        method_map = {'b': ('other_b', lambda x: sum(x))}
        expected = {
                'other_a': 1,
                'other_b': 5
        }
        self.assertEqual(
                self.api._make_attrs_dict(case, attrs_map, method_map),
                expected
        )


    def test_make_attrs_dict_raises_error(self):
        """_make_attrs_dict() raises KeyError"""

        case = {'a': 1}
        attrs_map = {}
        func_map = {}
        self.assertRaises(
                KeyError,
                self.api._make_attrs_dict,
                case,
                attrs_map,
                func_map
        )


    def test_parse_date(self):
        """_parse_date()"""

        date = self.api._parse_date('2008-12-18T20:36:49Z')
        self.assertEqual(
            date,
            datetime.datetime(2008, 12, 18, 20, 36, 49)
        )


    def test_parse_user_simple(self):
        """_parse_user() simple"""

        for case, expected in self.user_profile_cases:
            self.assertEqual(
                    self.api._parse_user(case),
                    expected
            )


    def test_parse_users_iter_simple(self):
        """_parse_users_iter() simple"""


        cases, expected = self.separate_cases_and_expected(
                self.user_profile_cases)
        self.assertEqual(
                list(self.api._parse_users_iter(cases)),
                expected
        )


    def test_parse_users_simple(self):
        """_parse_users() simple"""


        cases, expected = self.separate_cases_and_expected(
                self.user_profile_cases)
        self.assertEqual(
                self.api._parse_users(cases),
                expected
        )


    def test_parse_sub_list_simple(self):
        """_parse_sub_list() simple"""

        for case, expected in self.list_cases:
            self.assertEqual(
                    self.api._parse_sub_list(case),
                    expected
            )


    def test_parse_sub_lists_iter_simple(self):
        """_parse_sub_lists_iter() simple"""

        cases, expected = self.separate_cases_and_expected(
                self.list_cases)
        self.assertEqual(
                list(self.api._parse_sub_lists_iter(cases)),
                expected
        )


    def test_parse_lists_simple(self):
        """_parse_sub_lists() simple"""

        cases, expected = self.separate_cases_and_expected(
                self.list_cases)
        self.assertEqual(
                self.api._parse_sub_lists(cases),
                expected
        )


    def test_parse_service(self):
        """_parse_service()"""

        for case, expected in self.service_cases:
            self.assertEqual(
                    self.api._parse_service(case),
                    expected
            )


    def test_parse_services_iter(self):
        """_parse_services_iter()"""

        cases, expected = self.separate_cases_and_expected(
                self.service_cases)
        self.assertEqual(
                list(self.api._parse_services_iter(cases)),
                expected
        )


    def test_parse_services(self):
        """_parse_services()"""

        cases, expected = self.separate_cases_and_expected(
                self.service_cases)
        self.assertEqual(
                self.api._parse_services(cases),
                expected
        )


    def test_parse_privacy(self):
        """_parse_privacy()"""

        cases = (('public', False), ('private', True), ('Public',
            False))
        for case, expected in cases:
            self.assertEqual(self.api._parse_privacy(case), expected)


    def test_parse_privacy_error(self):
        """_parse_privacy() raises ValueError"""

        self.assertRaises(
                ValueError,
                self.api._parse_privacy,
                'fake'
        )


    def test_parse_room_simple(self):
        """_parse_room() simple"""

        for case, expected in self.room_cases:
            self.assertEqual(
                    self.api._parse_room(case),
                    expected
            )


    def test_parse_rooms_iter_simple(self):
        """_parse_rooms_iter() simple"""

        cases, expected = self.separate_cases_and_expected(
                self.room_cases)
        self.assertEqual(
                list(self.api._parse_rooms_iter(cases)),
                expected
        )


    def test_parse_rooms_simple(self):
        """_parse_rooms() simple"""

        cases, expected = self.separate_cases_and_expected(
                self.room_cases)
        self.assertEqual(
                self.api._parse_rooms(cases),
                expected
        )


    def test_parse_user_full(self):
        """_parse_user() full"""

        case = self.user_profile_cases[0][0]
        sub_case, sub_expected = self.user_profile_cases[1]
        case['subscriptions'] = [sub_case]
        service_case, service_expected = self.service_cases[0]
        case['services'] = [service_case]
        room_case, room_expected = self.room_cases[0]
        case['rooms'] = [room_case]
        sub_list_case, sub_list_expected = self.list_cases[0]
        case['lists'] = [sub_list_case]
        case['status'] = 'public'
        expected = friendfeed.User(
                id=case['id'],
                name=case['name'],
                nickname=case['nickname'],
                private=False,
                profile_url=case['profileUrl'],
                rooms=[room_expected],
                lists=[sub_list_expected],
                services=[service_expected],
                subscriptions=[sub_expected]
                )

        result = self.api._parse_user(case)
        self.assertEqual(result, expected)


    def test_parse_room_full(self):
        """_parse_room() full"""

        case = self.room_cases[0][0]
        case['status'] = 'private'
        user_case, user_expected = self.user_profile_cases[0]
        case['administrators'] = [user_case]
        case['members'] = [user_case]
        expected = friendfeed.Room(
                id=case['id'],
                name=case['name'],
                nickname=case['nickname'],
                url=case['url'],
                private=True,
                description=case['description'],
                administrators=[user_expected],
                members=[user_expected]
                )

        result = self.api._parse_room(case)
        self.assertEqual(result, expected)


    def test_parse_sub_list_full(self):
        """_parse_sub_list() full"""

        case = self.list_cases[0][0]
        user_case, user_expected = self.user_profile_cases[0]
        case['users'] = [user_case]
        room_case, room_expected = self.room_cases[0]
        case['rooms'] = [room_case]
        expected = friendfeed.SubscriptionList(
                id=case['id'],
                name=case['name'],
                nickname=case['nickname'],
                url=case['url'],
                users=[user_expected],
                rooms=[room_expected]
                )

        result = self.api._parse_sub_list(case)
        self.assertEqual(result, expected)


    def test_parse_like(self):
        """_parse_like()"""

        for case, expected in self.like_cases:
            self.assertEqual(self.api._parse_like(case), expected)


    def test_parse_likes_iter(self):
        """_parse_likes_iter()"""

        cases, expected = self.separate_cases_and_expected(
                self.like_cases)
        self.assertEqual(
                list(self.api._parse_likes_iter(cases)),
                expected
        )


    def test_parse_likes(self):
        """_parse_likes()"""

        cases, expected = self.separate_cases_and_expected(
                self.like_cases)
        self.assertEqual(
                self.api._parse_likes(cases),
                expected
        )


    def test_parse_comment(self):
        """_parse_comment()"""

        for case, expected in self.comment_cases:
            self.assertEqual(
                    self.api._parse_comment(case),
                    expected
            )


    def test_parse_comments_iter(self):
        """_parse_comments_iter()"""

        cases, expected = self.separate_cases_and_expected(
                self.comment_cases)
        self.assertEqual(
                list(self.api._parse_comments_iter(cases)),
                expected
        )


    def test_parse_comments(self):
        """_parse_comments()"""

        cases, expected = self.separate_cases_and_expected(
                self.comment_cases)
        self.assertEqual(
                self.api._parse_comments(cases),
                expected
        )


    def test_parse_enclosures(self):
        """_parse_enclosures()"""

        enclosures = None
        self.assertEqual(
                self.api._parse_enclosures(enclosures),
                []
        )
        enclosures = [{'foo': 'bar'}]
        self.assertEqual(
                self.api._parse_enclosures(enclosures),
                enclosures
        )


    def test_parse_media_file(self):
        """_parse_media_file()"""

        for case, expected in self.media_cases:
            self.assertEqual(
                    self.api._parse_media_file(case),
                    expected
            )


    def test_parse_media_files_iter(self):
        """_parse_media_files_iter()"""

        cases, expected = self.separate_cases_and_expected(
                self.media_cases)
        self.assertEqual(
                list(self.api._parse_media_files_iter(cases)),
                expected
        )


    def test_parse_media_files(self):
        """_parse_media_files()"""

        cases, expected = self.separate_cases_and_expected(
                self.media_cases)
        self.assertEqual(
                self.api._parse_media_files(cases),
                expected
        )


    def test_parse_entry(self):
        """_parse_entry()"""

        for case, expected in self.entry_cases:
            result = self.api._parse_entry(case)
            self.assertEqual(
                    result,
                    expected
            )


    def test_parse_entries_iter(self):
        """_parse_entries_iter()"""

        cases, expected = self.separate_cases_and_expected(
                self.entry_cases)
        self.assertEqual(
                list(self.api._parse_entries_iter(cases)),
                expected
        )


    def test_parse_entries(self):
        """_parse_entries()"""

        cases, expected = self.separate_cases_and_expected(
                self.entry_cases)
        self.assertEqual(
                self.api._parse_entries(cases),
                expected
        )


    def test_parse_subscriptions_iter(self):
        """_parse_subscriptions_iter()"""

        cases = [
                self.user_profile_cases[0],
                self.imaginary_friend_cases[0]
                ]
        cases, expected = self.separate_cases_and_expected(cases)
        self.assertEqual(
                list(self.api._parse_subscriptions_iter(cases)),
                expected
        )


    def test_parse_subscriptions(self):
        """_parse_subscriptions()"""

        cases = [
                self.user_profile_cases[0],
                self.imaginary_friend_cases[0]
                ]
        cases, expected = self.separate_cases_and_expected(cases)
        self.assertEqual(
                self.api._parse_subscriptions(cases),
                expected
        )


class FriendFeedAPITests(unittest.TestCase):
    """Tests for FriendFeedAPI."""

    def setUp(self):

        self.api = friendfeed.FriendFeedAPI()

    def test_make_uri(self):
        """make_uri()"""

        cases = (
                (
                    '/feed/public',
                    {},
                    'http://friendfeed.com/api/feed/public'
                ),
                (
                    '/feed/public',
                    {'format': 'json'},
                    'http://friendfeed.com/api/feed/public?format=json'
                )
        )
        api = friendfeed.FriendFeedAPI()
        for resource, args, expected_uri in cases:
            if args:
                uri = api.make_uri(resource, args)
            else:
                uri = api.make_uri(resource)
            self.assertEqual(
                    uri,
                    expected_uri
            )


    def test_fetch_get(self):
        """_fetch() GET"""

        def urlopen(request):
            return open(ENTRY_JSON_PATH)

        api = friendfeed.FriendFeedAPI(urlopen=urlopen)
        result = api._fetch('http://friendfeed.com/api/feed/entry/658465da-3bc1-55fc-150b-c52c41cd158a')
        self.assertEqual(
                result,
                entry_example.entry_dict
        )


    def test_check_for_error(self):
        """_check_for_error()"""

        error_cases = [
            ('bad-id-format', friendfeed.BadIdFormatError),
            ('bad-url-format', friendfeed.BadUrlFormatError),
            ('entry-not-found', friendfeed.EntryNotFoundError),
            ('entry-required', friendfeed.EntryRequiredError),
            ('forbidden', friendfeed.ForbiddenError),
            ('image-format-not-supported',
                friendfeed.ImageFormatNotSupportedError),
            ('internal-server-error',
                friendfeed.InternalServerErrorError),
            ('limit-exceeded', friendfeed.LimitExceededError),
            ('room-not-found', friendfeed.RoomNotFoundError),
            ('room-required', friendfeed.RoomRequiredError),
            ('title-required', friendfeed.TitleRequiredError),
            ('unauthorized', friendfeed.UnauthorizedError),
            ('user-not-found', friendfeed.UserNotFoundError),
            ('user-required', friendfeed.UserRequiredError),
            ('error', friendfeed.FriendFeedError)
        ]

        for case, expected_error in error_cases:
            self.assertRaises(
                    expected_error,
                    self.api._check_for_error,
                    {'errorCode': case}
            )


if __name__ == '__main__':
    unittest.main()
