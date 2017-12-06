import io
import requests
from pkg_resources import resource_stream

from PIL import Image, ImageDraw, ImageFont

NEARLY_WHITE = (239, 247, 247, 255)
ALMOST_BLACK = (8, 8, 16, 255)

def bytes_to_image(img_bytes):
    """Convert bytes (e.g. request.content after getting a jpg) to Image"""

    return Image.open(io.BytesIO(img_bytes))

def image_to_bytes(img, frmt='png'):
    """Convert an image to bytes."""

    obj = io.BytesIO()
    img.save(obj, format=frmt)
    obj.seek(0)

    return obj

def get_average_value(img, pos=None):
    """Return the average Value(HSV) of the pixels in img"""
    if pos == 'top':
        h = img.height * (1/3)
        img = img.crop(0, 0, img.width, img.height * (1/3))
    elif pos == 'bottom':
        h = img.height * (1/3)
        img = img.crop(0, img.height * (2/3), img.width, img.height)
    else:
        h = img.height

    # This could raise an Exception if img isn't an RBG Image
    img = img.convert('HSV')
    hist = img.histogram()

    weighted_value = sum(i * v for i, v in enumerate(hist[512:]))

    return weighted_value / (h * img.width)

def image_is_dark(img, pos=None):
    """Return True if the image is relatively dark, True otherwise"""
    return get_average_value(img, pos) < 128

def load_font(url, size=60):
    if url:
        font_resp = requests.get(url)
        if not font_resp.ok:
            raise RuntimeError("Bad response from {0}: {1}".format(url, font_resp))
        font_data = io.BytesIO(font_resp.content)
    else:
        font_data = resource_stream(__name__, 'Jellee-Roman.otf')

    return ImageFont.truetype(font_data, size=size)

def place_text_on_image(txt, font, img, pos=None):
    """Return a new img with txt rendered on it in font at pos ('top', 'bottom', or 'center')"""

    is_dark = image_is_dark(img)
    text_color = is_dark and NEARLY_WHITE or ALMOST_BLACK
    outline_color = is_dark and ALMOST_BLACK or NEARLY_WHITE

    img_layer = img.convert('RGBA')
    text_layer = Image.new('RGBA', img_layer.size, (255, 255, 255, 0))

    tls = text_layer.size

    words = txt.split(' ');
    lines = []

    while words:
        current_line = words[:]
        words = []

        while font.getsize(' '.join(current_line))[0] > tls[0] * .9:
            words.insert(0, current_line.pop())

        lines.append(' '.join(current_line))

    text_lines = "\n".join(lines)

    text_draw = ImageDraw.Draw(text_layer)

    text_spacing = int(font.size*.2)
    text_size = text_draw.multiline_textsize(text_lines,
        font=font,
        spacing=text_spacing)

    width, height = tls

    if pos == 'top':
        height *= .3 # upper third
    elif pos == 'bottom':
        height *= 1.6 # bottom third

    text_pos = (int((width - text_size[0])/2), int((height - text_size[1])/2))

    # Draw outline
    for x in 2, -2:
        for y in 2, -2:
            text_draw.multiline_text(
                (text_pos[0]+x, text_pos[1]+y),
                text_lines,
                font=font,
                fill=outline_color,
                spacing=text_spacing,
                align="center")

    # Draw text
    text_draw.multiline_text(
        text_pos,
        text_lines,
        font=font,
        fill=text_color,
        spacing=text_spacing,
        align="center")

    return Image.alpha_composite(img_layer, text_layer)

def build_meme(orig_img, font_url, line1, line2):
    font_size = 60
    if orig_img.height < 550 or orig_img.width < 500:
        font_size = 48 # arbitrary rule of thumb

    font = load_font(font_url, font_size)

    final_img = place_text_on_image(line1, font, orig_img, pos='top')
    final_img = place_text_on_image(line2, font, final_img, pos='bottom')

    return final_img

if __name__ == '__main__':
    import os
    import text
    import flickr

    flickr_key = os.environ['FLICKR_KEY']
    flickr_secret = os.environ['FLICKR_SECRET']
    text_url = os.environ.get('TEXT_URL', None)
    font_url = os.environ.get('FONT_URL', None)

    txt_gen = text.TextGen(text_url)
    txt = txt_gen.make_short_sentence()

    f = flickr.Flickr(flickr_key, flickr_secret)
    photo = f.pick_photo(txt)
    photo_bytes = f.download_photo_bytes(photo)
    orig_img = bytes_to_image(photo_bytes)

    line1, line2 = txt_gen.split_meme(txt)
    print(line1)
    print(line2)

    img = build_meme(orig_img, font_url, line1, line2)

    img.show() # Should open in a window
