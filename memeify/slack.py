import requests
import logging
import os

logger = logging.getLogger()

def post_text_message(token, channel, text):
    url = 'https://slack.com/api/chat.postMessage'

    params = {
        'token': token,
        'channel': channel,
        'text': text or 'Hello, world!'
    }

    result = requests.get(url, params=params)

    if not result.ok or not result.json()['ok']:
        logger.error("Something went wrong")
        logger.error(result.status_code)
        logger.error(result.text)
        raise RuntimeError("Bad response from slack API")

    return

if __name__ == '__main__':
    slack_token = os.environ['SLACK_TOKEN']
    post_text_message(slack_token, 'general', 'Test message')
