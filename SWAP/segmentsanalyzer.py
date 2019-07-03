#!/usr/bin/env python
"""
Analysise the audio file and assuming that it is speech, look for the pauses between
sentences and and identify the segments.

Based on https://gist.github.com/rudolfbyker/8fc0d99ecadad0204813d97fee2c6c06
"""

import os
import tempfile
import threading
import queue

from scipy.io import wavfile
import numpy as np
from pydub import AudioSegment


class SegmentsAnalyzer:
    def __init__(self):
        self.window_duration = 0.6
        self.silence_threshold = 1e-6
        self.step_duration = 0.2

        self.progress_callback = None
        self.completed_callback = None

        self._abandon_processing = threading.Event()
        self._queue = queue.Queue()
        self._thread = threading.Thread(
                target=self._process_queue,
                args=(self._queue, self._abandon_processing),
                daemon=True,
                name="SegmentsAnalyzer")
        self._thread.start()

    def process(self, media_file):
        #
        # Tell the SegmentsAnalyzer daemon to stop what ever it may currently be processing,
        # then queue the this item
        #
        self._abandon_processing.set()
        self._queue.put(media_file)

    @staticmethod
    def _windows(signal, window_size, step_size):
        if type(window_size) is not int:
            raise AttributeError("Window size must be an integer.")
        if type(step_size) is not int:
            raise AttributeError("Step size must be an integer.")
        for i_start in range(0, len(signal), step_size):
            i_end = i_start + window_size
            if i_end >= len(signal):
                break
            yield signal[i_start:i_end]

    @staticmethod
    def _energy(samples):
        return np.sum(np.power(samples, 2.)) / float(len(samples))

    @staticmethod
    def _rising_edges(binary_signal):
        previous_value = 0
        index = 0
        for x in binary_signal:
            if x and not previous_value:
                yield index
            previous_value = x
            index += 1

    def _process_queue(self, pqueue, _abandon_processing):
        while True:
            file_name = pqueue.get(block=True, timeout=None)
            _abandon_processing.clear()
            self._compute_segments(file_name, _abandon_processing)

    #
    # Take an audio file and look for windows of window_silence level of power of window_duration seconds,
    # and when a window is found, skip forward step_duration
    #
    def _compute_segments(self, file_name, _abandon_processing):
        #
        # Convert the file to WAV format
        #
        _work_wave_convert_time = 20.0
        if self.progress_callback is not None:
            self.progress_callback(_work_wave_convert_time)

        temp_file_name = next(tempfile._get_candidate_names())  # noqa
        tmp_wave_file = os.path.join(tempfile.mkdtemp(), temp_file_name)
        AudioSegment.from_file(file_name).export(tmp_wave_file, format="wav")
        if _abandon_processing.is_set():
            os.remove(tmp_wave_file)
            return

        #
        # Load the wav file
        #
        sample_rate, samples = wavfile.read(filename=tmp_wave_file, mmap=True)
        max_amplitude = np.iinfo(samples.dtype).max
        max_energy = SegmentsAnalyzer._energy([max_amplitude])

        window_size = int(self.window_duration * sample_rate)
        step_size = int(self.step_duration * sample_rate)

        signal_windows = SegmentsAnalyzer._windows(
            signal=samples,
            window_size=window_size,
            step_size=step_size
        )

        work_progress_units = int(int(len(samples) / float(step_size)) / (100.0 - _work_wave_convert_time))
        pct_complete = _work_wave_convert_time
        window_energy = []
        for i, w in enumerate(signal_windows):
            window_energy.append(SegmentsAnalyzer._energy(w) / max_energy)
            #
            # Check if we should stop
            #
            if _abandon_processing.is_set():
                os.remove(tmp_wave_file)
                return
            #
            # Report progress
            #
            if (i % work_progress_units) == 0:
                pct_complete += 1
                if self.progress_callback is not None:
                    self.progress_callback(pct_complete)

        window_silence = (e > self.silence_threshold for e in window_energy)
        frames = []
        for r in SegmentsAnalyzer._rising_edges(window_silence):
            frames.append(r * self.step_duration)

        # Add frame for the end of the file
        frames.append(len(window_energy) * self.step_duration)

        if self.progress_callback is not None:
            self.progress_callback(0.0)
        os.remove(tmp_wave_file)

        if self.completed_callback is not None:
            self.completed_callback(frames)


if __name__ ==  "__main__":
    import time

    def callback(f):
        print("Found {} frames".format(len(f)))

    sa = SegmentsAnalyzer()
    sa.completed_callback = callback
    sa.process("sample.mp3")
    time.sleep(100)

