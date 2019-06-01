"""
Manage the settings, such as the list of recently opened media files

"""

import os
import configparser


class SettingsManager:

    MAX_RECENT_FILES = 20
    _RECENTS = "recents"
    _SETTINGS = "settings"

    def __init__(self, model):
        self._config_file = os.path.join(os.path.expanduser("~"), '.swaplayer')
        self._config = configparser.ConfigParser()
        self.model = model
        self._load()
        self.model.recent_files.add_callback(self.recents_changed)

    #
    # Load the current settings
    #
    def _load(self):
        if not os.path.exists(self._config_file) or not os.access(self._config_file, os.R_OK):
            return
        self._config.read(self._config_file)
        if SettingsManager._RECENTS not in self._config:
            # a new file with no recents
            self._config[SettingsManager._RECENTS] = {}
        recents = []
        for i in range(0, SettingsManager.MAX_RECENT_FILES):
            fnk = 'file.{}.name'.format(i)
            if fnk in self._config[SettingsManager._RECENTS]:
                fn = self._config[SettingsManager._RECENTS][fnk]
                recents.append(fn)
        self.model.recent_files.set(recents)

    #
    # The file name in the model has changed, so need to update the recents and
    # save the settings file
    #
    def recents_changed(self, _):
        self.save()

    #
    # Save the current config
    # On app shutdown, this should be called to write out the current config
    #
    def save(self):
        if os.path.exists(self._config_file) and not os.access(self._config_file, os.W_OK):
            return

        if SettingsManager._RECENTS not in self._config:
            self._config[SettingsManager._RECENTS] = {}
        else:
            self._config[SettingsManager._RECENTS].clear()

        for i, r in enumerate(self.model.recent_files.get()):
            self._config[SettingsManager._RECENTS]['file.{}.name'.format(i)] = r
        with open(self._config_file, 'w') as cf:
            self._config.write(cf)

    #
    # Get the directory from where the last file was opened to use as a starting point 
    # for the the File/Open command.
    #
    def get_last_media_directory(self):
        if len(self.model.recent_files.get()) == 0:
            return os.path.join(os.path.expanduser("~"))
        else:
            return os.path.dirname(os.path.realpath(self.model.recent_files.get()[0]))
