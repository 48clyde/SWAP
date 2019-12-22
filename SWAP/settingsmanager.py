"""
Manage the settings, such as the list of recently opened media files

"""

import os
import configparser
from SWAP.player import PlayerState

class SettingsManager:

    MAX_RECENT_FILES = 20
    _RECENTS = "recents"
    _SETTINGS = "settings"

    _config = configparser.ConfigParser()
    _config_file = os.path.join(os.path.expanduser("~"), '.swaplayer')


    @staticmethod
    def save(model):
        if os.path.exists(SettingsManager._config_file) and not os.access(SettingsManager._config_file, os.W_OK):
            return

        #
        # Recent files
        #
        if SettingsManager._RECENTS not in SettingsManager._config:
            SettingsManager._config[SettingsManager._RECENTS] = {}
        else:
            SettingsManager._config[SettingsManager._RECENTS].clear()

        for i, r in enumerate(model.recent_files.get()):
            SettingsManager._config[SettingsManager._RECENTS]['file.{}.name'.format(i)] = r

        #
        # State related settings
        #
        if SettingsManager._SETTINGS not in SettingsManager._config:
            SettingsManager._config[SettingsManager._SETTINGS] = {}
        else:
            SettingsManager._config[SettingsManager._SETTINGS].clear()

        SettingsManager._config[SettingsManager._SETTINGS]['player.volume'] = "{}".format(model.volume.get())
        SettingsManager._config[SettingsManager._SETTINGS]['player.gap_analysis'] = model.gap_analysis.get()
        SettingsManager._config[SettingsManager._SETTINGS]['player.position'] = "{}".format(model.current_position.get())

        with open(SettingsManager._config_file, 'w') as cf:
            SettingsManager._config.write(cf)


    @staticmethod
    def load(model):
        if not os.path.exists(SettingsManager._config_file) or not os.access(SettingsManager._config_file, os.R_OK):
            return
        SettingsManager._config.read(SettingsManager._config_file)
        if SettingsManager._RECENTS in SettingsManager._config:
            recents = []
            for i in range(0, SettingsManager.MAX_RECENT_FILES):
                fnk = 'file.{}.name'.format(i)
                if fnk in SettingsManager._config[SettingsManager._RECENTS]:
                    fn = SettingsManager._config[SettingsManager._RECENTS][fnk]
                    recents.append(fn)
            model.recent_files.set(recents)

        if SettingsManager._SETTINGS in SettingsManager._config:
            if 'player.muted' in SettingsManager._config[SettingsManager._SETTINGS]:
                model.muted.set(SettingsManager._config[SettingsManager._SETTINGS]['player.muted'])

            if 'player.volume' in SettingsManager._config[SettingsManager._SETTINGS]:
                v = float(SettingsManager._config[SettingsManager._SETTINGS]['player.volume'])
                model.volume.set(v)

            if 'player.gap_analysis' in SettingsManager._config[SettingsManager._SETTINGS]:
                model.gap_analysis.set(SettingsManager._config[SettingsManager._SETTINGS]['player.gap_analysis'])

            if 'player.position' in SettingsManager._config[SettingsManager._SETTINGS]:
                p = float(SettingsManager._config[SettingsManager._SETTINGS]['player.position'])
                model.current_position.set(p)
