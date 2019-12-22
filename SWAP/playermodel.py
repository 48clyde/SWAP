"""


"""

from SWAP.observable import Observable
from SWAP.player import PlayerState


class PlayerModel:

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
        # Segments Analysis
        #
        self.gap_analysis = Observable("standard")


    def clear_file(self):
        self.file_name.set("")
        self.album.set("")
        self.title.set("")
        self.segments.set([])
        self.track_length.set(0.0)
        self.current_position.set(0.0)

    def set_current_position(self, cp):
        self.current_position.set(cp)
        #
        # Work out what the current segment is, if segments are loaded
        #
        if len(self.segments.get()) == 0:
            return
        ix = 0
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

    def set_segments(self, segments):
        self.segments.set(segments)
        self.set_current_position(self.current_position.get())

if __name__ == "__main__":

    def mon_current_segment(cs):
        print("Current Segment {}".format(cs))

    def mon_current_position(cp):
        print("Current Position {}".format(cp))

    m = PlayerModel()
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
