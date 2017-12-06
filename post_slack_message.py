import os
import urllib

def lambda_handler(event, context):
    token = os.environ['SLACK_TOKEN']

    url = 'https://slack.com/api/chat.postMessage'

    params = {
        'token': token,
        'channel': 'general',
        'text': 'Hello, world!'
    }

    response = urllib.request.urlopen(url + '?' + urllib.parse.urlencode(params))

    print("Got: " + str(response.getcode()))
    print(response.read().decode('utf-8'))

    return
