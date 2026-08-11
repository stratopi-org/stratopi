import os

from lib import log
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError, SlackClientError


def create_api():
    return WebClient(token=os.environ['SLACK_BOT_TOKEN'])

api = create_api()

def send_message(message):
    try:
        api.chat_postMessage(
            channel=os.environ['SLACK_CHANNEL_ID'],
            text=message,
        )
    except SlackApiError as err:
        error = err.response.get('error', 'unknown_error')
        log.error(f'slack API error: {error}')
        return False
    except SlackClientError as err:
        log.error(f'slack client error: {err}')
        return False
    except OSError as err:
        log.error(f'slack connection error: {err}')
        return False

    return True
