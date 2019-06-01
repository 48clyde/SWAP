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
        self.track_length = Observable(0.0)
        self.album = Observable("")
        self.title = Observable("")
        self.segment_times = Observable([])
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
        self.segment_analyzer.completed_callback = self.segment_times.set

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
        self.segment_times.set([])
        #
        # get the meta data
        #
        audiofile = eyed3.load(filename)
        self.album.set(audiofile.tag.album or "Unknown")
        self.title.set(audiofile.tag.title or "Unknown")
        self.track_length.set(audiofile.info.time_secs)
        #
        # Get the segments
        #
        self.segment_analyzer.process(filename)


    def set_current_pos(self, pos):
        self.current_position.set(pos)
        for ix, s in enumerate(self.segment_times.get()):
            if s > self.current_position.get():
                self.current_segment.set(max(ix - 1, 0))
                break

    def set_current_segment(self, seg):
        if seg is None:
            self.current_segment.set(0)
            self.current_position.set(0.0)
            return

        self.current_segment.set(seg)
        pos = self.segment_times.get()[seg]
        self.current_position.set(pos)
