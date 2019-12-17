from __future__ import absolute_import, division, print_function

from genutility.compat import FileExistsError
from genutility.compat.os import makedirs
from .__init__ import Video, Sheet, InvalidVideoFile

def do(args, inpath, outfile=None, outdir=None, overwrite=False):
    assert outfile is None or outdir is None

    filename = str(inpath)

    if outfile:
        outpath = outfile
    elif outdir:
        outpath = outdir / Path(inpath.name[:-3] + args.format)
    else:
        outpath = Path(filename[:-3] + args.format)
    
    if not overwrite and outpath.exists():
        raise FileExistsError(outpath)

    try:
        video = Video(filename)
        sheet = Sheet(video, args.columns, not args.notime, args.bgcolour, args.text_colour, args.thumbsize)

        count = 20
        mode = 'number'
        if args.interval is not None:
            mode = 'interval'
            count = args.interval
        if args.number is not None:
            mode = 'number'
            count = args.number
        if args.header is not None:
            c = args.header
            if c < 85:
                c = 85
            sheet.set_property('header_size', c)
        if args.font is not None:
            font = (args.font[0], int(args.font[1]))
            sheet.set_property('font', font)

        if mode == 'number':
            imgsheet = sheet.make_sheet_by_number(count)
        else:
            imgsheet = sheet.make_sheet_by_interval(count)

        imgsheet.save(outpath)

        if args.preview is not None:
            imgsheet.show()

    except InvalidVideoFile as e:
        print("Invalid video file", inpath, str(e))

if __name__ == "__main__":
    from pathlib import Path
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter,
        description='Create thumbnail contact sheet from a video.')
    parser.add_argument('filename', type=Path,
        help='Input video filename or directory.')
    parser.add_argument('--output', '-o', default=None, metavar='<output_file>', type=Path,
        help='Specify output video filename or directory.')
    parser.add_argument('--interval', '-i', type=int, default=None, metavar='<sec>',
        help='Create thumnnails at fixed interval. Each thumbnail is <sec> seconds apart.')
    parser.add_argument('--number', '-n', type=int, default=None, metavar='<num>',
        help='Create total of <num> thumbnails. Each thumbnail is at equidistant apart.')
    parser.add_argument('--columns', '-c', type=int, default=5, metavar='<num>',
        help='Specify number of column of thumbnail sheet.')
    parser.add_argument('--notime', action='store_true',
        help='Remove thumbnail timestamp.')
    parser.add_argument('--header', type=int, default=None, metavar='<size>',
        help='Specify height of description header.')
    parser.add_argument('--thumbsize', '-t', nargs=2, type=int, default=(220, 220), metavar=('<width>', '<height>'),
        help='Specify maximum size of a thumbnail. The thumbnails will keep its aspect ratio unchanged.')
    parser.add_argument('--text_colour', nargs=4, type=int, default=(255, 255, 255, 0), metavar=('<r>', '<g>', '<b>', '<a>'),
        help='Specify text colour of description. Colour is specify in RGBA format.')
    parser.add_argument('--bgcolour', nargs=4, type=int, default=(0, 0, 0, 0), metavar=('<r>', '<g>', '<b>', '<a>'),
        help='Specify background colour of contact sheet. Colour is specify in RGBA format.')
    parser.add_argument('--font', nargs=2, default=None, metavar=('<fontfile>', '<size>'),
        help='Specify font of description. Any truetype font are supported.')
    parser.add_argument('--preview', action='count',
        help='Preview the result contact sheet.')
    parser.add_argument('--format', choices=("jpg", "png"), default="jpg",
        help='Picture format of the output file.')
    parser.add_argument('--recursive', action="store_true",
        help='Recurse into subfolders if input is a directory.')
    parser.add_argument('--overwrite', action="store_true",
        help='Overwrite existing images.')
    args = parser.parse_args()

    if args.filename.is_file():
        do(args, args.filename, outfile=args.output, overwrite=args.overwrite)

    elif args.filename.is_dir():
        if args.recursive:
            it = args.filename.rglob("*")
        else:
            it = args.filename.glob("*")

        for path in it:
            if not path.is_file():
                continue

            if path.suffix not in {".mkv", ".mp4", ".avi", ".wmv", ".mpg", ".mov"}:
                print("Skipping non-video file", path)
                continue

            print("Processing", path)

            if args.output is None:
                outpath = None
            else:
                outpath = args.output / path.parent.relative_to(args.filename)
                makedirs(outpath, exist_ok=True)

            try:
                do(args, path, outdir=outpath, overwrite=args.overwrite)
            except FileExistsError as e:
                print(str(e), "already exists")
