#!/usr/bin/env python
"""
Analyze the audio file and assuming that it is speech, look for the pauses between
sentences and and identify the segments.

Based on https://gist.github.com/rudolfbyker/8fc0d99ecadad0204813d97fee2c6c06
"""

import os
import threading
import queue

from scipy.io import wavfile
import numpy as np
from pydub import AudioSegment
from SWAP.mediacache import MediaCache
import pickle

# AnalyzerSettings = namedtuple('AnalyzerSettings','window_duration silence_threshold step_duration')
# short = AnalyzerSettings(0.2, 1e-5,  0.2)
# medium = AnalyzerSettings(0.4, 1e-6,  0.2)
# long = AnalyzerSettings(0.5, 1e-6,  0.2)

class AnalyzerProfile:
    def __init__(self, name, window_duration, silence_threshold, step_duration):
        self.name = name
        self.window_duration = window_duration
        self.silence_threshold = silence_threshold
        self.step_duration = step_duration

    def __str__(self):
        return self.name


class SegmentsAnalyzer:
    SHORT = 'short'
    STANDARD = 'standard'
    LONG = 'long'

    def __init__(self):

        self.analyzer_profiles = {
            SegmentsAnalyzer.SHORT :  AnalyzerProfile(SegmentsAnalyzer.SHORT, 0.15, 1e-5,  0.15),
            SegmentsAnalyzer.STANDARD: AnalyzerProfile(SegmentsAnalyzer.STANDARD, 0.4, 1e-6,  0.3),
            SegmentsAnalyzer.LONG: AnalyzerProfile(SegmentsAnalyzer.LONG, 0.5, 1e-6,  0.2)
        }
        self.analyzer_profile = self.analyzer_profiles[SegmentsAnalyzer.STANDARD]


        self.progress_callback = None
        self.completed_callback = None
        self.wave_cache = MediaCache("wav")
        self.segments_cache = MediaCache("seg")

        self._abandon_processing = threading.Event()
        self._queue = queue.Queue()
        self._thread = threading.Thread(
                target=self._process_queue,
                args=(self._queue, self._abandon_processing),
                daemon=True,
                name="SegmentsAnalyzer")
        self._thread.start()

    def set_analyzer_profile(self, analyzer_profile):
        if analyzer_profile in self.analyzer_profiles:
            self.analyzer_profile = self.analyzer_profiles[analyzer_profile]


    def process(self, media_file):
        #
        # Tell the SegmentsAnalyzer daemon to stop what ever it may currently be processing,
        # then queue the this item
        #
        self._abandon_processing.set()

        #
        # if the segments exist in the cache, then use them
        #
        seg_file = os.path.join(media_file, self.analyzer_profile.name)
        if self.segments_cache.is_file_in_cache(seg_file):
            cfn = self.segments_cache.get_file_cache_name(seg_file)
            segments = pickle.load( open( cfn, "rb" ) )
            if self.progress_callback is not None:
                self.progress_callback(0.0)
            if self.completed_callback is not None:
                self.completed_callback(segments)
            return

        #
        # The file isn't in the cache, so will need to process the mp3 to create it
        #
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
        # Convert the file to WAV format if there isn't already a copy in the cache
        #
        cfn = self.wave_cache.get_file_cache_name(file_name)
        _work_wave_convert_time = 0
        if not self.wave_cache.is_file_in_cache(file_name):
            _work_wave_convert_time = 20.0
            if self.progress_callback is not None:
                self.progress_callback(_work_wave_convert_time)
            AudioSegment.from_file(file_name).export(cfn, format="wav")
            self.wave_cache.add_file(file_name)
            if _abandon_processing.is_set():
                return

        #
        # Analyse the wave file
        #
        sample_rate, samples = wavfile.read(filename=cfn, mmap=True)
        max_amplitude = np.iinfo(samples.dtype).max
        max_energy = SegmentsAnalyzer._energy([max_amplitude])

        window_size = int(self.analyzer_profile.window_duration * sample_rate)
        step_size = int(self.analyzer_profile.step_duration * sample_rate)

        signal_windows = SegmentsAnalyzer._windows(
            signal=samples,
            window_size=window_size,
            step_size=step_size
        )

        work_progress_units = 1 + (int(int(len(samples) / float(step_size)) / (100.0 - _work_wave_convert_time)))
        pct_complete = _work_wave_convert_time
        window_energy = []
        for i, w in enumerate(signal_windows):
            window_energy.append(SegmentsAnalyzer._energy(w) / max_energy)
            #
            # Check if we should stop
            #
            if _abandon_processing.is_set():
                return
            #
            # Report progress
            #
            if (i % work_progress_units) == 0:
                pct_complete += 1
                if self.progress_callback is not None:
                    self.progress_callback(pct_complete)

        window_silence = (e > self.analyzer_profile.silence_threshold for e in window_energy)
        frames = []
        for r in SegmentsAnalyzer._rising_edges(window_silence):
            frames.append(r * self.analyzer_profile.step_duration)

        # Add frame for the end of the file
        frames.append(len(window_energy) * self.analyzer_profile.step_duration)

        if self.progress_callback is not None:
            self.progress_callback(0.0)

        if self.completed_callback is not None:
            self.completed_callback(frames)

        # store the frames in the cache
        seg_file = os.path.join(file_name, self.analyzer_profile.name)
        cache_seg_file = self.segments_cache.get_file_cache_name(seg_file)
        pickle.dump(frames, open(cache_seg_file, "wb"))
        self.segments_cache.add_file(seg_file)


if __name__ ==  "__main__":
    import time

    def callback(f):
        print("Found {} frames".format(len(f)))

    sa = SegmentsAnalyzer()
    sa.completed_callback = callback
    sa.process("sample.mp3")
    time.sleep(100)

