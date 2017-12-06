import flickrapi

import logging
import os
import random
import requests

logger = logging.getLogger()

class Flickr:
    def __init__(self, key, secret):
        self.flickr = None
        self.auth(key, secret)

    def auth(self, key, secret):
        self.flickr = flickrapi.FlickrAPI(
            key,
            secret,
            format='parsed-json',
            store_token=False)

        return

    def search(self, text):
        "Call flickr's search, returning a list of photos with URLs"
        photos = self.flickr.photos.search(
            text=text,
            per_page='20',
            safe_search='1',
            content_type='1', # photos only, not screenshots
            media='photos',
            sort='relevance',
            extras='url_c')

        return [ p for p in photos['photos']['photo'] if 'url_c' in p ]

    def remove_short_words(self, text):
        return ' '.join([ t for t in text.split(' ') if len(t) > 2])

    def remove_first_word(self, text):
        return ' '.join([ t for t in text.split(' ')][1:])

    def pick_photo(self, text):
        "Use 'text' to search for a photo, until one is found"

        photos = self.search(text)

        text = self.remove_short_words(text)

        retries = 20
        while retries and not photos:
            retries -= 1
            text = self.remove_first_word(text)

            if not text:
                text = "kittens"
                logger.info("No images found for text, searching for kittens instead")

            photos = self.search(text)

        if not photos:
            raise RuntimeError("No photos found for '{0}'".format(text))

        logger.info("Found {0} image(s) for text.".format(len(photos)))

        return random.choice(photos)

    def download_photo_bytes(self, photo):
        """Download photo from it's url_c and return content (bytes)"""
        img_resp = requests.get(photo['url_c'])

        if not img_resp.ok:
            raise RuntimeError("Didn't get OK from get '{0}', got '{1}'".format(photo['url_c'], img_resp))

        return img_resp.content

if __name__ == '__main__':
    flickr_key = os.environ['FLICKR_KEY']
    flickr_secret = os.environ['FLICKR_SECRET']

    f = Flickr(flickr_key, flickr_secret)
    photo = f.pick_photo("happy day")

    print(photo)
