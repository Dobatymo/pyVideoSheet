from __future__ import absolute_import, division, print_function

import re, os
from subprocess import Popen, PIPE, STDOUT
from io import BytesIO
from typing import TYPE_CHECKING

import pkg_resources
from PIL import Image, ImageDraw, ImageFont

if TYPE_CHECKING:
    from typing import Any, Optional, List, Tuple

def get_time_string(seconds):
    # type: (int, ) -> str

    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    return "{:02}:{:02}:{:02}".format(hours, minutes, seconds)

def get_file_size_mb(filename):
    # type: (str, ) -> float

    return os.stat(filename).st_size / 1024**2

class InvalidVideoFile(Exception):
    pass

class Video(object):

    def __init__(self, filename, ffmpeg="ffmpeg"):
        # type: (str, str) -> None

        self.filename = filename
        self.ffmpeg = ffmpeg
        self.filesize = get_file_size_mb(filename)
        try:
            example = self.get_frame_at(0)
        except OSError:
            raise RuntimeError("bad video file")

        self.resolution = example.size
        self.mode = example.mode
        self.duration = self.get_video_duration()
        self.thumbnails = [] # type: List[Image]
        self.thumbsize = self.resolution

    def get_video_duration(self):
        # type: () -> int

        cmd = [self.ffmpeg, "-i", self.filename]
        p = Popen(cmd, stdout=PIPE, stderr=STDOUT)
        pout = p.communicate()
        match = re.search(br"Duration:\s{1}(?P<hours>\d+?):(?P<minutes>\d+?):(?P<seconds>\d+\.\d+?),",
            pout[0], re.DOTALL)
        if not match:
            raise RuntimeError("could extract video duration")

        matches = match.groupdict()
        hours = int(matches["hours"])
        minutes = int(matches["minutes"])
        seconds = int(float(matches["seconds"]))
        duration = 3600 * hours + 60 * minutes + seconds

        return duration

    def get_frame_at(self, seektime):
        # type: (int, ) -> Image

        timestring = get_time_string(seektime)
        cmd = [self.ffmpeg, "-ss", timestring, "-i", self.filename, "-f", "image2", "-frames:v",
            "1", "-c:v", "png", "-loglevel", "8", "-"]
        p = Popen(cmd, stdout=PIPE)
        pout = p.communicate()
        if not pout[0]:
            raise InvalidVideoFile(" ".join(cmd))

        return Image.open(BytesIO(pout[0]))

    def make_thumbnails(self, interval):
        # type: (int, ) -> None

        thumbs_list = []
        for seektime in range(0, self.duration, interval):
            img = self.get_frame_at(seektime)
            thumbs_list.append(img)

        self.thumbnails = thumbs_list

    def shrink_thumbs(self, maxsize):
        # type: (Tuple[int, int], ) -> None

        if not self.thumbnails:
            return

        for thumbnail in self.thumbnails:
            thumbnail.thumbnail(maxsize)

        self.thumbsize = self.thumbnails[0].size

class Sheet(object):

    def __init__(self, video, columns=5, timestamp=True, background_colour=(0, 0, 0, 0),
        text_colour=(255, 255, 255, 0), max_thumb_size=(220, 220)
    ):
        # type: (Video, int, bool) -> None

        self.video = video
        self.grid_column = columns
        self.timestamp = timestamp
        self.background_colour = background_colour
        self.text_colour = text_colour
        self.max_thumb_size = max_thumb_size

        self.header_size = 100

        fontfile = pkg_resources.resource_stream("pyVideoSheet", "data/Cabin-Regular-TTF.ttf")
        self.font = ImageFont.truetype(fontfile, 15)
        self.vid_interval = None # type: Optional[int]

    def set_property(self, prop, value):
        # type: (str, Any) -> None

        if prop == "font":
            self.font = ImageFont.truetype(value[0], value[1])
        elif prop == "header_size":
            self.header_size = value
        else:
            raise Exception("Invalid Sheet property")

    def make_grid(self, interval):
        # type: (int, ) -> Image

        column = self.grid_column
        thumbcount = len(self.video.thumbnails)
        row = thumbcount // column
        if (thumbcount % column) > 0:
            row += 1
        width = self.video.thumbsize[0]
        height = self.video.thumbsize[1]
        grid = Image.new(self.video.mode, (width * column, height * row))
        d = ImageDraw.Draw(grid)
        seektime = 0
        for j in range(0, row):
            for i in range(0, column):
                if j*column + i >= thumbcount:
                    break
                grid.paste(self.video.thumbnails[j * column + i], (width * i, height * j))
                if self.timestamp is True:
                    ts = get_time_string(seektime)
                    d.text((width * i, height * j), ts, font=self.font, fill=self.text_colour)
                    seektime += interval

        return grid

    def make_header(self, mode, width):
        # type: () -> Image

        width = self.video.resolution[0]
        height = self.video.resolution[1]
        timestring = get_time_string(self.video.duration)

        header = Image.new(mode, (width, self.header_size), self.background_colour)
        d = ImageDraw.Draw(header)

        d.text((10, 10), "File Name: {}".format(os.path.basename(self.video.filename)),
            font=self.font, fill=self.text_colour)
        d.text((10, 30), "File Size: {:10.6f} MB".format(self.video.filesize),
            font=self.font, fill=self.text_colour)
        d.text((10, 50), "Resolution: {}x{}".format(width, height),
            font=self.font, fill=self.text_colour)
        d.text((10, 70), "Duration: {}".format(timestring),
            font=self.font, fill=self.text_colour)

        return header

    def make_sheet_by_interval(self, interval):
        # type: (int, ) -> Image

        self.video.make_thumbnails(interval)
        self.video.shrink_thumbs(self.max_thumb_size)
        grid = self.make_grid(interval)
        header = self.make_header(grid.mode, grid.width)
        sheet = Image.new(grid.mode, (grid.width, grid.height + header.height))
        sheet.paste(header, (0, 0))
        sheet.paste(grid, (0, header.height))

        return sheet

    def make_sheet_by_number(self, num_of_thumbs):
        # type: (int, ) -> Image

        interval = self.video.duration // (num_of_thumbs - 1)

        return self.make_sheet_by_interval(interval)
