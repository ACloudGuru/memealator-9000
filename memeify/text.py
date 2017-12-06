import markovify
import math
import os
import requests
from pkg_resources import resource_string

class TextGen:
    def __init__(self, url=None):
        self.text_model = None

        if url:
            # Get text from URL
            text_resp = requests.get(url)
            if not text_resp.ok:
                raise RuntimeError("Bad response from {0}: {1}".format(url, text_resp))

            # Build the model.
            self.text_model = markovify.Text(text_resp.content.decode('utf-8'))
        else:
            # Get raw text as string.
            text = resource_string(__name__, 'pg100.txt')

            # Build the model.
            self.text_model = markovify.Text(text.decode('utf-8'))

        return

    def make_short_sentence(self, length=120):
        return self.text_model.make_short_sentence(length)

    @classmethod
    def split_meme(cls, txt):
        """Split txt into a two element tuple"""

        if ' ' not in txt:
            return tuple(txt, txt)

        if ';' in txt[:-1]:
            return tuple(p.strip() for p in txt.split(';', maxsplit=1))

        words = txt.split(' ')

        # Q: What the heck is Robin doing?
        # A: Using the golden ratio for no good reason
        #    ...but, it does split the text about 60/40
        split_point = math.floor(len(words)/1.618)

        return (' '.join(words[0:split_point]), ' '.join(words[split_point:]))

if __name__ == '__main__':
    text_url = os.environ.get('TEXT_URL', None)

    txt_gen = TextGen(text_url)
    txt = txt_gen.make_short_sentence()
    line1, line2 = txt_gen.split_meme(txt)
    print(line1)
    print(line2)
