"""
Buddy
"""

from tools import *
import logging
import math
from time import sleep

# Intro
terminal_intro("Study Buddy")

# Create Slack App

App = SlackApp()

# Import CSV with filtered Columns
df = rename_and_filer_columns(*cfg['columns'])

# Fill Slack User IDS using the Email column
df = fill_user_ids(App, df, 'email')

# Check Slack API
# Channel Check
logging.info("Checking Channel IDs")
App.update_channels()
channel_id_list = []  # Create ID List
for channel in App.channels:
    channel_id_list.append(str(channel['id']))
for key, val in cfg['track channels'].items():
    if val in channel_id_list:
        logging.debug("Channel for {} with ID {} is valid!".format(key, val))
    else:
        raise Exception("Channel for {} with ID {} cannot be found in Workspace!"
                        " check the ID and make sure that the Bot is part of the Channel".format(key, val))
logging.info("Channel IDs are valid!")
# Users Check
logging.info("Checking User IDs")
App.update_users()
user_id_list = []
for user in App.users:
    user_id_list.append(str(user['id']))
for row in range(0, len(df)):
    user_id = df['ID'][row]
    user_email = df['email'][row]
    if user_id in user_id_list:
        logging.debug("User {} with ID {} exist in Workspace".format(user_email, user_id))
    else:
        raise Exception("User {} with ID {} cannot be found in the workspace".format(user_email, user_id))
logging.info("User IDs are valid!")

# Add the Users to the Track Channel
track_comlumns = ['track1', 'track2', 'track3', 'track4']
if query_yes_no("Should I Add the Users to the respective track channels?"):
    for row in range(0, len(df)):
        for track_comlumn in track_comlumns:
            if str(df[track_comlumn][row]) != 'nan':
                user_track = df[track_comlumn][row]
                user_id = df['ID'][row]
                channel_id = cfg['track channels'][user_track]
                user_email = df['email'][row]
                try:
                    App.add_to_channel(user_id, channel_id)
                    logging.info("user {} with ID {} was added to the channel {}({})".format(user_email,
                                                                                             user_id,
                                                                                             user_track,
                                                                                             channel_id))
                except errors.SlackApiError:
                    logging.error("could not Add user {} with ID {} to the channel {}({})".format(user_email,
                                                                                                  user_id,
                                                                                                  user_track,
                                                                                                  channel_id))

# Create Data frames for each track
tracks_dfs = dict()
for key, val in cfg['track channels'].items():
    track_filter = df[track_comlumns[0]] == key
    tracks_dfs[key] = df[track_filter]

# Create the groups
buddy_groups = []

for key, val in tracks_dfs.items():
    # Check if there's a techie in the Track
    techies_nr = len(val)
    if techies_nr != 0:
        # restart sufix
        buddy_group_nr = 1
        # Check for an optimal number of members
        desired_members = cfg['buddy groups']['members max']

        leftover = techies_nr % desired_members
        group_nr = techies_nr / desired_members
        while not (leftover == 0 or leftover > cfg['buddy groups']['members min']):
            # try to find a better group size
            desired_members -= 1
            if desired_members < cfg['buddy groups']['members min']:
                raise Exception(" Cannot find a optimal size for groups in the {} track".format(key))
            techies_nr = len(val)
            leftover = techies_nr % desired_members
            group_nr = techies_nr / desired_members
        if leftover:
            logging.info("for track {}, {} groups each with {} (last group with {})".format(key,
                                                                                            math.ceil(group_nr),
                                                                                            desired_members,
                                                                                            leftover))
        else:
            logging.info("for track {}, {} groups each with {}".format(key,
                                                                       math.ceil(group_nr),
                                                                       desired_members))
        # Make Groups accordingly
        groups = {n: val.iloc[n:n + desired_members, :]
                  for n in range(0, len(val), desired_members)}
        # Save groups in the array
        for g_key, g_val in groups.items():
            buddy_groups.append(BuddyGroup(buddy_group_nr, key, g_val))
            buddy_group_nr += 1
    else:
        logging.warning("the track {} is empty!".format(key))

# Check that the channels do not exist (known channels)
channel_name_list = []
for channel in App.channels:
    channel_name_list.append(str(channel['name']))
for buddy_group in buddy_groups:
    if buddy_group.name in channel_name_list:
        raise Exception("a channel with the name {} already exist in the workspace!".format(buddy_group.name))

# Ask the user
width = 50
# sleep(3)
print('\n'
      '>>>>I Will create the following Groups:')
for buddy_group in buddy_groups:
    print()
    print()
    print("|{}|".format("=" * 96))
    print("|{:^96}|".format('#' + buddy_group.name))
    print("|{}|".format("=" * 96))
    print('|{:^30}|{:63d}  |'.format('SIZE', buddy_group.size))
    print('|{:^30}|{:>63}  |'.format('TRACK', buddy_group.track))
    print("|{:-^96}|".format('MEMBERS'))
    print("|{:_^30.30}|{:_^51.51}|{:_^13.13}|".format('Full_Name', 'email', 'SlackID'))
    for index, row in buddy_group.members.iterrows():
        print("|{:^30.30}|{:^51.51}|{:^13.13}|".format('{} {}'.format(row['name'], row['last name']),
                                                       row['email'],
                                                       row['ID']))
    print("|{}|".format("=" * 96))
print()
print()
print("and will post the following message:\n{}".format(cfg['buddy groups']['start message']))

if query_yes_no("Should I Proceed?"):
    for buddy_group in buddy_groups:
        # Create Channel
        try:
            response = App.client.conversations_create(name=buddy_group.name, is_private=True)
        except errors.SlackApiError:
            logging.warning("Cannot create the channel #{}, will try with the name #{}".format(buddy_group.name,
                                                                                               buddy_group.name + '_2'))
            try:
                response = App.client.conversations_create(name=buddy_group.name + '_2', is_private=True)

            except errors.SlackApiError:
                logging.error("Cannot create the channel #{} or #{}".format(buddy_group.name,
                                                                            buddy_group.name + '_2'))
                continue

        # Set Channel ID
        buddy_group.slack_id = response['channel']['id']
        # Add techies
        for index, row in buddy_group.members.iterrows():
            try:
                App.add_to_channel(row['ID'], buddy_group.slack_id)
                logging.info("user {} with ID {} was added to the channel ({}) {}".format(
                    '{} {}'.format(row['name'], row['last name']),
                    row['ID'],
                    buddy_group.slack_id,
                    buddy_group.name))
            except errors.SlackApiError:
                logging.error("could not Add user {} with ID {} to the channel ({}){}".format(
                    '{} {}'.format(row['name'], row['last name']),
                    row['ID'],
                    buddy_group.slack_id,
                    buddy_group.name))
        # Send Message
        message = cfg['buddy groups']['start message']
        try:
            response = App.client.chat_postMessage(
                channel=buddy_group.slack_id,
                text=message
            )
            logging.info("Message sent! to channel {}".format(buddy_group.name))
        except errors.SlackApiError as e:
            # You will get a SlackApiError if "ok" is False
            assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
else:
    logging.warning("No Studdy Buddy Groups were created...")
