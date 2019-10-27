import sys

from PIL import Image
import argparse
import math

OFFSET = 0x2800
p = argparse.ArgumentParser()
p.add_argument('img')
p.add_argument('-sp', '--size-percent', dest='size_percent', default=-1, type=int, help='The size percentage')
p.add_argument('-mx', dest='max_x', default=128, type=int, help='Max x')
p.add_argument('-my', dest='max_y', default=128, type=int, help='Max y')
p.add_argument('-r', '--reverse', action='store_true', dest='reverse', help='Reverse colors')
p.add_argument('-v', '--verbose', action='store_true', dest='verbose')
p.add_argument('-b', '--binary', action='store_true', dest='binary', help='Don\'t crop, and use one character per '
                                                                          'pixel')
p.add_argument('--not-full', action='store_true', dest='not_full', help='Avoid using full characters')
p.add_argument('-nf', '--no-flush', action='store_true', dest='nf')
p.add_argument('--ignore-max-pixels', action='store_true', dest='no_max', help='Ignore maximum amount of pixels.')

p.add_argument('--output', dest='output', help='output, duh')
args = p.parse_args()


def print_nf(*msg, end='\n', sep=' '):
    """print function without flushing"""
    sys.stdout.write(sep.join(msg) + end)


if args.nf:
    print = print_nf
if args.no_max:
    Image.MAX_IMAGE_PIXELS = None

if (args.max_x != 128 or args.max_y != 128) and args.size_percent != -1:
    # noinspection PyUnboundLocalVariable
    print('Arguments -mx, -my are not compatible with -sp')
    exit(2)

if args.img == '-':  # stdin
    img = Image.open(sys.stdin.buffer)
else:
    img = Image.open(args.img)
org_size = (img.width, img.height)
if args.size_percent == -1:
    img.thumbnail((args.max_x, args.max_y))
else:
    new_size = (org_size[0] * (args.size_percent / 100), org_size[1] * (args.size_percent / 100))
    if args.size_percent > 100:
        img = img.resize((round(new_size[0]), round(new_size[1])))
    else:
        img.thumbnail(new_size)

img = img.convert('LA')
if args.verbose:
    print('Converted image to {0}X{1} or {2:.2f}% area, {3:.2f}% of X, {4:.2f}% of Y of the original size.'
          ''.format(img.width,
                    img.height,
                    ((img.width * img.height)
                     / (org_size[0] * org_size[1])
                     * 100),
                    (img.width / org_size[0] * 100),
                    (img.height / org_size[1] * 100)))
output = ''
dots = []


def divide_image(image, max_size):
    offset = (0, 0)
    output = []
    # Podziel po x
    for y in range(math.ceil(image.height / max_size[1])):
        for x in range(math.ceil(image.width / max_size[0])):
            curr_img = image.crop(box=(offset[0], offset[1], offset[0] + max_size[0], offset[1] + max_size[1]))
            output.append([offset, curr_img])
            # curr_img.show()
            offset = (offset[0] + max_size[0], offset[1])
        offset = (0, offset[1] + max_size[1])
        output.append([offset, '\n'])
    return output


_print = print
if args.output:
    output_file = open(args.output, 'w')


    def print(*args, **kwargs):
        kwargs.update({'file': output_file})
        _print(*args, **kwargs)

POSITIONS = [
    0x1, 0x8, 0x2, 0x10, 0x4, 0x20, 0x40, 0x80
]
if not args.binary:
    parts = divide_image(img, (2, 4))
    for i in parts:
        data = 0
        pos = 0
        if i[1] == '\n':
            print()
            continue
        for y in range(i[1].height):
            for x in range(i[1].width):
                val = i[1].getpixel((x, y))
                binary = val[0] > 181 / 2
                if val[1] == 0:
                    binary = False
                if (not binary and not args.reverse) or (binary and args.reverse):
                    data += POSITIONS[pos]
                pos += 1
        print(chr(OFFSET + data), end='')
else:
    sum_all = sum(POSITIONS)
    empty = chr(OFFSET) * 2
    full = chr(OFFSET + sum_all) * 2
    for y in range(img.height):
        for x in range(img.width):
            val = img.getpixel((x, y))
            binary = val[0] > 181 / 2
            if val[1] == 255:
                binary = False

            if (not binary and not args.reverse) or (binary and args.reverse):
                print(full, end='')
            else:
                print(empty, end='')
        print()
sys.stdout.flush()
