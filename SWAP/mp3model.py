"""


"""
import eyed3

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
        self.segment_analyzer.completed_callback = self.segments.set

        #
        #
        #
        self.file_name.add_callback(self._open_file)
        self.file_name.add_callback(self._update_recent_files)

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
        audiofile = eyed3.load(filename)


        if audiofile.tag is None:
            self.album.set("Unknown")
            self.title.set("Unknown")
        else:
            self.album.set(audiofile.tag.album or "Unknown")
            self.title.set(audiofile.tag.title or "Unknown")

        #
        # Get the segments
        #
        self.segment_analyzer.process(filename)


    def set_current_position(self, cp):
        self.current_position.set(cp)
        if len(self.segments.get()) == 0:
            return
        if cp > self.segments.get()[-1:][0]:
            ix = len(self.segments.get()) - 1
        elif cp < self.segments.get()[0]:
            ix = 0
        else:
            ix = next(x for x, val in enumerate(self.segments.get()) if val > cp) - 1
        self.current_segment.set(ix)

    def set_current_segment(self, seg):
        if seg is None:
            self.current_segment.set(0)
            self.current_position.set(0.0)
            return

        self.current_segment.set(seg)
        pos = self.segments.get()[seg]
        self.current_position.set(pos)
