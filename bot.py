import time
from urllib import response
import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from slackeventsapi import SlackEventAdapter
import re


env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']

app = Flask(__name__)

slack_event_adapter = SlackEventAdapter(
    os.environ['SIGNING_SECRET'], '/slack/events', app)

message_counts = {}
surveys = {}
invited = set()


class WelcomeMessage:
    START_TEXT = {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': (
                'Welcome to this awesome channel!\n\n'
                '*Get started by completing this survey! React with a :white_check_mark: when you\'re done*\n\n'
                'www.placeholder.com'
            )
        }
    }

    DIVIDER = {'type': 'divider'}

    def __init__(self, channel, user):
        self.channel = channel
        self.user = user
        self.icon_emoji = ':robot_face:'
        self.timestamp = ''
        self.completed = False

    def get_message(self):
        return {
            'as_user': True,
            'ts': self.timestamp,
            'channel': self.user,
            'username': 'Welcome Robot',
            'icon_emoji': self.icon_emoji,
            'blocks': [
                self.START_TEXT,
                self.DIVIDER
            ]
        }


def delete_message_history(channel):
    history = client.conversations_history(channel=channel).get('messages')
    for mes in history:
        client.chat_delete(**mes, channel=channel)


def send_welcome_message(channel, user):
    welcome = WelcomeMessage(channel, user)
    message = welcome.get_message()
    response = client.chat_postMessage(**message)
    welcome.timestamp = response['ts']
    surveys[user] = response['ts']


def make_slack_channel(user_ids, interest):
    channel_name = interest.lower() + "-"
    for id in user_ids:
        rawname = client.users_info(user=id).get('user').get('name').lower()
        name = re.sub("[^A-Za-z]", "", rawname)
        channel_name += name + "-"
    channel_name = channel_name[0:len(channel_name)-1]
    print(channel_name)
    channel_id = client.conversations_create(
        name=channel_name).get('channel').get('id')
    client.conversations_invite(channel=channel_id, users=user_ids)
    group_welcome = "Greetings "
    for i in range(0, len(user_ids)-1):
        name = client.users_info(user=user_ids[i]).get('user').get('name')
        group_welcome += name + ", "
    group_welcome += "and " + \
        client.users_info(user=user_ids[-1]).get('user').get('name')
    group_welcome += ". This is a group chat created based on your shared interest of: " + interest + "."
    client.chat_postMessage(channel=channel_id, text=group_welcome)


@slack_event_adapter.on('member_joined_channel')
def member_joined_channel(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    if BOT_ID != user_id and user_id != None and user_id not in invited:
        invited.add(user_id)
        send_welcome_message(channel_id, user_id)
        # time.sleep(30)
        make_slack_channel([user_id, 'U044JTNB8CE', 'U045F7RNLRE'], "Soccer")

# @slack_event_adapter.on('app_mention')
# def app_mention(payload):
#     # print(payload)
#     event = payload.get('event', {})
#     channel_id = event.get('channel')
#     user_id = event.get('user')
#     # client.chat_postMessage(channel=user_id, as_user=True,
#     #                         text="Hello and welcome to BisConnect. To connect you to your peers, please fill out this form! www.google.com")
#     if BOT_ID != user_id and user_id != None:
#         send_welcome_message(channel_id, user_id)
#         print("SURVEYS:")
#         print(surveys)
#     make_slack_channel([user_id, 'U044JTNB8CE'], "Soccer")


@slack_event_adapter.on('reaction_added')
def reaction(payload):
    event = payload.get('event', {})
    channel_id = event.get('item', {}).get('channel')
    user_id = event.get('user')
    reactions = client.reactions_get(
        timestamp=surveys.get(user_id), channel=channel_id)
    message_reactions = reactions.get('message').get('reactions')
    if (message_reactions is not None):
        for dic in message_reactions:
            if (dic.get('name') == 'white_check_mark'):
                client.chat_delete(ts=surveys.get(user_id), channel=channel_id)


if __name__ == "__main__":
    app.run(debug=True)
