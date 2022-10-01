from email import message
import time
import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from slackeventsapi import SlackEventAdapter


env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']

app = Flask(__name__)

slack_event_adapter = SlackEventAdapter(
    os.environ['SIGNING_SECRET'], '/slack/events', app)

message_counts = {}


class WelcomeMessage:
    START_TEXT = {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': (
                'Welcome to this awesome channel!\n\n'
                '*Get started by completing this survey!'
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
            'ts': self.timestamp,
            'channel': self.channel,
            'username': 'Welcome Robot',
            'icon_emoji': self.icon_emoji,
            'blocks': [
                self.START_TEXT,
                self.DIVIDER,
                self._get_reaction_task()
            ]
        }

    def _get_reaction_task(self):
        checkmark = ':white_check_mark'
        if not self.completed:
            checkmark = ':white_large_square'

        text = f'{checkmark} *React to this message'

        return {'type': 'section', 'text': {'type': 'mrkdwn', 'text': text}}


# @slack_event_adapter.on('message')
# def message(payload):
#     event = payload.get('event', {})
#     channel_id = event.get('channel')
#     user_id = event.get('user')
#     text = event.get('text')
#     if user_id != BOT_ID:
#         client.chat_postMessage(channel='#test', text=text)
@slack_event_adapter.on('member_joined_channel')
def member_joined_channel(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    client.chat_postMessage(channel=user_id, as_user=True,
                            text="Hello and welcome to BisConnect. To connect you to your peers, please fill out this form! www.google.com")
    time.sleep(3)
    client.chat_postMessage(channel=user_id, as_user=True,
                            text="We have found a group that shares your interest of: Sports. Would you like to join?")


@slack_event_adapter.on('app_mention')
def app_mention(payload):
    # print(payload)
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    client.chat_postMessage(channel=user_id, as_user=True,
                            text="Hello and welcome to BisConnect. To connect you to your peers, please fill out this form! www.google.com")


if __name__ == "__main__":
    app.run(debug=True)
