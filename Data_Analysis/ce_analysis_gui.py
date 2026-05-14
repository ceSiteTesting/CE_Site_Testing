

################################################################################################################################
#------------------------------------------------------------------------------------------------------------------------------#
                                                                     
             ##                                                        
            ####                ####   ####   #####  #####  #####        ##         ####     
           ######               #   #  #   #  #      #      #            #####      #   #  #   #  ####            
             ##                 ####   ####   ####   #####  #####        ########   ####   #   #  #   #
             ##                 #      #   #  #          #      #        #####      #   #  #   #  #   #
             ##                 #      #   #  #####  #####  #####        ##         #   #   ###   #   #
             ##

#------------------------------------------------------------------------------------------------------------------------------#
################################################################################################################################




################################################################################################################################
################################################################################################################################




'''
Sorry in advanced to whoever is trying to maintain or update this code. I tried to not use magic numbers
and annotate the best I could. 

Good luck and sorry for any potential headache.

- Carlos A. Campos

p.s. 
Yes, I know that I am extra about my commenting/organizing

-----

GUI Version Notes:
    All terminal input() prompts and print() menus have been replaced with
    tkinter widgets. The core analysis logic (csv_upload data processing,
    mseed_upload, get_optional_float defaults, plot_time_series,
    plot_spectrum, plot_spectrogram) is unchanged. Only the UI layer
    (menus, input prompts) has been converted to GUI.

    IMPORTANT - Matplotlib threading rule:
        ALL plt.* calls must run on the main thread.
        Worker threads do the heavy computation, then hand results back
        to the main thread via self.after(0, plot_fn).
        Never call plt.show() from a worker thread.
'''

import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import warnings

import obspy
from obspy import UTCDateTime
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("TkAgg")          # must be set before importing pyplot
from matplotlib import pyplot as plt
from scipy import signal
from matplotlib import gridspec
import matplotlib.ticker as mticker




'''##########################################################################################################################'''
'''##########################################################################################################################'''

                             ####  ######  #   #       #####  ###  #      #####  #####
                            #      #       #   #       #       #   #      #      #
                            #      ######  #   #       ###     #   #      ###    #####
                            #           #   # #        #       #   #      #          #
                             ####  ######    #         #      ###  #####  #####  #####
                
'''##########################################################################################################################'''
'''##########################################################################################################################'''



def load_csv_data(file_path, function):
    """
    Pure data-loading logic extracted from the original csv_upload().
    Returns the same tuple as before; raises on error.
    """
    metadata_rows = []
    metadata = {}

    with open(file_path, 'r') as f:
        for _ in range(5):
            metadata_rows.append(f.readline().strip())

    for row in metadata_rows:
        if ':' in row:
            key, value = row.split(':', 1)
            metadata[key.strip()] = value.strip()

    sample_rate = float(metadata["Sample Rate"])

    if function == "mag":
        columns          = ["Sample", "Time (s)", "Noise (V)", "Voltage X (V)", "Voltage Y (V)", "Voltage Z (V)", "blank"]
        calibration      = (1.222e-05) / 21
        ctrl_calibration = (1.222e-05) / 21
        control_file     = 'mag_data.csv'

    elif function == "seis":
        columns          = ["Sample", "Time (s)", "Noise (V)", "Channel E (V)", "Channel N (V)", "Channel Z (V)", "blank"]
        calibration      = (0.0125e-1) / 21
        ctrl_calibration = 0.0076e-6
        control_file     = 'ligo_seis_data.txt'

    else:
        raise ValueError("Unknown function: " + str(function))

    data         = pd.read_csv(file_path, skiprows=6, delimiter=',')
    data.columns = columns

    time   = data[columns[1]]
    x_axis = data[columns[3]] * calibration
    y_axis = data[columns[4]] * calibration
    z_axis = data[columns[5]] * calibration

    script_dir        = os.getcwd()
    control_data_path = os.path.join(script_dir, control_file)

    if os.path.exists(control_data_path):

        if control_file == 'ligo_seis_data.txt':
            huddle         = pd.read_csv(control_data_path, delimiter=r"\s+", engine='python')
            huddle.columns = ["frequency", "x", "y", "z"]
            ctrl_freq      = huddle["frequency"]
            ctrl_x         = huddle["x"] * ctrl_calibration
            ctrl_y         = huddle["y"] * ctrl_calibration
            ctrl_z         = huddle["z"] * ctrl_calibration
            return sample_rate, time, x_axis, y_axis, z_axis, ctrl_x, ctrl_y, ctrl_z, ctrl_freq

        elif control_file == 'mag_data.csv':
            ligo    = pd.read_csv(control_data_path, delimiter=",", skiprows=5)
            ctrl_z  = ligo['Voltage Z (V)'][0:647487] * calibration
            ctrl_y  = ligo['Voltage Y (V)'] * calibration
            ctrl_x  = ligo['Voltage X (V)'] * calibration
            ctrl_sr = 5120
            return sample_rate, time, x_axis, y_axis, z_axis, ctrl_x, ctrl_y, ctrl_z, ctrl_sr

    return sample_rate, time, x_axis, y_axis, z_axis, None, None, None, None




'''##########################################################################################################################'''
'''##########################################################################################################################'''

                    #######  #####  #####  #####  ####        #####  ###  #      #####  #####
                    #  #  #  #      #      #      #   #       #       #   #      #      #
                    #  #  #  #####  ###    ###    #   #       ###     #   #      ###    #####
                    #  #  #      #  #      #      #   #       #       #   #      #          #
                    #     #  #####  #####  #####  ####        #      ###  #####  #####  #####

'''##########################################################################################################################'''
'''##########################################################################################################################'''



def load_mseed_data(file_paths, start_time=None, end_time=None):
    """
    Pure data-loading logic extracted from the original mseed_upload().
    """

    def process_multiple_miniseed(fps, st=None, et=None):
        sample_rates_all = []
        times_all        = []
        data_values_all  = []

        for fp in fps:
            stream = obspy.read(fp)
            try:
                stream = stream.trim(starttime=st, endtime=et)
            except Exception:
                pass

            if len(stream) == 0:
                continue

            sample_rates = []
            times        = []
            data_values  = []

            for trace in stream:
                sample_rates.append(trace.stats.sampling_rate)
                times.append(trace.times())
                data_values.append(trace.data)

            sample_rates_all.append(sample_rates)
            times_all.append(times)
            data_values_all.append(data_values)

        sr1, _sr2, _sr3   = sample_rates_all
        times_e, times_n, times_z = times_all
        data_e,  data_n,  data_z  = data_values_all

        return data_e, data_n, data_z, times_e, times_n, times_z, sr1

    data_e, data_n, data_z, times_e, times_n, times_z, sr = process_multiple_miniseed(
        file_paths, st=start_time, et=end_time)

    time_e = times_e[0]
    time_n = times_n[0]
    time_z = times_z[0]

    z_out = data_z[0] * 0.0015e-6
    n_out = data_n[0] * 0.0015e-6
    e_out = data_e[0] * 0.0015e-6

    sr_out = sr[0]

    script_dir        = os.getcwd()
    control_data_path = os.path.join(script_dir, 'ligo_seis_data.txt')

    if os.path.exists(control_data_path):
        huddle         = pd.read_csv(control_data_path, delimiter=r"\s+", engine='python')
        huddle.columns = ["frequency", "x", "y", "z"]
        hf = huddle["frequency"]
        hx = huddle["x"] * 0.0076e-6
        hy = huddle["y"] * 0.0076e-6
        hz = huddle["z"] * 0.0076e-6
    else:
        hx = hy = hz = hf = None

    return e_out, n_out, z_out, time_e, time_n, time_z, sr_out, hx, hy, hz, hf




'''##########################################################################################################################'''
'''##########################################################################################################################'''

                    #####  #   #######   #####     #####  #####  #      #####   ####  #####  ###   ###   ##    #
                      #    #   #  #  #   #         #      #      #      #      #        #     #   #   #  # #   #
                      #    #   #  #  #   ###       #####  ####   #      ###    #        #     #   #   #  #  #  #
                      #    #   #  #  #   #             #  #      #      #      #        #     #   #   #  #   # #
                      #    #      #   #  #####     #####  #####  #####  #####   ####    #    ###   ###   #    ##

'''##########################################################################################################################'''
'''##########################################################################################################################'''


# ─────────────────────────────────────────────────────────────────
#  Colours / fonts
# ─────────────────────────────────────────────────────────────────

BG     = "#1a1d23"
BG2    = "#22262e"
ACCENT = "#00c8a0"
FG     = "#dce3ec"
FG2    = "#8893a6"
FONT_H = ("Courier", 13, "bold")
FONT_B = ("Courier", 11)
FONT_S = ("Courier", 10)


def _mk_entry(parent, label_text, default_val, row, col_offset=0):
    """Create label + entry at grid row/col_offset. Returns the Entry widget."""
    tk.Label(parent, text=label_text, bg=BG, fg=FG2, font=FONT_S, anchor="e").grid(
        row=row, column=col_offset, sticky="e", padx=(10, 4), pady=3)
    ent = tk.Entry(parent, width=16, bg=BG2, fg=FG, insertbackground=FG,
                   relief="flat", font=FONT_B,
                   highlightthickness=1, highlightbackground=FG2, highlightcolor=ACCENT)
    ent.insert(0, str(default_val) if default_val is not None else "")
    ent.grid(row=row, column=col_offset + 1, sticky="ew", padx=(0, 12), pady=3)
    return ent


def _float_or_none(text):
    """Convert entry string to float or None; raises ValueError on bad input."""
    t = text.strip().lower()
    if t in ("", "none"):
        return None
    return float(t)


# ─────────────────────────────────────────────────────────────────
#  DateTime dialog (MiniSEED)
# ─────────────────────────────────────────────────────────────────

class _DateTimeDialog(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)
        self.title("MiniSEED Time Range")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.result = None
        self.grab_set()

        tk.Label(self, text="MiniSEED Time Range", bg=BG, fg=ACCENT, font=FONT_H).pack(pady=(16, 4))
        tk.Label(self,
                 text="Format: 2020-01-01T00:00:00\nLeave blank to use the full file range.",
                 bg=BG, fg=FG2, font=FONT_S).pack(pady=(0, 10))

        frame = tk.Frame(self, bg=BG)
        frame.pack(padx=20, pady=4)

        tk.Label(frame, text="Start time:", bg=BG, fg=FG, font=FONT_B, width=12, anchor="w").grid(
            row=0, column=0, pady=6)
        self.start_ent = tk.Entry(frame, width=28, bg=BG2, fg=FG, insertbackground=FG,
                                  relief="flat", font=FONT_B,
                                  highlightthickness=1, highlightbackground=FG2, highlightcolor=ACCENT)
        self.start_ent.grid(row=0, column=1, pady=6, padx=(4, 0))

        tk.Label(frame, text="End time:", bg=BG, fg=FG, font=FONT_B, width=12, anchor="w").grid(
            row=1, column=0, pady=6)
        self.end_ent = tk.Entry(frame, width=28, bg=BG2, fg=FG, insertbackground=FG,
                                relief="flat", font=FONT_B,
                                highlightthickness=1, highlightbackground=FG2, highlightcolor=ACCENT)
        self.end_ent.grid(row=1, column=1, pady=6, padx=(4, 0))

        bf = tk.Frame(self, bg=BG)
        bf.pack(pady=14)
        tk.Button(bf, text="  Load  ", command=self._ok,
                  bg=ACCENT, fg=BG, font=FONT_H, relief="flat", cursor="hand2").pack(side="left", padx=8)
        tk.Button(bf, text=" Cancel ", command=self.destroy,
                  bg=BG2, fg=FG2, font=FONT_B, relief="flat", cursor="hand2").pack(side="left", padx=8)

        self.bind("<Return>", lambda _: self._ok())
        self.bind("<Escape>", lambda _: self.destroy())
        self.wait_window(self)

    def _ok(self):
        start_str = self.start_ent.get().strip()
        end_str   = self.end_ent.get().strip()
        start = end = None

        if start_str:
            try:
                start = UTCDateTime(start_str)
            except Exception as exc:
                messagebox.showerror("Invalid date", f"Start time error:\n{exc}", parent=self)
                return
        if end_str:
            try:
                end = UTCDateTime(end_str)
            except Exception as exc:
                messagebox.showerror("Invalid date", f"End time error:\n{exc}", parent=self)
                return

        self.result = (start, end)
        self.destroy()




'''##########################################################################################################################'''
'''##########################################################################################################################'''

                            ######   ###   ##    #  #####  #      #####
                            #       #   #  # #   #    #    #      #
                            ######  #####  #  #  #    #    #      ###
                            #       #   #  #   # #    #    #      #
                            #       #   #  #    ##  #####  #####  #####

'''##########################################################################################################################'''
'''##########################################################################################################################'''


class CEAnalysisApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("CE Analysis  |  Sensor Data Tool")
        self.configure(bg=BG)
        self.minsize(680, 480)

        self.sensor_data = None
        self.function    = None
        self.status_var  = tk.StringVar(value="Ready")

        self._build_ui()

    # ─────────────────────────────────────────────────────────
    #  UI
    # ─────────────────────────────────────────────────────────

    def _build_ui(self):
        tk.Frame(self, bg=ACCENT, height=3).pack(fill="x")

        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=24, pady=(16, 4))
        tk.Label(hdr, text="CE ANALYSIS",
                 bg=BG, fg=ACCENT, font=("Courier", 22, "bold")).pack(side="left")
        tk.Label(hdr, text="  //  Sensor Data Tool",
                 bg=BG, fg=FG2, font=("Courier", 13)).pack(side="left", pady=2)

        # 1 · Sensor
        sf = tk.LabelFrame(self, text=" 1 · Select Sensor ",
                           bg=BG, fg=ACCENT, font=FONT_B, bd=1, relief="solid")
        sf.pack(fill="x", padx=24, pady=(10, 4))
        self.sensor_var = tk.StringVar(value="mag")
        row = tk.Frame(sf, bg=BG)
        row.pack(padx=12, pady=10, anchor="w")
        for text, val in [("Magnetometer (CSV)",              "mag"),
                          ("Seismometer  WebDAQ (CSV)",       "seis"),
                          ("Seismometer  Minimus (MiniSEED)", "mini")]:
            tk.Radiobutton(row, text=text, variable=self.sensor_var, value=val,
                           bg=BG, fg=FG, selectcolor=BG2, activebackground=BG,
                           activeforeground=ACCENT, font=FONT_B).pack(anchor="w", pady=2)

        # 2 · Load
        lf = tk.LabelFrame(self, text=" 2 · Load Data ",
                           bg=BG, fg=ACCENT, font=FONT_B, bd=1, relief="solid")
        lf.pack(fill="x", padx=24, pady=4)
        li = tk.Frame(lf, bg=BG)
        li.pack(padx=12, pady=10)
        self.file_label = tk.Label(li, text="No file loaded", bg=BG, fg=FG2, font=FONT_S)
        self.file_label.pack(side="left", padx=(0, 12))
        tk.Button(li, text="  Browse & Load File(s)  ", command=self._load_data,
                  bg=BG2, fg=ACCENT, font=FONT_B, relief="flat",
                  activebackground=ACCENT, activeforeground=BG, cursor="hand2",
                  highlightthickness=1, highlightbackground=ACCENT).pack(side="left")

        # 3 · Analysis
        af = tk.LabelFrame(self, text=" 3 · Analysis ",
                           bg=BG, fg=ACCENT, font=FONT_B, bd=1, relief="solid")
        af.pack(fill="x", padx=24, pady=4)
        bg_grid = tk.Frame(af, bg=BG)
        bg_grid.pack(padx=12, pady=10, fill="x")
        bg_grid.columnconfigure((0, 1, 2), weight=1)

        for col, (label, cmd) in enumerate([
            ("📈  Time Series",  self._open_time_series),
            ("📊  FFT Spectrum", self._open_spectrum),
            ("🔥  Spectrogram",  self._open_spectrogram),
        ]):
            tk.Button(bg_grid, text=label, command=cmd,
                      bg=BG2, fg=FG, font=FONT_B, relief="flat",
                      activebackground=ACCENT, activeforeground=BG,
                      cursor="hand2", width=22, pady=8,
                      highlightthickness=1, highlightbackground=FG2,
                      ).grid(row=0, column=col, padx=6, sticky="ew")

        # Status
        sb = tk.Frame(self, bg=BG2, height=26)
        sb.pack(fill="x", side="bottom")
        tk.Label(sb, textvariable=self.status_var, bg=BG2, fg=FG2, font=FONT_S
                 ).pack(side="left", padx=10, pady=4)

    # ─────────────────────────────────────────────────────────
    #  Helpers
    # ─────────────────────────────────────────────────────────

    def _status(self, msg):
        self.status_var.set(msg)
        self.update_idletasks()

    def _check_data(self):
        if self.sensor_data is None:
            messagebox.showwarning("No data", "Please load data first (Step 2).")
            return False
        return True

    # ─────────────────────────────────────────────────────────
    #  Data loading
    # ─────────────────────────────────────────────────────────

    def _load_data(self):
        func = self.sensor_var.get()

        if func in ("mag", "seis"):
            path = filedialog.askopenfilename(
                title="Select CSV data file",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
            if not path:
                return
            self.file_label.config(text=os.path.basename(path), fg=FG)
            self._status("Loading CSV data…")

            def _worker():
                try:
                    result = load_csv_data(path, func)
                    def _done():
                        self.sensor_data = result
                        self.function    = func
                        self._status(f"✓ Loaded  |  SR = {result[0]:.1f} Hz  |  {os.path.basename(path)}")
                    self.after(0, _done)
                except Exception as exc:
                    self.after(0, lambda: messagebox.showerror("Load Error", str(exc)))
                    self.after(0, lambda: self._status("Load failed."))

            threading.Thread(target=_worker, daemon=True).start()

        elif func == "mini":
            # askopenfilenames supports multi-select natively
            paths = filedialog.askopenfilenames(
                title="Select MiniSEED files (one per channel)",
                filetypes=[("MiniSEED", "*.mseed *.miniseed"), ("All Files", "*.*")])
            if not paths:
                return
            self.file_label.config(text=f"{len(paths)} file(s) selected", fg=FG)

            dlg = _DateTimeDialog(self)
            if dlg.result is None:
                return
            start_time, end_time = dlg.result

            self._status("Loading MiniSEED data…")

            def _worker():
                try:
                    result = load_mseed_data(sorted(paths), start_time, end_time)
                    def _done():
                        self.sensor_data = result
                        self.function    = "mini"
                        self._status(f"✓ Loaded  |  SR = {result[6]:.1f} Hz  |  {len(paths)} files")
                    self.after(0, _done)
                except Exception as exc:
                    self.after(0, lambda: messagebox.showerror("Load Error", str(exc)))
                    self.after(0, lambda: self._status("Load failed."))

            threading.Thread(target=_worker, daemon=True).start()

    # ─────────────────────────────────────────────────────────
    #  Window openers
    # ─────────────────────────────────────────────────────────

    def _open_time_series(self):
        if self._check_data(): TimeSeriesWindow(self)

    def _open_spectrum(self):
        if self._check_data(): SpectrumWindow(self)

    def _open_spectrogram(self):
        if self._check_data(): SpectrogramWindow(self)




'''##########################################################################################################################'''
'''##########################################################################################################################'''

                    #####  ###  #      #####       #   #  ###  ##    #  ####    ###   #   #  #####
                      #     #   #      #           #   #   #   # #   #  #   #  #   #  #   #  #
                      #     #   #      ###         # # #   #   #  #  #  #   #  #   #  # # #  ###
                      #     #   #      #           ## ##   #   #   # #  #   #  #   #   # #   #
                      #    ###  #####  #####       #   #  ###  #    ##  ####    ###    # #   #####

'''##########################################################################################################################'''
'''##########################################################################################################################'''


class _AnalysisWindow(tk.Toplevel):
    """
    Base class.
    KEY RULE: matplotlib must only be called from the main thread.
    Use _compute_then_plot(compute_fn, plot_fn) for all analysis:
      - compute_fn() runs on a worker thread (no plt calls)
      - plot_fn(result) is scheduled on the main thread via self.after(0,...)
    """

    def __init__(self, app, title):
        super().__init__(app)
        self.app = app
        self.title(title)
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(560, 360)

        data = app.sensor_data
        func = app.function

        if func in ("mag", "seis"):
            (self.sr, self.time,
             self.x,  self.y,  self.z,
             self.ligo_x, self.ligo_y, self.ligo_z, self.ligo_extra) = data
        elif func == "mini":
            (self.x,  self.y,  self.z,
             t_e, t_n, t_z, self.sr,
             self.ligo_x, self.ligo_y, self.ligo_z, self.ligo_extra) = data
            self.time = [t_e, t_n, t_z]

        self.function = func

        tk.Frame(self, bg=ACCENT, height=3).pack(fill="x")
        tk.Label(self, text=title.upper(),
                 bg=BG, fg=ACCENT, font=FONT_H).pack(pady=(12, 4), padx=20, anchor="w")

    def _compute_then_plot(self, compute_fn, plot_fn):
        """
        compute_fn() → result   (worker thread, no plt calls)
        plot_fn(result)          (main thread, plt calls OK)
        """
        def _worker():
            try:
                result = compute_fn()
                self.after(0, lambda: plot_fn(result))
            except Exception as exc:
                import traceback; traceback.print_exc()
                self.after(0, lambda: messagebox.showerror("Error", str(exc), parent=self))

        threading.Thread(target=_worker, daemon=True).start()




'''##########################################################################################################################'''
'''##########################################################################################################################'''

                              #####  #   #######   #####     #####  #####  ####    #  #####  #####
                                #    #   #  #  #   #         #      #      #   #   #  #      #    
                                #    #   #  #  #   ###       #####  ####   ####    #  ###    #####
                                #    #   #  #  #   #             #  #      #   #   #  #          #
                                #    #   #     #   #####     #####  #####  #   #   #  #####  #####

'''##########################################################################################################################'''
'''##########################################################################################################################'''



class TimeSeriesWindow(_AnalysisWindow):

    def __init__(self, app):
        super().__init__(app, "Time Series")

        func = self.function

        # Default x limits
        if func == "mini":
            self.xmax_def = float(self.time[0][-1])
        else:
            t = self.time
            self.xmax_def = float(t.iloc[-1] if hasattr(t, 'iloc') else t[-1])
        self.xmin_def = 0.0

        if func == "mag":
            self.amp_unit  = "[T]"
            self.ch_labels = ("X", "Y", "Z")
        else:
            self.amp_unit  = "[m/s]"
            self.ch_labels = ("E", "N", "Z")

        self._build()

    def _build(self):
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=20, pady=10)

        # ── channel selector ─────────────────────────────────
        cf = tk.LabelFrame(main, text=" Channel(s) to plot ",
                           bg=BG, fg=ACCENT, font=FONT_B, bd=1, relief="solid")
        cf.pack(fill="x", pady=(0, 8))
        self.channel_var = tk.StringVar(value="all")
        cr = tk.Frame(cf, bg=BG)
        cr.pack(padx=10, pady=8, anchor="w")
        L = self.ch_labels
        for text, val in [("All channels", "all"),
                          (f"{L[0]} axis",  "east"),
                          (f"{L[1]} axis",  "north"),
                          ("Z axis",        "zed")]:
            tk.Radiobutton(cr, text=text, variable=self.channel_var, value=val,
                           bg=BG, fg=FG, selectcolor=BG2, activebackground=BG,
                           activeforeground=ACCENT, font=FONT_B).pack(side="left", padx=10)

        # ── axis limits ──────────────────────────────────────
        lf = tk.LabelFrame(main, text=" Axis Limits  (leave blank = auto) ",
                           bg=BG, fg=ACCENT, font=FONT_B, bd=1, relief="solid")
        lf.pack(fill="x", pady=(0, 8))
        g = tk.Frame(lf, bg=BG)
        g.pack(padx=10, pady=8)

        self.xmin_ent = _mk_entry(g, f"X min [s]",           self.xmin_def, 0, 0)
        self.xmax_ent = _mk_entry(g, f"X max [s]",           self.xmax_def, 0, 2)
        self.ymin_ent = _mk_entry(g, f"Y min {self.amp_unit}", "",          1, 0)
        self.ymax_ent = _mk_entry(g, f"Y max {self.amp_unit}", "",          1, 2)

        # ── buttons ──────────────────────────────────────────
        bf = tk.Frame(main, bg=BG)
        bf.pack(pady=8)
        tk.Button(bf, text="  Plot  ", command=self._plot,
                  bg=ACCENT, fg=BG, font=FONT_H, relief="flat",
                  activebackground="#00e0b5", cursor="hand2",
                  padx=14, pady=6).pack(side="left", padx=8)
        tk.Button(bf, text="Reset limits", command=self._reset,
                  bg=BG2, fg=FG2, font=FONT_B, relief="flat", cursor="hand2",
                  padx=10).pack(side="left", padx=8)

    def _reset(self):
        for ent, val in [(self.xmin_ent, self.xmin_def),
                         (self.xmax_ent, self.xmax_def),
                         (self.ymin_ent, ""),
                         (self.ymax_ent, "")]:
            ent.delete(0, "end")
            if val != "":
                ent.insert(0, str(val))

    def _plot(self):
        try:
            xmin = _float_or_none(self.xmin_ent.get())
            xmax = _float_or_none(self.xmax_ent.get())
            ymin = _float_or_none(self.ymin_ent.get())
            ymax = _float_or_none(self.ymax_ent.get())
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc), parent=self)
            return

        channel  = self.channel_var.get()
        function = self.function
        time     = self.time

        # Convert to numpy arrays now, outside the closure, to avoid
        # pandas Series indexing in a thread and potential stale references
        x_arr = np.asarray(self.x)
        y_arr = np.asarray(self.y)
        z_arr = np.asarray(self.z)

        if function == "mag":
            title   = "Magnetic"
            labels  = list(self.ch_labels)   # ["X","Y","Z"]
            y_label = "Amplitude [T]"
        else:
            title   = "Seismic"
            labels  = list(self.ch_labels)   # ["E","N","Z"]
            y_label = "Amplitude (m/s)"

        if function == "mini":
            t0, t1, t2 = np.asarray(time[0]), np.asarray(time[1]), np.asarray(time[2])
        else:
            t_arr = np.asarray(time)
            t0 = t1 = t2 = t_arr

        # Plot runs on the main thread — scheduled via after(0,...)
        # No heavy computation here so no worker thread needed.
        def _do(_=None):
            if function == "mag" and channel == "all":
                # Original behaviour: separate figure per channel
                for data, label, t_ax, color in zip(
                        [x_arr, y_arr, z_arr], labels, [t0, t1, t2],
                        ['blue', 'red', 'black']):
                    fig, ax = plt.subplots(figsize=(20, 8))
                    ax.yaxis.get_offset_text().set_fontsize(16)
                    ax.plot(t_ax, data, linewidth=1.5, color=color, label=label)
                    ax.set_title(title + " Channel: " + label, fontweight='bold', fontsize=25)
                    ax.set_xlabel("Time (s)", fontweight="bold", fontsize=20)
                    ax.set_ylabel(y_label,    fontweight="bold", fontsize=20)
                    ax.set_xlim(xmin, xmax)
                    ax.set_ylim(ymin, ymax)
                    ax.tick_params(axis='both', labelsize=20)
                    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
                        lbl.set_fontweight("bold")
                    ax.legend(loc="upper right", fontsize=18)
                    ax.grid(True)
                    fig.tight_layout()
                    plt.show()
                return

            # Build plot list
            if channel == "all":
                plots     = [(labels[0], x_arr, t0, 'blue'),
                             (labels[1], y_arr, t1, 'red'),
                             (labels[2], z_arr, t2, 'black')]
                fig_title = title + " Data Time Series"
            elif channel == "east":
                plots     = [(labels[0], x_arr, t0, 'blue')]
                fig_title = title + " Channel: " + labels[0]
            elif channel == "north":
                plots     = [(labels[1], y_arr, t1, 'red')]
                fig_title = title + " Channel: " + labels[1]
            else:   # zed
                plots     = [(labels[2], z_arr, t2, 'black')]
                fig_title = title + " Channel: " + labels[2]

            fig, ax = plt.subplots(figsize=(20, 8))
            ax.yaxis.get_offset_text().set_fontsize(16)
            for label, data, t_ax, color in plots:
                ax.plot(t_ax, data, linewidth=1.5, color=color, label=label)
            ax.set_title(fig_title, fontweight='bold', fontsize=25)
            ax.set_xlabel("Time (s)", fontweight="bold", fontsize=20)
            ax.set_ylabel(y_label,   fontweight="bold", fontsize=20)
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(ymin, ymax)
            ax.tick_params(axis='both', labelsize=20)
            for lbl in ax.get_xticklabels() + ax.get_yticklabels():
                lbl.set_fontweight("bold")
            ax.legend(loc="upper right", fontsize=18)
            ax.grid(True)
            fig.tight_layout()
            plt.show()

        self.after(0, _do)   # always on main thread




'''##########################################################################################################################'''
'''##########################################################################################################################'''

                    #####  ####   #####   ####  #####  ####    #    #  #######
                    #      #   #  #      #        #    #   #   #    #  #  #  #
                    #####  ####   ####   #        #    ####    #    #  #  #  #
                        #  #      #      #        #    #   #   #    #  #  #  #
                    #####  #      #####   ####    #    #   #    ####   #     #

'''##########################################################################################################################'''
'''##########################################################################################################################'''


def _asd_compute(data_z, data_n, data_e, sample_rate,
                 lf, lx, ly, lz,
                 bart_sample_rate, bart_x, bart_y, bart_z,
                 frequency, over_lap, fft, signal_prom, mode):
    """
    Pure computation: Welch PSD → ASD, peak finding.
    Returns a result dict.  NO matplotlib calls.
    """
    warnings.simplefilter('ignore')

    def _spectrum(data, sr):
        f, Pxx = signal.welch(data, sr, window='hamming',
                              nperseg=int(sr * fft),
                              noverlap=round(sr * (over_lap * 0.01)))
        return f, np.sqrt(Pxx)

    def _peaks(sf, sl, freq, sp):
        tol = 1
        if freq is None:
            p, _ = signal.find_peaks(sl, prominence=sp)
        else:
            mask = (sf >= freq - tol) & (sf <= freq + tol)
            pl, _ = signal.find_peaks(sl[mask], prominence=sp)
            p = np.where(mask)[0][pl]
        return p

    input_data = {'z': data_z, 'n': data_n, 'e': data_e}
    results    = {}

    for key, data in input_data.items():
        if data is None:
            continue
        sf, amp = _spectrum(data, sample_rate)
        log_amp = np.log(np.clip(amp, 1e-300, None))
        disp    = amp / (2 * np.pi * sf) if mode == 'displacement' else None
        pk      = _peaks(sf, log_amp, frequency, signal_prom)
        results[key] = {'frequency': sf, 'amp': amp, 'disp': disp, 'peaks': pk}

    # Resolve LIGO / control arrays
    ctrl_f = lf
    ctrl_x = lx
    ctrl_y = ly
    ctrl_z = lz

    if bart_sample_rate is not None:
        ref_data = {'x': bart_x, 'y': bart_y, 'z': bart_z}
        ref_out  = {}
        for key, data in ref_data.items():
            if data is not None:
                ctrl_f, amp = _spectrum(data, bart_sample_rate)
                ref_out[key] = amp
        ctrl_x = ref_out.get('x')
        ctrl_y = ref_out.get('y')
        ctrl_z = ref_out.get('z')

    return {
        'results':   results,
        'ctrl_f':    ctrl_f,
        'ctrl_x':    ctrl_x,
        'ctrl_y':    ctrl_y,
        'ctrl_z':    ctrl_z,
        'mode':      mode,
        'frequency': frequency,
        'fft':       fft,
        'over_lap':  over_lap,
    }


def _asd_plot(computed, drctn_title, v_title, s_title, v_label, s_label,
              channel, ymin, ymax, xmin, xmax):
    """
    Draw an ASD figure.  Must be called from the MAIN thread.
    """
    results  = computed['results']
    ctrl_f   = computed['ctrl_f']
    ctrl_x   = computed['ctrl_x']
    ctrl_y   = computed['ctrl_y']
    ctrl_z   = computed['ctrl_z']
    mode     = computed['mode']
    frequency = computed['frequency']
    fft      = computed['fft']
    over_lap = computed['over_lap']

    color_map = {'z': 'black', 'n': 'red',   'e': 'blue'}
    ctrl_map  = {'z': ctrl_z,  'n': ctrl_y,  'e': ctrl_x}
    title_map = {'z': drctn_title[2], 'n': drctn_title[1], 'e': drctn_title[0]}

    title_str = v_title if mode == 'velocity' else s_title
    ylabel    = v_label if mode == 'velocity' else s_label

    if channel == 'all':
        channels_to_plot = ['z', 'n', 'e']
    else:
        channels_to_plot = [channel[0]]       # "east"→'e', "north"→'n', "zed"→'z'
        title_str = title_map[channels_to_plot[0]]

    fig, ax = plt.subplots(figsize=(20, 8))
    ax.set_yscale('log')
    ax.set_xscale('log')

    for ch in channels_to_plot:
        if ch not in results:
            continue

        y_vals = results[ch]['amp'] if mode == 'velocity' else results[ch]['disp']
        f      = results[ch]['frequency']
        pk     = results[ch]['peaks']

        ax.plot(f, y_vals, color=color_map[ch], linewidth=1.75, label=title_map[ch])

        if ctrl_map[ch] is not None and ctrl_f is not None:
            ax.plot(ctrl_f, ctrl_map[ch], color='dimgrey', linewidth=2,
                    alpha=0.5, label=f'LIGO {title_map[ch]}')

        if len(f[pk]) > 0:
            ax.scatter(f[pk], y_vals[pk], s=100, color='limegreen', marker='x', linewidths=2.5)
            if frequency is not None:
                print(f'{title_map[ch]}:  {f[pk][0]:.2f} Hz   Ampl: {y_vals[pk][0]:.3e}')
        else:
            print(f"No peaks in {title_map[ch]}")

    ax.legend(loc='lower left', fontsize=14.5, ncol=2)
    ax.set_title('FFT: ' + str(fft) + 's',         fontsize=18, loc='left',  style='italic')
    ax.set_title('Overlap: ' + str(over_lap) + '%', fontsize=18, loc='right', style='italic')
    ax.set_title(title_str, fontweight='bold', fontsize=25)
    ax.set_xlabel('Frequency [Hz]', fontweight='bold', fontsize=20)
    ax.set_ylabel(ylabel,           fontweight='bold', fontsize=20)
    ax.tick_params(axis='both', which='major', labelsize=20)
    ax.tick_params(axis='both', which='minor', labelsize=16)
    for lbl in ax.get_yticklabels(which='minor') + ax.get_xticklabels(which='minor'):
        lbl.set_fontweight('bold')
    if frequency is not None:
        ax.xaxis.set_minor_formatter(mticker.ScalarFormatter())
    ax.set_ylim(ymin, ymax)
    ax.set_xlim(xmin, xmax)
    ax.grid(True, which='both', ls='-')
    fig.tight_layout()
    plt.show()




class SpectrumWindow(_AnalysisWindow):
    """
    FFT / ASD Spectrum window.

    Layout:
      ┌─ FFT Parameters ──────────────────────────────────────┐
      │  FFT Length [s]  |  Overlap [%]                       │
      ├─ Plot Limits ─────────────────────────────────────────┤
      │  X min / X max                                        │
      │  Y vel min / Y vel max                                │
      │  Y disp min / Y disp max                              │
      │  Peak Prominence                                      │
      ├─ Time Slice (optional) ───────────────────────────────┤
      │  Start [s]  |  End [s]                                │
      ├─ Specific Frequency (optional) ───────────────────────┤
      │  Freq [Hz]                                            │
      └───────────────────────────────────────────────────────┘
      [Plot Velocity] [Plot Displacement] [Compare LIGO]
      [Specific Frequency] [Reset]
    """

    def __init__(self, app):
        super().__init__(app, "FFT Spectrum (ASD)")

        func = self.function

        if func in ("seis", "mini"):
            self.y_max   = 10e-6;  self.y_min  = 10e-13
            self.my_max  = 10e-7;  self.my_min = 10e-15
            self.x_max   = 100;    self.x_min  = 0.1
            self.fft_len = 128;    self.overlap = 50;  self.prom = 5
            self.v_title     = "Seismic Velocity Data ASD"
            self.s_title     = "Seismic Dispacement Data ASD"
            self.drctn_title = ["E Direction", "N Direction", "Z Direction"]
            self.v_label     = "Amplitude [ms⁻¹/√Hz]"
            self.s_label     = "Amplitude [m/√Hz]"
        else:   # mag
            self.y_max   = 10e-8;  self.y_min  = 10e-13
            self.my_max  = None;   self.my_min = None
            self.x_max   = 2000;   self.x_min  = 0.01
            self.fft_len = 10;     self.overlap = 50;  self.prom = 5
            self.v_title     = "Magnetic Data ASD"
            self.s_title     = ""
            self.drctn_title = ["X Direction", "Y Direction", "Z Direction"]
            self.v_label     = "Amplitude [T/√Hz]"
            self.s_label     = ""

        self._build()

    def _build(self):
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=20, pady=8)

        # ── FFT Parameters ───────────────────────────────────
        ff = tk.LabelFrame(main, text=" FFT Parameters ",
                           bg=BG, fg=ACCENT, font=FONT_B, bd=1, relief="solid")
        ff.pack(fill="x", pady=(0, 5))
        fg = tk.Frame(ff, bg=BG)
        fg.pack(padx=10, pady=8)
        self.fft_ent  = _mk_entry(fg, "FFT Length [s]", self.fft_len,  0, 0)
        self.ovlp_ent = _mk_entry(fg, "Overlap [%]",    self.overlap,  0, 2)

        # ── Plot Limits ──────────────────────────────────────
        plf = tk.LabelFrame(main, text=" Plot Limits ",
                            bg=BG, fg=ACCENT, font=FONT_B, bd=1, relief="solid")
        plf.pack(fill="x", pady=(0, 5))
        pg = tk.Frame(plf, bg=BG)
        pg.pack(padx=10, pady=8)
        self.xmin_ent  = _mk_entry(pg, "X min [Hz]",    self.x_min,  0, 0)
        self.xmax_ent  = _mk_entry(pg, "X max [Hz]",    self.x_max,  0, 2)
        self.ymin_ent  = _mk_entry(pg, "Y vel min",     self.y_min,  1, 0)
        self.ymax_ent  = _mk_entry(pg, "Y vel max",     self.y_max,  1, 2)
        self.mymin_ent = _mk_entry(pg, "Y disp min",    self.my_min, 2, 0)
        self.mymax_ent = _mk_entry(pg, "Y disp max",    self.my_max, 2, 2)
        self.prom_ent  = _mk_entry(pg, "Peak Prominence", self.prom, 3, 0)

        # ── Time Slice ───────────────────────────────────────
        tsf = tk.LabelFrame(main, text=" Time Slice  (optional — leave blank for full data) ",
                            bg=BG, fg=ACCENT, font=FONT_B, bd=1, relief="solid")
        tsf.pack(fill="x", pady=(0, 5))
        tsg = tk.Frame(tsf, bg=BG)
        tsg.pack(padx=10, pady=8)
        self.ts_ent = _mk_entry(tsg, "Start [s]", "", 0, 0)
        self.te_ent = _mk_entry(tsg, "End [s]",   "", 0, 2)

        # ── Specific Frequency ───────────────────────────────
        sqf = tk.LabelFrame(main, text=" Specific Frequency  (optional — used by the button below) ",
                            bg=BG, fg=ACCENT, font=FONT_B, bd=1, relief="solid")
        sqf.pack(fill="x", pady=(0, 5))
        sqg = tk.Frame(sqf, bg=BG)
        sqg.pack(padx=10, pady=8, anchor="w")
        self.freq_ent = _mk_entry(sqg, "Freq [Hz]", "", 0, 0)

        # ── Buttons ──────────────────────────────────────────
        bf = tk.Frame(main, bg=BG)
        bf.pack(pady=8)

        def _btn(text, cmd, accent=False):
            tk.Button(bf, text=text, command=cmd,
                      bg=ACCENT if accent else BG2,
                      fg=BG     if accent else FG,
                      font=FONT_B, relief="flat",
                      activebackground=ACCENT, activeforeground=BG,
                      cursor="hand2", padx=8, pady=5,
                      ).pack(side="left", padx=4)

        _btn("Plot Velocity",      self._plot_velocity,    accent=True)
        _btn("Plot Displacement",  self._plot_displacement)
        _btn("Compare LIGO",       self._plot_ligo)
        _btn("Specific Frequency", self._plot_freq)
        _btn("Reset",              self._reset)

    # ── helpers ──────────────────────────────────────────────

    def _get_params(self):
        try:
            fft   = _float_or_none(self.fft_ent.get())  or self.fft_len
            ovlp  = _float_or_none(self.ovlp_ent.get()) or self.overlap
            prom  = _float_or_none(self.prom_ent.get()) or self.prom
            xmin  = _float_or_none(self.xmin_ent.get())
            xmax  = _float_or_none(self.xmax_ent.get())
            ymin  = _float_or_none(self.ymin_ent.get())
            ymax  = _float_or_none(self.ymax_ent.get())
            mymin = _float_or_none(self.mymin_ent.get())
            mymax = _float_or_none(self.mymax_ent.get())
            ts    = _float_or_none(self.ts_ent.get())
            te    = _float_or_none(self.te_ent.get())
            freq  = _float_or_none(self.freq_ent.get())
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc), parent=self)
            return None
        return fft, ovlp, prom, xmin, xmax, ymin, ymax, mymin, mymax, ts, te, freq

    def _reset(self):
        pairs = [
            (self.fft_ent,  self.fft_len), (self.ovlp_ent, self.overlap),
            (self.prom_ent, self.prom),
            (self.xmin_ent, self.x_min),   (self.xmax_ent, self.x_max),
            (self.ymin_ent, self.y_min),   (self.ymax_ent, self.y_max),
            (self.mymin_ent, self.my_min), (self.mymax_ent, self.my_max),
            (self.ts_ent, ""),             (self.te_ent,   ""),
            (self.freq_ent, ""),
        ]
        for ent, val in pairs:
            ent.delete(0, "end")
            if val is not None and val != "":
                ent.insert(0, str(val))

    def _slice(self, ts, te):
        """Return x,y,z numpy arrays, optionally sample-sliced."""
        x = np.asarray(self.x)
        y = np.asarray(self.y)
        z = np.asarray(self.z)
        sr = self.sr
        if ts is not None and te is not None:
            s = max(0, int(ts * sr))
            e = int(te * sr)
            return x[s:e], y[s:e], z[s:e]
        return x, y, z

    # ── plot actions ─────────────────────────────────────────

    def _plot_velocity(self):
        p = self._get_params()
        if p is None: return
        fft, ovlp, prom, xmin, xmax, ymin, ymax, _, __, ts, te, _f = p

        x, y, z = self._slice(ts, te)
        sr = self.sr

        # Capture label strings by value now (not inside closure)
        drctn = list(self.drctn_title)
        vt, st, vl, sl = self.v_title, self.s_title, self.v_label, self.s_label

        def _compute():
            return _asd_compute(z, y, x, sr,
                                None, None, None, None,
                                None, None, None, None,
                                None, ovlp, fft, prom, 'velocity')

        def _plot(computed):
            _asd_plot(computed, drctn, vt, st, vl, sl, 'all', ymin, ymax, xmin, xmax)

        self._compute_then_plot(_compute, _plot)

    def _plot_displacement(self):
        if self.function not in ("seis", "mini"):
            messagebox.showinfo("Not available",
                                "Displacement is only available for Seismometer data.",
                                parent=self)
            return
        p = self._get_params()
        if p is None: return
        fft, ovlp, prom, xmin, xmax, _yv1, _yv2, mymin, mymax, ts, te, _f = p

        x, y, z = self._slice(ts, te)
        sr = self.sr
        drctn = list(self.drctn_title)
        vt, st, vl, sl = self.v_title, self.s_title, self.v_label, self.s_label

        def _compute():
            return _asd_compute(z, y, x, sr,
                                None, None, None, None,
                                None, None, None, None,
                                None, ovlp, fft, prom, 'displacement')

        def _plot(computed):
            _asd_plot(computed, drctn, vt, st, vl, sl, 'all', mymin, mymax, xmin, xmax)

        self._compute_then_plot(_compute, _plot)

    def _plot_ligo(self):
        p = self._get_params()
        if p is None: return
        fft, ovlp, prom, xmin, xmax, ymin, ymax, _, __, ts, te, _f = p

        # ── capture all references by value BEFORE defining closures ──
        lx_v = self.ligo_x
        ly_v = self.ligo_y
        lz_v = self.ligo_z
        ex_v = self.ligo_extra
        func = self.function
        sr   = self.sr
        drctn = list(self.drctn_title)
        vt, st, vl, sl = self.v_title, self.s_title, self.v_label, self.s_label

        if lx_v is None:
            messagebox.showinfo("LIGO data not found",
                                "Control data file not found in working directory.", parent=self)
            return

        x_arr, y_arr, z_arr = self._slice(ts, te)

        if func in ("seis", "mini"):
            lf_v  = ex_v                             # pre-computed freq axis
            bs_v  = None
            bx_v = by_v = bz_v = None
            cx_v, cy_v, cz_v = lx_v, ly_v, lz_v
        else:   # mag
            lf_v  = None
            bs_v  = ex_v                             # bart sample rate
            bx_v, by_v, bz_v = lx_v, ly_v, lz_v
            cx_v = cy_v = cz_v = None

        # Per-channel triplets: (channel_key, data_z, data_n, data_e)
        channel_defs = [
            ("east",  None,  None,   x_arr),
            ("north", None,  y_arr,  None),
            ("zed",   z_arr, None,   None),
        ]

        for ch, dz, dn, de in channel_defs:
            # Use default-arg trick so each closure captures its own values
            def _make_compute(dz=dz, dn=dn, de=de):
                def _compute():
                    return _asd_compute(dz, dn, de, sr,
                                        lf_v, cx_v, cy_v, cz_v,
                                        bs_v, bx_v, by_v, bz_v,
                                        None, ovlp, fft, prom, 'velocity')
                return _compute

            def _make_plot(ch=ch):
                def _plot(computed):
                    _asd_plot(computed, drctn, vt, st, vl, sl,
                              ch, ymin, ymax, xmin, xmax)
                return _plot

            self._compute_then_plot(_make_compute(), _make_plot())

    def _plot_freq(self):
        p = self._get_params()
        if p is None: return
        fft, ovlp, prom, xmin, xmax, ymin, ymax, _, __, ts, te, freq = p

        if freq is None:
            messagebox.showwarning("No frequency",
                                   "Enter a target frequency in the 'Freq [Hz]' field.", parent=self)
            return

        freq_min = freq - 1
        freq_max = freq + 1

        # Capture by value
        lx_v = self.ligo_x
        ly_v = self.ligo_y
        lz_v = self.ligo_z
        ex_v = self.ligo_extra
        func = self.function
        sr   = self.sr
        drctn = list(self.drctn_title)
        vt, st, vl, sl = self.v_title, self.s_title, self.v_label, self.s_label

        x_arr, y_arr, z_arr = self._slice(ts, te)

        if func in ("seis", "mini"):
            lf_v  = ex_v
            bs_v  = None
            bx_v = by_v = bz_v = None
            cx_v, cy_v, cz_v = lx_v, ly_v, lz_v
        else:
            lf_v  = None
            bs_v  = ex_v
            bx_v, by_v, bz_v = lx_v, ly_v, lz_v
            cx_v = cy_v = cz_v = None
            fft  = 100
            prom = 4.5

        if lx_v is None:
            messagebox.showinfo("LIGO data not found",
                                "Control data not found. Plotting field data only.", parent=self)

        channel_defs = [
            ("east",  None,  None,   x_arr),
            ("north", None,  y_arr,  None),
            ("zed",   z_arr, None,   None),
        ]

        for ch, dz, dn, de in channel_defs:

            def _make_compute(dz=dz, dn=dn, de=de):
                def _compute():
                    return _asd_compute(dz, dn, de, sr,
                                        lf_v, cx_v, cy_v, cz_v,
                                        bs_v, bx_v, by_v, bz_v,
                                        freq, ovlp, fft, prom, 'velocity')
                return _compute

            def _make_plot(ch=ch):
                def _plot(computed):
                    _asd_plot(computed, drctn, vt, st, vl, sl,
                              ch, ymin, ymax, freq_min, freq_max)
                return _plot

            self._compute_then_plot(_make_compute(), _make_plot())




'''##########################################################################################################################'''
'''##########################################################################################################################'''

                #####  ####   #####   ####  #####  ####    ###    ###   ####    ####   #######
                #      #   #  #      #        #    #   #  #   #  #      #   #  #    #  #  #  #
                #####  ####   ####   #        #    ####   #   #  #  ##  ####   ######  #  #  #
                    #  #      #      #        #    #   #  #   #  #   #  #   #  #    #  #  #  #
                #####  #      #####   ####    #    #   #   ###    ###   #   #  #    #  #     #

'''##########################################################################################################################'''
'''##########################################################################################################################'''


class SpectrogramWindow(_AnalysisWindow):

    def __init__(self, app):
        super().__init__(app, "Spectrogram")

        func = self.function
        if func in ("seis", "mini"):
            self.cmin    = 10e-10; self.cmax    = 10e-9
            self.y_min   = 0;      self.y_max   = 100
            self.x_min   = 0;      self.x_max   = None
            self.fft_len = 10;     self.overlap  = 50
        else:
            self.cmin    = 10e-14; self.cmax    = 10e-10
            self.y_min   = 0;      self.y_max   = 500
            self.x_min   = None;   self.x_max   = None
            self.fft_len = 10;     self.overlap  = 50

        self._build()

    def _build(self):
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=20, pady=8)

        pf = tk.LabelFrame(main, text=" Spectrogram Parameters ",
                           bg=BG, fg=ACCENT, font=FONT_B, bd=1, relief="solid")
        pf.pack(fill="x", pady=(0, 8))
        pg = tk.Frame(pf, bg=BG)
        pg.pack(padx=10, pady=8)

        self.fft_ent  = _mk_entry(pg, "FFT Length [s]", self.fft_len,  0, 0)
        self.ovlp_ent = _mk_entry(pg, "Overlap [%]",    self.overlap,  0, 2)
        self.ymin_ent = _mk_entry(pg, "Y min [Hz]",     self.y_min,    1, 0)
        self.ymax_ent = _mk_entry(pg, "Y max [Hz]",     self.y_max,    1, 2)
        self.xmin_ent = _mk_entry(pg, "X min [s]",      self.x_min,    2, 0)
        self.xmax_ent = _mk_entry(pg, "X max [s]",      self.x_max,    2, 2)
        self.cmin_ent = _mk_entry(pg, "Color min",      self.cmin,     3, 0)
        self.cmax_ent = _mk_entry(pg, "Color max",      self.cmax,     3, 2)

        # ── channel selector ─────────────────────────────────
        cf = tk.LabelFrame(main, text=" Channel ",
                           bg=BG, fg=ACCENT, font=FONT_B, bd=1, relief="solid")
        cf.pack(fill="x", pady=(0, 8))
        self.channel_var = tk.StringVar(value="all")
        cr = tk.Frame(cf, bg=BG)
        cr.pack(padx=10, pady=8, anchor="w")
        func = self.function
        ch_opts = ([("All","all"),("X","x"),("Y","y"),("Z","z")]
                   if func == "mag"
                   else [("All","all"),("E","x"),("N","y"),("Z","z")])
        for text, val in ch_opts:
            tk.Radiobutton(cr, text=text, variable=self.channel_var, value=val,
                           bg=BG, fg=FG, selectcolor=BG2, activebackground=BG,
                           activeforeground=ACCENT, font=FONT_B).pack(side="left", padx=10)

        # ── buttons ──────────────────────────────────────────
        bf = tk.Frame(main, bg=BG)
        bf.pack(pady=8)
        tk.Button(bf, text="  Plot  ", command=self._plot,
                  bg=ACCENT, fg=BG, font=FONT_H, relief="flat",
                  activebackground="#00e0b5", cursor="hand2",
                  padx=14, pady=6).pack(side="left", padx=8)
        tk.Button(bf, text="Reset", command=self._reset,
                  bg=BG2, fg=FG2, font=FONT_B, relief="flat", cursor="hand2",
                  padx=10).pack(side="left", padx=8)

    def _reset(self):
        for ent, val in [
            (self.fft_ent,  self.fft_len), (self.ovlp_ent, self.overlap),
            (self.ymin_ent, self.y_min),   (self.ymax_ent, self.y_max),
            (self.xmin_ent, self.x_min),   (self.xmax_ent, self.x_max),
            (self.cmin_ent, self.cmin),    (self.cmax_ent, self.cmax),
        ]:
            ent.delete(0, "end")
            if val is not None:
                ent.insert(0, str(val))

    def _plot(self):
        try:
            fft  = _float_or_none(self.fft_ent.get())  or self.fft_len
            ovlp = _float_or_none(self.ovlp_ent.get()) or self.overlap
            ymin = _float_or_none(self.ymin_ent.get())
            ymax = _float_or_none(self.ymax_ent.get())
            xmin = _float_or_none(self.xmin_ent.get())
            xmax = _float_or_none(self.xmax_ent.get())
            cmin = _float_or_none(self.cmin_ent.get())
            cmax = _float_or_none(self.cmax_ent.get())
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc), parent=self)
            return

        channel = self.channel_var.get()
        func    = self.function
        sr      = self.sr

        # Capture arrays by value
        x_arr = np.asarray(self.x)
        y_arr = np.asarray(self.y)
        z_arr = np.asarray(self.z)

        sensor_key = "seis" if func in ("seis", "mini") else "mag"
        channel_titles = {
            "seis": {"x": "E Direction", "y": "N Direction", "z": "Z Direction"},
            "mag":  {"x": "X Direction", "y": "Y Direction", "z": "Z Direction"}}
        cbar_units_map = {
            "seis": "Intensity [ms⁻¹/√Hz]",
            "mag":  "Intensity [T/√Hz]"}
        cbar_units = cbar_units_map[sensor_key]

        def _compute_spec(data, ch_key):
            """Worker: returns (f, t, Sxx, ch_key)."""
            warnings.simplefilter('ignore')
            f, t, Sxx = signal.spectrogram(
                data, sr, window='hamming',
                nperseg=round(sr * fft),
                noverlap=round(sr * (ovlp * 0.01)))
            return f, t, Sxx, ch_key

        def _plot_spec(result):
            """Main thread: draws one spectrogram figure."""
            f, t, Sxx, ch_key = result
            title = channel_titles[sensor_key].get(ch_key, "Channel")
            _xmin = xmin if (xmin is not None and xmin >= t[0]) else t[0]
            _xmax = xmax if (xmax is not None and xmax <= t[-1]) else t[-1]

            fig = plt.figure(figsize=(20, 8))
            gs  = gridspec.GridSpec(1, 1)
            ax1 = fig.add_subplot(gs[0, 0])
            m0  = ax1.pcolormesh(t, f, np.sqrt(Sxx), shading='gouraud', vmin=cmin, vmax=cmax)
            ax1.set_title('FFT: '    + str(fft)  + "s",  fontsize=15, loc="left",  style='italic')
            ax1.set_title("Overlap: "+ str(ovlp) + "%",  fontsize=15, loc="right", style='italic')
            ax1.set_title(title, fontweight='bold', fontsize=25)
            ax1.set_xlabel('Time [s]',       fontweight='bold', fontsize=20)
            ax1.set_ylabel('Frequency [Hz]', fontweight='bold', fontsize=20)
            ax1.tick_params(labelsize=16)
            cbar = fig.colorbar(m0, pad=0.02)
            cbar.ax.tick_params(labelsize=16)
            cbar.set_label(label=cbar_units, weight='bold', fontsize=16)
            cbar.ax.yaxis.offsetText.set_fontsize(14)
            ax1.set_ylim(ymin, ymax)
            ax1.set_xlim(_xmin, _xmax)
            fig.tight_layout()
            plt.show()

        if channel == "all":
            to_plot = [("x", x_arr), ("y", y_arr), ("z", z_arr)]
        else:
            data_map = {"x": x_arr, "y": y_arr, "z": z_arr}
            to_plot  = [(channel, data_map[channel])]

        for ch_key, data in to_plot:
            # Default-arg captures so each iteration is independent
            def _make_compute(data=data, ch_key=ch_key):
                def _compute():
                    return _compute_spec(data, ch_key)
                return _compute

            self._compute_then_plot(_make_compute(), _plot_spec)




'''##########################################################################################################################'''
'''##########################################################################################################################'''

                            #######   ###   #  ##    #    #######  #####  ##    #  #    #
                            #  #  #  #   #     # #   #    #  #  #  #      # #   #  #    #
                            #  #  #  #####  #  #  #  #    #  #  #  ####   #  #  #  #    #
                            #  #  #  #   #  #  #   # #    #  #  #  #      #   # #  #    #
                            #     #  #   #  #  #    ##    #     #  #####  #    ##   ####

'''##########################################################################################################################'''
'''##########################################################################################################################'''


if __name__ == "__main__":
    app = CEAnalysisApp()
    app.mainloop()
