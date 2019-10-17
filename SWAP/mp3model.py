"""


"""
import eyed3
import os
from SWAP.segmentsanalyzer import SegmentsAnalyzer
from SWAP.observable import Observable
from SWAP.player import PlayerState


class MediaModel:

    def __init__(self):
        #
        # Items relating to the file
        #
        self.file_name = Observable("")
        self.album = Observable("")
        self.title = Observable("")
        self.segments = Observable([])
        self.track_length = Observable(0.0)

        self.load_progress = Observable(0)

        #
        # Playing the file
        #
        self.current_position = Observable(0.0)
        self.current_segment = Observable(0)
        self.player_state = Observable(PlayerState.UNINITALISED)
        self.muted = Observable(False)
        self.volume = Observable(0)

        #
        # Recent files
        #
        self.recent_files = Observable([])

        #
        #
        #
        self.segment_analyzer = SegmentsAnalyzer()
        self.segment_analyzer.progress_callback = self.load_progress.set
        self.segment_analyzer.completed_callback = self._set_segments

        #
        #
        #
        self.file_name.add_callback(self._open_file)
        self.file_name.add_callback(self._update_recent_files)
        self.player_state.add_callback(self._state_changed)

    #
    # Callback handler on file_name for updating recents
    #
    def _update_recent_files(self, nf):
        rf = self.recent_files.get()
        if len(rf) > 0 and rf[0] == nf:
            # already the first item
            return

        if nf in rf:
            rf.remove(nf)
        rf = [nf] + rf
        self.recent_files.set(rf)

    #
    # Get the meta-data from the file
    #
    def _open_file(self, filename):
        #
        # clear out the current values..
        #
        self.track_length.set(0.0)
        self.current_position.set(0.0)
        self.segments.set([])
        #
        # get the meta data
        #
        if not filename or filename is "" or not os.path.exists(filename) or not os.access(filename, os.R_OK):
            self.album.set("Unknown")
            self.title.set("Unknown")
            return

        audiofile = eyed3.load(filename)

        if audiofile.tag is None:
            self.album.set("Unknown")
            self.title.set("Unknown")
        else:
            self.album.set(audiofile.tag.album or "Unknown")
            if audiofile.tag.track_num[0]:
                self.title.set("{} : {}".format(audiofile.tag.track_num[0], audiofile.tag.title or "Unknown"))
            else:
                self.title.set(audiofile.tag.title or "Unknown")


        #
        # Get the segments
        #
        self.segment_analyzer.process(filename)


    def _state_changed(self, state):
        # print("Player State    {}".format(state))
        return


    def set_current_position(self, cp):
        self.current_position.set(cp)
        #
        # Work out what the current segment is, if segments are loaded
        #
        if len(self.segments.get()) == 0:
            return

        if cp > self.segments.get()[-1:][0]:
            # cp is beyond the last segment
            ix = len(self.segments.get()) - 1
        elif cp <= self.segments.get()[0]:
            # must be the first segment
            ix = 0
        else:
            for ix in range(len(self.segments.get()) - 1, -1, -1):
                s = self.segments.get()[ix]
                if s <= cp:
                    break

        self.current_segment.set(ix)


    # def set_current_position_by_segment(self, seg):
    #     if seg is None:
    #         self.set_current_position(0.0)
    #     elif 0 <= seg < len(self.segments.get()):
    #         self.set_current_position(self.segments.get()[seg])
    #     else:
    #         self.segments.get()[-1]


    def _set_segments(self, segments):
        self.segments.set(segments)
        self.set_current_position(self.current_position.get())


if __name__ ==  "__main__":

    def mon_current_segment(cs):
        print ("Current Segment {}".format(cs))

    def mon_current_position(cp):
        print ("Current Position {}".format(cp))

    m = MediaModel()
    m.current_segment.add_callback(mon_current_segment)
    m.current_position.add_callback(mon_current_position)

    m.segments.set([0.0, 3.4, 8.2, 11.4, 15.4])
    m.set_current_position(0.0)
    m.set_current_position(1.0)
    m.set_current_position(3.4)
    m.set_current_position(3.4000001)
    m.set_current_position(4.0)
    m.set_current_position(15.4)
    m.set_current_position(30.0)

