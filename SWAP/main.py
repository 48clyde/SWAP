import os
import sys
import tkinter as tk
from SWAP.playercontroller import PlayerController



####################################################################################################################
#
#
#
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x300")
    app = PlayerController(root)

    #
    # if there is a file specified on the CL, load it up, otherwise load up the most recent
    #
    if len(sys.argv) > 1:
        f = sys.argv[1]
        if os.path.exists(f) and os.access(f, os.R_OK):
            app.open_file(f)
    elif len(app.model.recent_files.get()) > 0:
        f = app.model.recent_files.get()[0]
        if not app.open_file(f):
            app.menu_open_file()
    else:
        app.menu_open_file()

    root.mainloop()

