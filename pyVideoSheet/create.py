from __future__ import absolute_import, division

from argparse import ArgumentParser
from .__init__ import Video, Sheet

if __name__ == "__main__":
    parser = ArgumentParser(description='Create thumbnail contact sheet from a video.')
    parser.add_argument('filename',
        help='Input video filename.')
    parser.add_argument('--output', '-o', default=None, metavar='<output_file>',
        help='Specift output video filename.')
    parser.add_argument('--interval', '-i', type=int, default=None, metavar='<sec>',
        help='Create thumnnails at fixed interval. Each thumbnail is <sec> seconds apart.')
    parser.add_argument('--number', '-n', type=int, default=None, metavar='<num>',
        help='Create total of <num> thumbnails. Each thumbnail is at equidistant apart.')
    parser.add_argument('--column', '-c', type=int, default=None, metavar='<num>',
        help='Specify number of column of thumbnail sheet.')
    parser.add_argument('--notime', action='count',
        help='Remove thumbnail timestamp.')
    parser.add_argument('--header', type=int, default=None, metavar='<size>',
        help='Specify height of description header.')
    parser.add_argument('--thumbsize', '-t', nargs=2, type=int, default=None, metavar=('<width>', '<height>'),
        help='Specify maximum size of a thumbnail. The thumbnails will keep its aspect ratio unchanged.')
    parser.add_argument('--text_colour', nargs=4, type=int, default=None, metavar=('<r>', '<g>', '<b>', '<a>'),
        help='Specify text colour of description. Colour is specify in RGBA format.')
    parser.add_argument('--bgcolour', nargs=4, type=int, default=None, metavar=('<r>', '<g>', '<b>', '<a>'),
        help='Specify background colour of contact sheet. Colour is specify in RGBA format.')
    parser.add_argument('--font', nargs=2, default=None, metavar=('<fontfile>', '<size>'),
        help='Specify font of description. Any truetype font are supported.')
    parser.add_argument('--preview', action='count',
        help='Preview the result contact sheet.')
    parser.add_argument('--format', choices=("jpg", "png"), default="jpg",
        help='Picture format of the output file.')
    args = parser.parse_args()

    video = Video(args.filename)
    sheet = Sheet(video)

    count = 20
    mode = 'number'
    if args.interval is not None:
        mode = 'interval'
        count = args.interval
    if args.number is not None:
        mode = 'number'
        count = args.number
    if args.column is not None:
        c = args.column
        if c < 1:
            c = 1
        sheet.set_property('grid_column', c)
    if args.header is not None:
        c = args.header
        if c < 85:
            c = 85
        sheet.set_property('header_size', c)
    if args.notime is not None:
        sheet.set_property('timestamp', False)
    if args.thumbsize is not None:
        thumbsize = (args.thumbsize[0], args.thumbsize[1])
        sheet.set_property('max_thumb_size', thumbsize)
    if args.text_colour:
        colour = (args.text_colour[0], args.text_colour[1], args.text_colour[2], args.text_colour[3])
        sheet.set_property('text_colour', colour)
    if args.bgcolour is not None:
        colour = (args.bgcolour[0], args.bgcolour[1], args.bgcolour[2], args.bgcolour[3])
        sheet.set_property('background_colour', colour)
    if args.font is not None:
        font = (args.font[0], int(args.font[1]))
        sheet.set_property('font', font)

    if mode == 'number':
        sheet.make_sheet_by_number(count)
    else:
        sheet.make_sheet_by_interval(count)

    if args.output is not None:
        sheet.sheet.save(args.output)
    else:
        sheet.sheet.save(args.filename[:-3] + args.format)

    if args.preview is not None:
        sheet.sheet.show()
