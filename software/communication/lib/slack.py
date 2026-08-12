import json
import logging
import os

from lib import log
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError, SlackClientError
from slack_sdk.http_retry.builtin_handlers import ConnectionErrorRetryHandler

logging.getLogger('slack_sdk').setLevel(logging.WARNING)

def create_api():
    return WebClient(
        token=os.environ['SLACK_BOT_TOKEN'],
        timeout=7
    )

api = create_api()

def send_message(message):
    if isinstance(message, (dict, list)):
        message = json.dumps(
            message,
            indent=2,
            default=str,
        )
        text = f"```{message}```"
    else:
        text = str(message)

    try:
        api.chat_postMessage(
            channel=os.environ['SLACK_CHANNEL_ID'],
            text=text
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
