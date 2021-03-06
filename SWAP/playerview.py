import tkinter as tk
from tkinter.ttk import Progressbar
import os.path
import sys


def resource_path(resource):
    frozen = 'not'
    if getattr(sys, 'frozen', False):
        # we are running in a bundle
        frozen = 'ever so'
        bundle_dir = sys._MEIPASS
    else:
        # we are running in a normal Python environment
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(bundle_dir, resource)


#
# Create the player window - do all the stuff to create the required widgets
# for the application
#
class PlayerView(tk.Frame):

    #
    #
    #
    def __init__(self, root=None):
        tk.Frame.__init__(self, root)
        self.master.minsize(400, 300)
        self.master.title("Spoken Word Audio Player")

        ################################################################################################################
        #
        # Variables for binding UI elements to the model.  Since these aren't hashable they can't be used
        # in lambda expressions so need various set_* funcitons
        #
        self._album = tk.StringVar("")
        self._title = tk.StringVar("")
        self._elapsed_time = tk.StringVar("")
        self._remaining_time = tk.StringVar("")
        self._track_length = 0.0
        self._load_progress = tk.IntVar(0)
        self._current_position = tk.DoubleVar(0.0)
        self._volume = tk.DoubleVar(0.0)
        self._segments = tk.StringVar([])

        ################################################################################################################
        #
        # The menus
        #
        self.main_menu = tk.Menu(root)
        root.config(menu=self.main_menu)

        self.file_menu = tk.Menu(self.main_menu)
        self.main_menu.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(
            label="Open", accelerator="Command+O",
            command=lambda i="menuFileOpen": self._menu_callback(i))
        self.menu_recents = tk.Menu(self.file_menu)
        self.menu_recents.add_separator()
        self.menu_recents.add_command(
            label="Clear", state=tk.DISABLED,
            command=lambda i="menuRecentClear": self._menu_callback(i))
        self.file_menu.add_cascade(label="Open recent", menu=self.menu_recents)
        self.file_menu.add_separator()

        self.file_menu.add_command(
            label="Quit", accelerator="Command+Q",
            command=lambda i="menuFileQuit": self._menu_callback(i))

        edit_menu = tk.Menu(self.main_menu)
        self.main_menu.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", state=tk.DISABLED, accelerator="Command+Z")
        edit_menu.add_command(label="Redo", state=tk.DISABLED, accelerator="Shift+Command+Z")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", state=tk.DISABLED, accelerator="Command+X")

        edit_menu.add_command(
            label="Copy", accelerator="Command+C", state=tk.NORMAL,
            command=lambda i="menuEditCopy": self._menu_callback(i))
        edit_menu.add_command(
            label="Paste", accelerator="Command+V",
            command=lambda i="menuEditPaste": self._menu_callback(i))

        analysis_menu = tk.Menu(self.main_menu)
        self.main_menu.add_cascade(label="Speech Gap Analysis", menu=analysis_menu)

        self.gap_analysis = tk.StringVar()
        self.gap_analysis.set('standard')
        analysis_menu.add_radiobutton(label="Short", command=lambda i="menuAnalysisShort": self._menu_callback(i), variable=self.gap_analysis, value='short')
        analysis_menu.add_radiobutton(label="Standard", command=lambda i="menuAnalysisStandard": self._menu_callback(i), variable=self.gap_analysis, value='standard')
        analysis_menu.add_radiobutton(label="Long", command=lambda i="menuAnalysisLong": self._menu_callback(i), variable=self.gap_analysis, value='long')

        # The menu callback methods for the controller
        #
        self.menu_callback = None
        self.menu_recents_callback = None

        ################################################################################################################
        #
        # Main GUI
        #

        #
        # Put the loading file progress bar across the bottom of the screen
        #
        self.loading_progress_bar = Progressbar(
                self.master, orient=tk.HORIZONTAL, length=100,
                mode='determinate', variable=self._load_progress
                )
        self.loading_progress_bar.pack(side=tk.BOTTOM, anchor=tk.S, fill=tk.X)

        #
        # Segments list goes on the right side
        #
        self.segment_list = tk.Listbox(
                self.master,
                listvariable=self._segments,
                width=10,
                justify=tk.CENTER,
                activestyle=tk.NONE)
        self.segment_list.pack(side=tk.RIGHT, fill=tk.Y)

        #
        # Left frame for the title, controls etc.
        #
        left_frame = tk.Frame(self.master)
        left_frame.pack(side=tk.TOP, expand=1, fill=tk.BOTH)

        #
        # info_frame
        #
        info_frame = tk.Frame(left_frame)
        info_frame.pack(side=tk.TOP, anchor=tk.CENTER, fill=tk.X)
        self._album_label = tk.Label(info_frame, textvariable=self._album, pady=15, font="-size 16")
        self._album_label.pack(side=tk.TOP, fill=tk.X)
        self._title_label = tk.Label(info_frame, textvariable=self._title, pady=10)
        self._title_label.pack(side=tk.TOP, fill=tk.X)

        #
        # position_frame
        #
        position_frame = tk.Frame(left_frame)
        position_frame.pack(side=tk.TOP, fill=tk.X)
        self.elapsed_time_label = tk.Label(position_frame, textvariable=self._elapsed_time, width=5)
        self.elapsed_time_label.pack(side=tk.LEFT)
        self.current_position_slider = tk.Scale(
                position_frame, from_=0, to=10,
                orient=tk.HORIZONTAL, showvalue=tk.FALSE,
                sliderlength=10,
                variable=self._current_position)
        self.current_position_slider.pack(side=tk.LEFT, fill=tk.X, expand=1, anchor=tk.CENTER)
        self.remaining_time_label = tk.Label(position_frame, textvariable=self._remaining_time, width=5)
        self.remaining_time_label.pack(side=tk.LEFT)

        #
        # volume_frame
        #
        volume_frame = tk.Frame(left_frame)
        volume_frame.pack(side=tk.BOTTOM, anchor=tk.W)
        self.volume_image = tk.PhotoImage(file=resource_path('images/volume_NORMAL.png'))
        self.muted_image = tk.PhotoImage(file=resource_path('images/mute_NORMAL.png'))

        self.mute_button = tk.Button(volume_frame, image=self.volume_image, bd=10)
        self.mute_button.pack(side=tk.LEFT, anchor=tk.W)
        self.volume_slider = tk.Scale(
                volume_frame, from_=0, to=1, resolution=0.1,
                variable=self._volume,
                orient=tk.HORIZONTAL,
                showvalue=tk.FALSE)
        self.volume_slider.pack(side=tk.LEFT, fill=tk.X, expand=1)

        spacer = tk.Label(left_frame)
        spacer.pack(side=tk.BOTTOM)

        #
        # control_frame
        #
        control_group_frame = tk.Frame(left_frame)
        control_group_frame.pack(side=tk.BOTTOM, anchor=tk.CENTER)

        self.prev_image_normal = tk.PhotoImage(file=resource_path('images/prev_NORMAL.png'))
        self.prev_image_disabled = tk.PhotoImage(file=resource_path('images/prev_DISABLED.png'))
        self.prev_interval_button = tk.Button(control_group_frame, image=self.prev_image_disabled)
        self.prev_interval_button.pack(side=tk.LEFT)

        self.repeat_image_normal = tk.PhotoImage(file=resource_path('images/repeat_NORMAL.png'))
        self.repeat_image_disabled = tk.PhotoImage(file=resource_path('images/repeat_DISABLED.png'))
        self.repeat_button = tk.Button(control_group_frame, image=self.repeat_image_normal)
        self.repeat_button.pack(side=tk.LEFT)

        self.play_image_normal = tk.PhotoImage(file=resource_path('images/play_NORMAL.png'))
        self.play_image_disabled = tk.PhotoImage(file=resource_path('images/play_DISABLED.png'))
        self.pause_image_normal = tk.PhotoImage(file=resource_path('images/pause_NORMAL.png'))
        self.pause_image_disabled = tk.PhotoImage(file=resource_path('images/pause_DISABLED.png'))
        self.play_pause_button = tk.Button(control_group_frame, image=self.play_image_normal)
        self.play_pause_button.pack(side=tk.LEFT)

        self.step_image_normal = tk.PhotoImage(file=resource_path('images/step_NORMAL.png'))
        self.step_image_disabled = tk.PhotoImage(file=resource_path('images/step_DISABLED.png'))
        self.step_button = tk.Button(control_group_frame, image=self.step_image_normal)
        self.step_button.pack(side=tk.LEFT)

        self.next_image_normal = tk.PhotoImage(file=resource_path('images/next_NORMAL.png'))
        self.next_image_disabled = tk.PhotoImage(file=resource_path('images/next_DISABLED.png'))
        self.next_button = tk.Button(control_group_frame, image=self.next_image_normal)
        self.next_button.pack(side=tk.LEFT)

    ################################################################################################################
    #
    # callback menu handlers
    #
    def _menu_callback(self, menu_name):
        if self.menu_callback is not None:
            self.menu_callback(menu_name)

    #
    #
    #
    def _recents_menu_selected(self, ix):
        if self.menu_recents_callback is not None:
            self.menu_recents_callback(ix)

    ################################################################################################################
    #
    # setters
    #
    def set_gap_analysis(self, analysis):
        self.gap_analysis.set(analysis)

    #
    #
    #
    def set_album(self, album):
        self._album.set(album)

    #
    #
    #
    def set_title(self, title):
        self._title.set(title)

    #
    # set the track length in seconds
    #
    def set_track_length(self, track_length):
        self._track_length = track_length
        self.current_position_slider.config(to=int(track_length))
        self._elapsed_time.set(PlayerView._display_time(self._current_position.get()))
        self._remaining_time.set(PlayerView._display_time(self._track_length - self._current_position.get()))

    #
    #
    #
    def set_load_progress(self, load_progress):
        self._load_progress.set(load_progress)

    #
    # set the current position indicator in seconds
    #
    def set_current_position(self, position):
        self._current_position.set(position)
        et = PlayerView._display_time(position)
        self._elapsed_time.set(et)
        self._remaining_time.set(PlayerView._display_time(self._track_length - position))

    #
    # set the volume as a float 0.0 - 1.0
    #
    def set_volume(self, volume):
        self._volume.set(volume)

    #
    # Select the specified segment
    #
    def set_current_segment(self, segment_ix):
        if segment_ix is None:
            return

        cs = self.segment_list.curselection()
        if (len(cs) == 0) or (len(cs) > 0 and cs[0] != segment_ix):
            self.segment_list.selection_clear(0, tk.END)
            self.segment_list.selection_set(segment_ix)
            self.segment_list.see(segment_ix)

    #
    #
    #
    def set_segments(self, ss):
        if ss is None or len(ss) == 0:
            self._segments.set([])
            return
        segments = []
        for i in ss:
            segments.append(PlayerView._display_time(i))
        self._segments.set(segments)
        self.segment_list.selection_clear(0, tk.END)
        self.segment_list.selection_set(0)

    ################################################################################################################
    #
    # update the recents menu with the first X most recent files if there are any available.
    #
    def set_menu_recents(self, recents):
        #
        # Remove old recents, i.e. those items from 0 until 1 before the separator
        #
        last = self.menu_recents.index(tk.END)
        seprator_ix = 0
        for i in range(last + 1):
            if self.menu_recents.type(i) == tk.SEPARATOR:
                break
            seprator_ix = i
        if seprator_ix > 0:
            self.menu_recents.delete(0, seprator_ix)

        #
        # Add new/replacement recents
        # https://stackoverflow.com/questions/17677649/tkinter-assign-button-command-in-loop-with-lambda/17677768#17677768
        have_recents = False
        for j, r in enumerate(recents):
            have_recents = True
            self.menu_recents.insert(
                j, label=r, itemType=tk.COMMAND,
                command=lambda k=j: self._recents_menu_selected(k))

        #
        # enable clear if there are some recents
        #
        self.menu_recents.entryconfig("Clear", state=tk.NORMAL if have_recents else tk.DISABLED)

    #
    #
    #
    def set_menu_edit_copy_state(self, state):
        self.main_menu.entryconfig("Copy", state=state)

    ################################################################################################################
    #
    # Format a number of seconds as (hh:)mm:ss
    #
    @staticmethod
    def _display_time(seconds):
        """
        Format an amount of seconds as (hh:)mm:ss
        """
        seconds = int(seconds)
        h = seconds // 3600
        seconds -= (3600 * h)
        m = seconds // 60
        seconds -= (60 * m)
        if h > 0:
            return "{:02d}:{:02d}:{:02d}".format(h, m, seconds)
        else:
            return "{:02d}:{:02d}".format(m, seconds)


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x300")
    app = PlayerView(root)
    app.set_album("French for the Traveller")
    app.set_title("Outdoor Activities")
    app.set_track_length(543)
    app.prev_interval_button.config(state=tk.NORMAL, image=app.prev_image_normal)
    app.set_volume(0.9)
    app.set_menu_recents(
        [
            "media/fishermanandhisoul_01_wilde_128kb.mp3",
            "media/fables_01_00_aesop_64kb.mp3",
            "media/fables_01_01_aesop_64kb.mp3"
        ])

    s = [
        0, 5, 13, 26, 29, 36, 50, 57, 67, 75, 78, 83, 87, 92,
        95, 108, 116, 129, 143, 158, 166, 172, 184, 187, 197,
        212, 224, 235, 240, 251, 256, 269, 275, 277, 292]
    app.set_segments(s)
    app.set_current_segment(4)
    app.set_current_position(s[4])
    root.mainloop()
