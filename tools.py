""""""

import sys
import os
import yaml
import logging
import pandas as pd
import numpy as np
import pyfiglet
from slack import WebClient, errors


# Set Logging
logging.basicConfig(format='%(levelname)s : %(module)s : %(funcName)s >> %(message)s\n',
                    #level=logging.DEBUG)
                    level=logging.INFO)
# read token
if len(sys.argv) >= 2:
    token = sys.argv[1]
    logging.debug("Token set to: {}".format(token))
else:
    logging.error("Not enough Arguments! (need token)")
    raise Exception('give the xoxb token as the first argument')


actual_folder = os.path.dirname(os.path.abspath(__file__))
with open(actual_folder + "/config.yml") as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)


class SlackApp:
    """
    App Manager
    """
    users = []
    channels = []

    def __init__(self):
        # Connection
        self.client = WebClient(token=token)

    def update_users(self):
        self.users = self.client.users_list()['members']
        logging.info("Users found = {}".format(len(self.users)))
        return self.users

    def add_to_channel(self, user_id, channel_id):
        self.client.conversations_invite(channel=channel_id, users=[user_id])

    def update_channels(self):
        self.channels = self.client.conversations_list(types="public_channel, private_channel")['channels']
        logging.info("Channels found = {}".format(len(self.channels)))
        return self.channels


class BuddyGroup:
    """
    Buddy Group
    """

    def __init__(self, suffix, track, members):
        self.members = members
        self.size = len(members)
        self.slack_id = ''
        # Set Track
        self.track = track
        # Set the Name
        self.name = "{}-{}-{}".format(cfg['buddy groups']['prefix'], track, suffix).lower()







def rename_and_filer_columns(*args):
    # Read csv
    df = pd.read_csv(cfg['csv'], sep=cfg['separator'])
    columns = []
    # Rename the Columns
    for arg in args:
        for key, val in arg.items():
            df.rename(columns={val: key}, inplace=True)
            columns.append(key)

    # Filter the columns
    return df[columns]


def fill_user_ids(App, df, email_column):
    # Check for users
    App.update_users()
    # Add an empty Column
    df['ID'] = ''
    for row in range(0, len(df)):
        df_email = df[email_column][row]
        for user in App.users:
            try:
                if str(df_email) == user['profile']['email']:
                    df.at[row, 'ID'] = user['id']
            except KeyError:
                logging.debug('No Email found for user with id {}'.format(user['id']))
    return df


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def terminal_intro(title):
    print("{:_^61}".format("_"))
    ascii_banner = pyfiglet.figlet_format(title)
    print(ascii_banner)
    print("{:^61}".format("By Andrés David Vega Botero"))
    print("{:_^61}".format("_"))
    print()