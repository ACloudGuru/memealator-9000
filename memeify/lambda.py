from memeify import slack, text, images, flickr

import boto3
from botocore.client import Config
from boto3.dynamodb.conditions import Key

import logging
import os
import time
import uuid
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # 'SINGLE', 'DOUBLE', 'LONG'
    click_type = event.get('clickType', 'SINGLE')

    if click_type == 'SINGLE':
        make_new_meme(event, context)
    elif click_type == 'LONG':
        upvote_last_meme(event, context)

    return

def make_new_meme(event, context):
    ## Environment
    #
    # Required
    flickr_key = os.environ['FLICKR_KEY']
    flickr_secret = os.environ['FLICKR_SECRET']
    slack_token = os.environ['SLACK_TOKEN']
    meme_bucket_name = os.environ['MEMES_BUCKET_NAME']
    aws_region = os.environ['AWS_REGION']
    #
    # Optional
    font_url = os.environ.get('FONT_URL', None)
    text_url = os.environ.get('TEXT_URL', None)
    slack_channel = os.environ.get('SLACK_CHANNEL', 'general')
    meme_table_name = os.environ.get('MEMES_TABLE_NAME', 'memes')
    #
    ## End Environment

    session = boto3.Session(region_name=aws_region)

    # Generate text
    txt_gen = text.TextGen(text_url)
    txt = txt_gen.make_short_sentence()
    logging.info("Text: '{0}'".format(txt))

    # Pick a photo
    flckr = flickr.Flickr(flickr_key, flickr_secret)
    photo = flckr.pick_photo(txt)

    orig_url = "https://www.flickr.com/photos/{0}/{1}".format(photo['owner'],
                                                              photo['id'])
    logging.info("Photo: '{0}'".format(orig_url))

    photo_bytes = flckr.download_photo_bytes(photo)
    orig_img = images.bytes_to_image(photo_bytes)

    # Put text on image
    line1, line2 = txt_gen.split_meme(txt)
    img_obj = images.build_meme(orig_img, font_url, line1, line2)


    meme_uuid = uuid.uuid4()
    s3_key = 'memes/{0}.png'.format(meme_uuid)

    # Upload final image to S3
    s3 = session.resource('s3')
    meme_bucket = s3.Bucket(meme_bucket_name)

    meme_bucket.upload_fileobj(
        images.image_to_bytes(img_obj),
        s3_key,
        ExtraArgs={'ContentType': 'image/png', 'ACL': 'public-read'}
        )

    # save metadata to dynamodb
    dynamodb = session.resource('dynamodb')
    meme_table = dynamodb.Table(meme_table_name)

    s3_url = "https://s3-{0}.amazonaws.com/{1}/{2}".format(aws_region,
                                                           meme_bucket_name,
                                                           s3_key)

    db_response = meme_table.put_item(
       Item={
            'button_id': event.get('serialNumber', 'None'),
            'unixtime': Decimal(str(time.time())),
            'uuid': str(meme_uuid),
            'text': txt,
            's3_url': s3_url,
            'orig_url': orig_url
        }
    )

    # Post to slack
    slack.post_text_message(slack_token, slack_channel, s3_url)

    return

def upvote_last_meme(event, context):
    # Add an upvote for the last shown meme

    ## Environment
    #
    # Required
    slack_token = os.environ['SLACK_TOKEN']
    aws_region = os.environ['AWS_REGION']
    #
    # Optional
    meme_table_name = os.environ.get('MEMES_TABLE_NAME', 'memes')
    votes_table_name = os.environ.get('VOTES_TABLE_NAME', 'meme_votes')
    slack_channel = os.environ.get('SLACK_CHANNEL', 'general')
    #
    ## End environment

    session = boto3.Session(region_name=aws_region)

    # Load last meme from db
    dynamodb = session.resource('dynamodb')
    meme_table = dynamodb.Table(meme_table_name)

    button_id = event.get('serialNumber', 'None')

    res = meme_table.query(
        KeyConditionExpression=Key("button_id").eq(button_id) & \
            Key("unixtime").lt(Decimal(str((time.time())))),
        Limit=1,
        ScanIndexForward=False,
    )

    if not res.get('Count', None):
        logger.error("Could not find record for button id '{0}'.".format(button_id))
        return

    # Add an upvote
    votes_table = dynamodb.Table(votes_table_name)
    res = votes_table.put_item(
           Item={
                'button_id': event.get('serialNumber', 'None'),
                'meme_unixtime': res['Items'][0]['unixtime'],
                'vote_unixtime': Decimal(str(time.time()))
                }
            )

    slack.post_text_message(slack_token, slack_channel, "Upvoted!")

    return
