""""""

import sys
import os
import yaml
import logging
import pandas as pd
import numpy as np
from slack import WebClient, errors


# Set Logging
logging.basicConfig(format='%(levelname)s : %(module)s : %(funcName)s >> %(message)s',
                    #level=logging.DEBUG)
                    level=logging.INFO)
# read token
if len(sys.argv) >= 2:
    token = sys.argv[1]
    logging.info("Token set to: {}".format(token))
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

    def __init__(self, suffix, track):
        self.members = []
        self.size = 0
        self.slack_id = ''
        # Set Track
        self.track = track
        # Set the Name
        self.name = "{}-{}-{}".format(cfg['buddy groups']['prefix'], track, suffix).lower()
        # Set max size
        self.max_size = cfg['buddy groups']['members']

    def check_size(self):
        self.size = len(self.members)
        return self.size

    def add_member(self, email, name, id):
        new_member = {'id': id,
                      'name': name,
                      'email': email}
        self.members.append(new_member)
        #return new_member



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
