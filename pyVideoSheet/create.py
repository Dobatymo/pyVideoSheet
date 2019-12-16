from __init__ import Video, Sheet
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create thumbnail contact sheet from a video.')
    parser.add_argument('filename', help='Input video filename.')
    parser.add_argument('--output','-o',default=None, metavar='<output_file>', help='Specift output video filename.')
    parser.add_argument('--interval', '-i', type=int, default=None, metavar='<sec>', help='Create thumnnails at fixed interval. Each thumbnail is <sec> seconds apart.')
    parser.add_argument('--number', '-n', type=int, default=None, metavar='<num>', help='Create total of <num> thumbnails. Each thumbnail is at equidistant apart.')
    parser.add_argument('--column','-c', type=int, default=None, metavar='<num>', help='Specify number of column of thumbnail sheet.')
    parser.add_argument('--notime', action='count', help='Remove thumbnail timestamp.')
    parser.add_argument('--header', type=int,default=None, metavar='<size>', help='Specify height of description header.')
    parser.add_argument('--thumbsize','-t', nargs=2, type=int, default=None, metavar=('<width>','<height>'), help='Specify maximum size of a thumbnail. The thumbnails will keep its aspect ratio unchanged.')
    parser.add_argument('--textcolour', nargs=4,type=int, default=None, metavar=('<r>','<g>','<b>','<a>'), help='Specify text colour of description. Colour is specify in RGBA format.')
    parser.add_argument('--bgcolour', nargs=4,type=int, default=None, metavar=('<r>','<g>','<b>','<a>'), help='Specify background colour of contact sheet. Colour is specify in RGBA format.')
    parser.add_argument('--font', nargs=2, default=None, metavar=('<fontfile>','<size>'), help='Specify font of description. Any truetype font are supported.')
    parser.add_argument('--preview', action='count', help='Preview the result contact sheet.')
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
        sheet.setProperty('gridColumn',c)
    if args.header is not None:
        c = args.header
        if c<85:
            c=85
        sheet.setProperty('headerSize',c)
    if args.notime is not None:
        sheet.setProperty('timestamp',False)
    if args.thumbsize is not None:
        thumbsize = (args.thumbsize[0],args.thumbsize[1])
        sheet.setProperty('maxThumbSize',thumbsize)
    if args.textcolour is not None:
        colour = (args.textcolour[0],args.textcolour[1],args.textcolour[2],args.textcolour[3])
        sheet.setProperty('textColour',colour)
    if args.bgcolour is not None:
        colour = (args.bgcolour[0],args.bgcolour[1],args.bgcolour[2],args.bgcolour[3])
        sheet.setProperty('backgroundColour',colour)
    if args.font is not None:
        font = (args.font[0],int(args.font[1]))
        sheet.setProperty('font',font)

    if mode == 'number':
        sheet.makeSheetByNumber(count)
    else:
        sheet.makeSheetByInterval(count)

    if args.output is not None:
        sheet.sheet.save(args.output)
    else:
        sheet.sheet.save(args.filename[:-3] + 'jpg')

    if args.preview is not None:
        sheet.sheet.show()
