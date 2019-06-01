#
#
#
import os
import sys
from tkinter import filedialog
import tkinter as tk

from SWAP.playerview import PlayerView
from SWAP.mp3model import MediaModel
from SWAP.settingsmanager import SettingsManager
from SWAP.player import Player, PlayerState


class PlayerController:
    def __init__(self, rw):
        self.root = rw
        self.root.protocol('WM_DELETE_WINDOW', self.quit)

        self.view = PlayerView(self.root)

        #
        # Create the media model and bind to the view
        #
        self.model = MediaModel()
        self.model.album.add_callback(self.view.set_album)
        self.model.title.add_callback(self.view.set_title)
        self.model.track_length.add_callback(self.view.set_track_length)
        self.model.current_position.add_callback(self.view.set_current_position)
        self.model.current_position.add_callback(self.player_state_prev_button)
        self.model.current_position.add_callback(self.player_state_repeat_button)
        self.model.current_position.add_callback(self.player_state_next_button)

        self.model.current_segment.add_callback(self.view.set_current_segment)

        self.model.segment_times.add_callback(self.view.set_segments)
        self.model.load_progress.add_callback(self.view.set_load_progress)
        self.model.track_length.add_callback(self.view.set_track_length)
        self.model.volume.add_callback(self.view.set_volume)

        #
        # Bind the controls to commands to process when users click on them
        #
        self.view.prev_interval_button.config(command=self.prev_pressed)
        self.view.repeat_button.config(command=self.repeat_pressed)
        self.view.play_pause_button.config(command=self.play_pause_pressed)
        self.view.next_button.config(command=self.next_pressed)
        self.view.current_position_slider.config(command=self.user_moving_current_position)
        self.view.mute_button.config(command=self.mute_pressed)
        self.view.volume_slider.config(command=self.volume_changed)
        self.view.segment_list.bind('<<ListboxSelect>>', self.interval_selected_event)

        #
        # bind the menus for when the user selects something
        #
        self.view.menu_callback = self.menu_callback
        self.view.menu_recents_callback = self.menu_recent_selected

        #
        # Load the settings, i.e. recents
        #
        self.model.recent_files.add_callback(self.view.set_menu_recents)
        self.settings = SettingsManager(self.model)

        #
        # Create the media player and get the current volume level
        #
        self.player = Player()
        self.model.volume.set(self.player.get_volume()[0])
        self.model.file_name.add_callback(self.player.open)

        #
        # Connect the observers for the buttons
        #
        self.model.player_state.add_callback(self.player_state_prev_button)
        self.model.player_state.add_callback(self.player_state_repeat_button)
        self.model.player_state.add_callback(self.player_state_play_pause_button)
        self.model.player_state.add_callback(self.player_state_next_button)
        self.model.muted.add_callback(self.player_state_muted_button)

        #
        # Bind some shortcut keys
        #
        self.view.master.bind("<Left>", lambda i=-1 : self.prev_pressed(i))
        self.view.master.bind("<Command-Left>", lambda i=-10 : self.prev_pressed(i))
        self.view.master.bind("r", self.repeat_pressed)
        self.view.master.bind("R", self.repeat_pressed)
        self.view.master.bind("<space>", self.play_pause_pressed)
        self.view.master.bind("<Right>", lambda i=1 : self.next_pressed(i))
        self.view.master.bind("<Command-Right>", lambda i=10 :  self.next_pressed(i))

        self.root.after(200, self.process_player_events)

    ####################################################################################################################
    #
    # Check the player for events that need to be reflected in the model
    #
    def process_player_events(self):
        while not self.player.event_queue.empty():
            ev, param = self.player.event_queue.get(block=False)
            self.model.player_state.set(ev)
            #
            # filter by event type...
            #
            if ev in [PlayerState.INITALISED]:
                self.model.track_length.set(0.0)
                self.model.set_current_pos(0.0)

            elif ev in [PlayerState.LOADED]:
                self.model.track_length.set(param)

            elif ev in [PlayerState.READY, PlayerState.PLAYING, PlayerState.PAUSED]:
                self.model.set_current_pos(param)

        self.root.after(200, self.process_player_events)

    ####################################################################################################################
    #
    # Callbacks re: the player state that impact on the buttons
    #
    def player_state_prev_button(self, _x):
        state = self.model.player_state.get()
        if state in [PlayerState.INITALISED, PlayerState.UNINITALISED]:
            self.view.prev_interval_button.config(state=tk.DISABLED, image=self.view.prev_image_disabled)

        elif state in [PlayerState.LOADED, PlayerState.READY, PlayerState.PAUSED, PlayerState.FINISHED]:
            if self.model.current_position.get() > 0:
                self.view.prev_interval_button.config(state=tk.NORMAL, image=self.view.prev_image_normal)
            else:
                self.view.prev_interval_button.config(state=tk.DISABLED, image=self.view.prev_image_disabled)

        elif state in [PlayerState.PLAYING]:
            self.view.prev_interval_button.config(state=tk.NORMAL, image=self.view.prev_image_normal)

    #
    #
    #
    def player_state_repeat_button(self, _x):
        state = self.model.player_state.get()
        if state in [PlayerState.INITALISED, PlayerState.UNINITALISED]:
            self.view.repeat_button.config(state=tk.DISABLED, image=self.view.repeat_image_disabled)

        elif state in [PlayerState.LOADED, PlayerState.READY, PlayerState.PAUSED, PlayerState.FINISHED]:
            if self.model.current_position.get() > 0.0:
                self.view.repeat_button.config(state=tk.NORMAL, image=self.view.repeat_image_normal)
            else:
                self.view.repeat_button.config(state=tk.DISABLED, image=self.view.repeat_image_disabled)

        elif state in [PlayerState.PLAYING]:
            self.view.repeat_button.config(state=tk.NORMAL, image=self.view.repeat_image_normal)

    #
    #
    #
    def player_state_play_pause_button(self,  _x):
        state = self.model.player_state.get()
        if state in [PlayerState.INITALISED, PlayerState.UNINITALISED]:
            self.view.play_pause_button.config(state=tk.DISABLED, image=self.view.play_image_disabled)

        elif state in [PlayerState.LOADED, PlayerState.READY]:
            self.view.play_pause_button.config(state=tk.NORMAL, image=self.view.play_image_normal)

        elif state in [PlayerState.PLAYING]:
            self.view.play_pause_button.config(state=tk.NORMAL, image=self.view.pause_image_normal)

        elif state in [PlayerState.PAUSED, PlayerState.FINISHED]:
            self.view.play_pause_button.config(state=tk.NORMAL, image=self.view.play_image_normal)

    #
    #
    #
    def player_state_next_button(self,  _x):
        state = self.model.player_state.get()
        if state in [PlayerState.INITALISED, PlayerState.UNINITALISED]:
            self.view.next_button.config(state=tk.DISABLED, image=self.view.next_image_disabled)

        elif state in [PlayerState.LOADED, PlayerState.READY, PlayerState.PAUSED, PlayerState.FINISHED]:
            if self.model.current_position.get() < self.model.track_length.get():
                self.view.next_button.config(state=tk.NORMAL, image=self.view.next_image_normal)
            else:
                self.view.next_button.config(state=tk.DISABLED, image=self.view.next_image_disabled)

        elif state in [PlayerState.PLAYING]:
            self.view.next_button.config(state=tk.NORMAL, image=self.view.next_image_normal)

    #
    #
    #
    def player_state_muted_button(self, muted):
        if muted:
            self.view.mute_button.config(image=self.view.muted_image)
            self.player.set_volume(0)
        else:
            self.view.mute_button.config(image=self.view.volume_image)
            self.player.set_volume(self.model.volume.get())

    ####################################################################################################################
    #
    # View control interaction handlers
    #
    def prev_pressed(self, event=None, step=-1):
        if event is not None and event.state & 12 > 0:
            step = -10
        cs = self.model.current_segment.get()
        if cs is not None:
            ts = max(cs + step, 0)
            tt = self.model.segment_times.get()[ts]
            self.player.seek(tt)

    #
    #
    #
    def repeat_pressed(self, _event=None):
        cs = self.model.current_segment.get()
        tt = self.model.segment_times.get()[cs]
        self.player.seek(tt)

    #
    #
    #
    def play_pause_pressed(self, _event=None):
        if self.model.player_state.get() == PlayerState.PLAYING:
            self.player.pause()
        else:
            self.player.play()

    #
    #
    #
    def next_pressed(self, event=None, step=1):
        if event is not None and event.state & 12 > 0:
            step = 10
        cs = self.model.current_segment.get()
        if cs is not None:
            ts = min(cs + step, len(self.model.segment_times.get()))
            self.model.set_current_segment(ts)
            tt = self.model.segment_times.get()[ts]
            self.player.seek(tt)

    #
    # The user has moved the slider, so send the seek command to the player to seek to that time.  The player will
    # then create an event with this new position that will be picked up in process_player_events so that
    # the model can be updated
    #
    def user_moving_current_position(self, _p=None):
        pos = self.view.current_position_slider.get()
        self.player.seek(pos)

    #
    # Toggle muted on or off
    #
    def mute_pressed(self):
        self.model.muted.set(not self.model.muted.get())

    #
    # The user has changed the volume
    #
    def volume_changed(self, vol):
        self.player.set_volume(float(vol))

    #
    # The user has selected a specific time interval in the list
    #
    def interval_selected_event(self, event):
        index = event.widget.curselection()[0]
        tt = self.model.segment_times.get()[index]
        self.player.seek(tt)

    ####################################################################################################################
    #
    # Menu action handlers
    #
    def menu_callback(self, menu_item):
        if menu_item == "menuFileOpen":
            self.menu_open_file()

        elif menu_item == "menuFileQuit":
            self.quit()

        elif menu_item == "menuEditCopy":
            if self.model.file_name is not None:
                self.root.clipboard_clear()
                self.root.clipboard_append(self.model.file_name.get())

        elif menu_item == "menuEditPaste":
            self.model.file_name.set(self.root.clipboard_get())

        elif menu_item == "menuRecentClear":
            self.model.recent_files.set([])

        else:
            print("Unhandled menu command '{}'".format(menu_item))

    def menu_open_file(self):
        file_name = filedialog.askopenfilename(
            initialdir=self.settings.get_last_media_directory(),
            title="Select file",
            filetypes=(
                ("MP3 files", "*.mp3"),
                ("all files", "*.*")))
        if file_name and file_name is not "" and os.path.exists(file_name) and os.access(file_name, os.R_OK):
            self.model.file_name.set(file_name)

    def quit(self):
        self.player.pause()
        self.root.destroy()

    def menu_recent_selected(self, recent_ix):
        selected_recent = self.model.recent_files.get()[recent_ix]
        self.model.file_name.set(selected_recent)


####################################################################################################################
#
#
#
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x300")
    app = PlayerController(root)

    #
    # if there is a file specified on the CL, load it up, otherwise load up the most recent if possible?
    #
    if len(sys.argv) > 1:
        f = sys.argv[1]
        if os.path.exists(f) and os.access(f, os.R_OK):
            app.model.file_name.set(f)
    elif len(app.model.recent_files.get()) > 0:
        f = app.model.recent_files.get()[0]
        app.model.file_name.set(f)
    else:
        app.menu_open_file()

    # if there is a file specified on the CL, try and open it and start playing?
    root.mainloop()
