"""
Buddy
"""

from tools import *
import logging
from time import sleep

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
channel_id_list = []    # Create ID List
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


#Add the Users to the Track Channel
for row in range(0, len(df)):
    user_track = df['track'][row]
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
