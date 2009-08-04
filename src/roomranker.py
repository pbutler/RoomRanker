#!/usr/bin/env python
# vim: et ts=4 sw=4 smarttab
# -*- coding: UTF-8 -*-

"""
Reports the popularity rankings of members of a FriendFeed room.

"""

__author__ = 'Chris Lasher'
__email__ = 'chris DOT lasher <AT> gmail DOT com'


import ConfigParser
import optparse
import os
import sys
import sys
import friendfeed


# Configuration file name
RC_FILE = '.roomrankerrc'
# By default, this program will look under the user's home directory for
# a configuration
#RC_PATH = os.path.expanduser('~') + os.sep + RC_FILE

# The configuration file should be a file containing one section with
# two variables: username and password. For example, it should look
# something like below:
#
# [User]
# username=myusername
# password=mypassword

USER_SECTION = 'User'


class UserInfoError(Exception):
    """
    Error raised when there is not enough information from the user
    to obtain a handle for the API.

    """

    pass


def make_cli_parser():

    usage = "\n\n".join([
        """\
python %prog [OPTIONS] ROOM

ARGUMENTS:
    ROOM: the nickname of the room to analyze (e.g., friendfeed-api for
        the "FriendFeed API" room)\
""",
        __doc__,
        """\
By default, runs an unauthenticated check. You can authenticate by
either placing your account information in a configuration file, or by
specifying your user name and password on the command line. See help for
options and details.

    python %prog -h\
"""])

    cli_parser = optparse.OptionParser(usage)
    cli_parser.add_option('-c', '--config',
        default=RC_PATH,
        help="Specify a different path to a configuration file"
        " [default: %default]"
    )
    cli_parser.add_option('-u', '--username',
        help="Specify a user name directly"
    )
    cli_parser.add_option('-p', '--password',
        help="Specify a password directly"
    )

    return cli_parser


def get_config_username_and_password(config_file_path):

    config = ConfigParser.ConfigParser()
    config.read(config_file_path)
    if config.has_option(USER_SECTION, 'username'):
        username = config.get(USER_SECTION, 'username')
    else:
        username = None

    if config.has_option(USER_SECTION, 'password'):
        password = config.get(USER_SECTION, 'password')
    else:
        password = None

    return username, password


def get_username_and_password(cli_opts):
    username = cli_opts.username
    password = cli_opts.password
    if not (username and password):
        config_file_path = cli_opts.config
        if os.path.isfile(config_file_path):
            cfg_username, cfg_password = \
                    get_config_username_and_password(config_file_path)

        if not username:
            username = cfg_username
        if not password:
            password = cfg_password

    return username, password


def get_api(username, password):
    if (username and password):
        api = friendfeed.FriendFeedAPI(username, password)
    else:
        print "Not enough user information. Running unauthenticated."
        api = friendfeed.FriendFeedAPI()

    return api

def generate_rankings(users):
    sortee = [ (len(v), k) for k,v in users.items() ]
    sortee.sort()
    sortee.reverse()
    return [ (k,v) for v,k in sortee ]


def main(argv):
    cli_parser = make_cli_parser()
    opts, args = cli_parser.parse_args(argv)
    if len(args) != 1:
        cli_parser.error("Give the nickname of a room")
    room_nickname = args[0]
    validate_nickname(room_nickname)
    username, password = get_username_and_password(opts)
    api = get_api(username, password)
    ## TODO: fetch room profile, then for each user, see who in the room
    ## the user follows
    #room = api.get_room_profile(


if __name__ == '__main__':
    main(sys.argv[1:])
