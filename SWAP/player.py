""" Extensions to mpg123

A MP3 Player based on mpg123 with added extensions required for manipulating
the current position and supporting the pausing and resumption of playback that
are not exposed or wrapped by mpg123.py

"""
import ctypes
from enum import Enum
import threading
import queue

import mpg123


class mpg123_frameinfo(ctypes.Structure):
    #
    # https://www.mpg123.de/api/mpg123_8h_source.shtml
    #
    _fields_ = [
        ('version',     ctypes.c_ubyte),
        ('layer',       ctypes.c_int),
        ('rate',        ctypes.c_long),
        ('mode',        ctypes.c_ubyte),
        ('mode_ext',    ctypes.c_int),
        ('framesize',   ctypes.c_int),
        ('flags',       ctypes.c_ubyte),
        ('emphasis',    ctypes.c_int),
        ('bitrate',     ctypes.c_int),
        ('abr_rate',    ctypes.c_int),
        ('vbr',         ctypes.c_ubyte)
    ]


#
# Extensions to Mpg123 to get access to positioning functions
#
class ExtMpg123(mpg123.Mpg123):
    SEEK_SET = 0
    SEEK_CURRENT = 1
    SEEK_END = 2

    def __init__(self, filename=None, library_path=None):
        try:
            super().__init__(filename, library_path)
        except ExtMpg123.LibInitializationException:
            super().__init__(filename, "/opt/local/lib/libmpg123.dylib")

    #
    # Open a mp3 media file
    #
    # https://www.mpg123.de/api/group__mpg123__input.shtml#ga8f74d35cf61667a791b507c76c22a29b
    #
    def open(self, filename):
        errcode = self._lib.mpg123_open(self.handle, filename.encode())
        if errcode != mpg123.OK:
            raise self.OpenFileException(self.plain_strerror(errcode))

    #
    # Get the frame at the specified time offset
    #
    # https://www.mpg123.de/api/group__mpg123__seek.shtml#gab6c3b85832ef3de29aafdb0ef790043b
    #
    def timeframe(self, tsec):
        t = ctypes.c_double(tsec)
        errcode = self._lib.mpg123_timeframe(self.handle, t)
        if errcode >= mpg123.OK:
            return errcode
        else:
            raise self.LengthException(self.plain_strerror(errcode))

    #
    # Seek a specific frame
    #
    # https://www.mpg123.de/api/group__mpg123__seek.shtml#gada9748c253215a8669eab327dd00d447
    #
    def seek_frame(self, pos, whence=SEEK_SET):
        px = ctypes.c_long(pos)
        errcode = self._lib.mpg123_seek_frame(self.handle, px, whence)
        if errcode >= mpg123.OK:
            return errcode
        else:
            raise self.LengthException(self.plain_strerror(errcode))

    #
    # Get the current frame number
    #
    # https://www.mpg123.de/api/group__mpg123__seek.shtml#gaab81ee3527294d01e2c10a10e91022ee
    #
    def tellframe(self):
        errcode = self._lib.mpg123_tellframe(self.handle)
        if errcode >= mpg123.OK:
            return errcode
        else:
            raise self.LengthException(self.plain_strerror(errcode))

    #
    # Get frame information about the MPEG audio bitstream
    #
    # https://www.mpg123.de/api/group__mpg123__status.shtml#ga2f3357b968c78a77ad456a3200820ba8
    #
    def info(self):
        px = mpg123_frameinfo()
        errcode = self._lib.mpg123_info(self.handle, ctypes.pointer(px))
        if errcode != mpg123.OK:
            raise self.ID3Exception(self.plain_strerror(errcode))
        return px

    #
    # Convert a frame number into seconds
    #
    # https://stackoverflow.com/questions/6220660/calculating-the-length-of-mp3-frames-in-milliseconds
    _samples_per_frame = [
        # version 1, layers 1,2,3
        [384, 1152, 1152],
        # version 2, layers 1,2,3
        [384, 1152, 576],
        # version 2.5, layers 1,2,3
        [384, 1152, 576]
    ]

    def frame_seconds(self, frame):
        info = self.info()
        return ExtMpg123._samples_per_frame[info.version][info.layer - 1] * frame / info.rate

    #
    # Get the current volume
    #
    # https://www.mpg123.de/api/group__mpg123__voleq.shtml#ga33be27860acfd34d5d2a1d17cf72a15a
    #
    def get_volume(self):
        base = ctypes.c_double()
        really = ctypes.c_double()
        rva_db = ctypes.c_double()

        errcode = self._lib.mpg123_getvolume(
                self.handle,
                ctypes.pointer(base),
                ctypes.pointer(really),
                ctypes.pointer(rva_db))
        if errcode != mpg123.OK:
            raise self.ID3Exception(self.plain_strerror(errcode))
        return base.value, really.value, rva_db.value

    #
    # Set the current volume
    #
    # https://www.mpg123.de/api/group__mpg123__voleq.shtml#gad3cf821056ba53d4a9caca2671485dc4
    #
    def set_volume(self, volume):
        vol = ctypes.c_double(volume)
        errcode = self._lib.mpg123_volume(self.handle, vol)
        if errcode != mpg123.OK:
            raise self.ID3Exception(self.plain_strerror(errcode))


#
# Add the required functions to Out123 to pause and resume the output
#
class ExtOut123(mpg123.Out123):
    def __init__(self, library_path=None):
        try:
            super().__init__(library_path)
        except mpg123.Out123.LibInitializationException:
            super().__init__("/opt/local/lib/libout123.dylib")

    #
    # Pause the current output
    #
    # https: // www.mpg123.de / api / group__out123__api.shtml  # gae62f06fb987ee2c108a9373a9cde76e7
    #
    def pause(self):
        self._lib.out123_pause(self.handle)

    #
    # Resume the output
    #
    # https://www.mpg123.de/api/group__out123__api.shtml#ga527fd0f94d08b354d0da70daaf170d1e
    def resume(self):
        self._lib.out123_continue(self.handle)


#
# Events generated by the player
#
class PlayerState(Enum):
    UNINITALISED = 0
    INITALISED = 1,  # Drivers loaded
    LOADED = 2,  # MP3 loaded of x seconds
    READY = 3,  # Ready to play a time x
    PLAYING = 4,  # Playing a file at time x
    PAUSED = 5,  # Paused at time x
    FINISHED = 6  # Finished


#
# A wrapper around mpg123 to handle the playback of files in a background thread
#
class Player:

    #
    # Commands that are sent to mpg123 to effect the required states
    #
    class Command(Enum):
        LOAD = 1,
        PLAY = 2,
        PAUSE = 3,
        SEEK = 5

    class IllegalStateException(Exception):
        pass

    def __init__(self):
        self.mp3 = ExtMpg123()
        self.out = ExtOut123()

        #
        # A queue that only allows one item that is used to pass commands
        # to the thread managing mpg123
        #
        self.command_queue = queue.Queue(maxsize=1)
        self.event_queue = queue.Queue()

        self._current_state = PlayerState.INITALISED
        self.event_queue.put((self._current_state, None))
        threading.Thread(target=self._run_player, daemon=True, name="Player").start()

    #
    # The main player run loop, look for commands and process them
    #
    def _run_player(self):
        while True:
            #
            # block until a command becomes available
            #
            command = self.command_queue.get(block=True, timeout=None)
            if command[0] == Player.Command.LOAD:
                if self._current_state in [PlayerState.PLAYING]:
                    self.out.pause()

                self.mp3.open(command[1])
                tf = self.mp3.frame_length()
                self.track_length = self.mp3.frame_seconds(tf)
                self.frames_per_second = tf // self.track_length
                self.update_per_frame_count = round(self.frames_per_second / 5)    # about 5 times a second
                self.to_time = self.track_length
                self._set_state(PlayerState.LOADED, self.track_length)
                self._set_state(PlayerState.READY, 0)

            elif command[0] == Player.Command.PLAY:

                if command[1] is not None:
                    tf = self.mp3.timeframe(command[1])
                    self.mp3.seek_frame(tf)
                self.to_time = self.track_length if command[2] is None else command[2]

                if self._current_state in [PlayerState.READY, PlayerState.PLAYING]:
                    self._play()

                elif self._current_state in [PlayerState.PAUSED]:
                    self.out.resume()
                    self._play()

            elif command[0] == Player.Command.PAUSE:
                self.out.pause()
                current_frame = self.mp3.tellframe()
                current_time = self.mp3.frame_seconds(current_frame)
                self._set_state(PlayerState.PAUSED, current_time)

            elif command[0] == Player.Command.SEEK:
                if self._current_state in \
                            [PlayerState.READY, PlayerState.PLAYING, PlayerState.PAUSED, PlayerState.FINISHED]:

                    tf = self.mp3.timeframe(command[1])
                    self.mp3.seek_frame(tf)
                    if self._current_state == PlayerState.FINISHED:
                        self._set_state(PlayerState.PAUSED, command[1])
                    else:
                        self.event_queue.put((self._current_state, command[1]))

                if self._current_state in [PlayerState.PLAYING]:
                    self._play()

            else:
                # what happened?
                pass

    #
    # The play loop, process the mp3 file, checking for any commands.  If there are any let let _run_player handle it
    #
    def _play(self):
        fc = self.mp3.tellframe()
        current_time = self.mp3.frame_seconds(fc)
        self._set_state(PlayerState.PLAYING, current_time)

        #
        # work out the end frame.  The to time will be in the returned frame so
        # want to stop at before the next one.
        to_frame = self.mp3.timeframe(self.to_time) + 1


        for frame in self.mp3.iter_frames(self.out.start):
            #
            # output the frame
            #
            self.out.play(frame)

            #
            # Check if the end frame has been reached otherwise
            # update the current track time about four times per second
            #
            fc += 1
            if fc > to_frame:
                current_time = self.mp3.frame_seconds(self.mp3.tellframe())
                self._set_state(PlayerState.PAUSED, current_time)
                return

            if fc % self.update_per_frame_count == 0:
                current_time = self.mp3.frame_seconds(self.mp3.tellframe())
                self.event_queue.put((PlayerState.PLAYING, current_time))

            if not self.command_queue.empty():
                return
        #
        # Iterator finished so at the end of the file
        #
        self._set_state(PlayerState.FINISHED)

    #
    # update the player state and put the event in the queue
    #
    def _set_state(self, state, param=None):
        #print ("Setting state {}".format(state))
        self._current_state = state
        self.event_queue.put((state, param))

    ####################################################################################################################
    #
    # Send commands to the player.  These are to be called from other threads such as the GUI/Tkinter runloop thread
    #
    def open(self, filename):
        self.command_queue.put((Player.Command.LOAD, filename))

    def pause(self):
        self.command_queue.put((Player.Command.PAUSE, None))

    def play(self, from_time=None, to_time=None):
        self.command_queue.put((Player.Command.PLAY, from_time, to_time))

    def seek(self, tsec):
        self.command_queue.put((Player.Command.SEEK, tsec))

    #
    # Set/get the volume.
    #
    def get_volume(self):
        return self.mp3.get_volume()

    def set_volume(self, volume):
        self.mp3.set_volume(volume)




if __name__ ==  "__main__":
    import time

    p = Player()

    def monitor():
        while True:
            e = p.event_queue.get(block=True, timeout=None)
            print("{} : {}".format(e[0], e[1]))

    threading.Thread(target=monitor, daemon=True, name="monitor").start()

    p.open("sample.mp3")
    p.seek(60)
    p.play(120, 125)
    time.sleep(10)
    p.play()
    time.sleep(5)

    p.play(None, 145)
    time.sleep(100)