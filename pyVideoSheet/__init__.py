from __future__ import absolute_import, division

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

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    return "{}:{}:{}".format(hours, minutes, seconds)

class Video(object):

    def __init__(self, filename, ffmpeg="ffmpeg"):
        # type: (str, ) -> None

        self.filename = filename
        self.ffmpeg = ffmpeg
        self.filesize = self.get_file_size()
        try:
            example = self.get_frame_at(0)
        except OSError:
            raise RuntimeError("bad video file")

        self.resolution = example.size
        self.mode = example.mode
        self.duration = self.get_video_duration()
        self.thumbnails = [] # type: List[Image]
        self.thumbsize = self.resolution

    def get_file_size(self):
        # type: () -> float

        return os.stat(self.filename).st_size / 1048576.

    def get_video_duration(self):
        # type: () -> int

        p = Popen([self.ffmpeg, "-i", self.filename], stdout=PIPE, stderr=STDOUT)
        pout = p.communicate()
        match = re.search(br"Duration:\s{1}(?P<hours>\d+?):(?P<minutes>\d+?):(?P<seconds>\d+\.\d+?),",
            pout[0], re.DOTALL)
        if not match:
            raise RuntimeError("could extract video duration")

        matches = match.groupdict()
        hours = int(matches['hours'])
        minutes = int(matches['minutes'])
        seconds = int(float(matches['seconds']))
        duration = 3600 * hours + 60 * minutes + seconds

        return duration

    def get_frame_at(self, seektime):
        # type: (int, ) -> Image

        timestring = get_time_string(seektime)
        cmd = [self.ffmpeg, "-ss", timestring, "-i", self.filename, "-f", "image2", "-frames:v",
            "1", "-c:v", "png", "-loglevel", "8", "-"]
        print(" ".join(cmd))
        p = Popen(cmd, stdout=PIPE)
        pout = p.communicate()
        assert pout[0]
        return Image.open(BytesIO(pout[0]))

    def make_thumbnails(self, interval):
        # type: (int, ) -> List[Image]

        total_thumbs = self.duration // interval
        thumbs_list = []
        seektime = 0
        for _ in range(0, total_thumbs):
            seektime += interval
            try:
                img = self.get_frame_at(seektime)
                thumbs_list.append(img)
            except OSError:
                pass

        self.thumbnails = thumbs_list

        return thumbs_list

    def shrink_thumbs(self, maxsize):
        # type: (Tuple[int, int], ) -> Optional[List[Image]]

        if not self.thumbnails:
            return None

        for thumbnail in self.thumbnails:
            thumbnail.thumbnail(maxsize)
        self.thumbsize = self.thumbnails[0].size

        return self.thumbnails

class Sheet(object):

    def __init__(self, video):
        # type: (Video, ) -> None

        fontfile = pkg_resources.resource_stream('pyVideoSheet', 'data/Cabin-Regular-TTF.ttf')
        self.font = ImageFont.truetype(fontfile, 15)
        self.background_colour = (0, 0, 0, 0)
        self.text_colour = (255, 255, 255, 0)
        self.header_size = 100
        self.grid_column = 5
        self.max_thumb_size = (220, 220)
        self.timestamp = True
        self.vid_interval = None # type: Optional[int]
        self.grid = None
        self.header = None
        self.sheet = None

        self.video = video

    def set_property(self, prop, value):
        # type: (str, Any) -> None

        if prop == 'font':
            self.font = ImageFont.truetype(value[0], value[1])
        elif prop == 'background_colour':
            self.background_colour = value
        elif prop == 'text_colour':
            self.text_colour = value
        elif prop == 'header_size':
            self.header_size = value
        elif prop == 'grid_column':
            self.grid_column = value
        elif prop == 'max_thumb_size':
            self.max_thumb_size = value
        elif prop == 'timestamp':
            self.timestamp = value
        else:
            raise Exception('Invalid Sheet property')

    def make_grid(self):
        # type: () -> Image

        if not self.vid_interval:
            raise RuntimeError("make_grid called before setup")

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
                    seektime += self.vid_interval
                    ts = get_time_string(seektime)
                    d.text((width * i, height * j), ts, font=self.font, fill=self.text_colour)
        self.grid = grid
        return grid

    def make_header(self):
        # type: () -> Image

        width = self.video.resolution[0]
        height = self.video.resolution[1]
        duration = self.video.duration
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        timestring = "{:4n}:{:2n}:{:2n}".format(hours, minutes, seconds)

        if not self.grid:
            raise RuntimeError("called make_header before setup")

        header = Image.new(self.grid.mode, (self.grid.width, self.header_size), self.background_colour)
        d = ImageDraw.Draw(header)

        d.text((10, 10), "File Name: {}".format(os.path.basename(self.video.filename)),
            font=self.font, fill=self.text_colour)
        d.text((10, 30), "File Size: {:10.6f} MB".format(self.video.filesize),
            font=self.font, fill=self.text_colour)
        d.text((10, 50), "Resolution: {}x{}".format(width, height),
            font=self.font, fill=self.text_colour)
        d.text((10, 70), "Duration: {}".format(timestring),
            font=self.font, fill=self.text_colour)

        self.header = header
        return header

    def make_sheet_by_interval(self, interval):
        # type: (int, ) -> Image

        self.vid_interval = interval
        self.video.make_thumbnails(interval)
        self.video.shrink_thumbs(self.max_thumb_size)
        self.make_grid()
        self.make_header()
        self.sheet = Image.new(self.grid.mode, (self.grid.width, self.grid.height + self.header.height))
        self.sheet.paste(self.header, (0, 0))
        self.sheet.paste(self.grid, (0, self.header.height))

        return self.sheet

    def make_sheet_by_number(self, num_of_thumbs):
        # type: (int, ) -> Image

        interval = self.video.duration // num_of_thumbs
        self.vid_interval = interval

        return self.make_sheet_by_interval(interval)
