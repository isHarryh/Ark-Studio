# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import time
import wave
import simpleaudio
from io import BytesIO


class AudioComposer:
    """Audio composer."""

    __instance:"AudioComposer" = None

    def __init__(self):
        """Not recommended to use. Please use the singleton instance."""
        self._tracks:"dict[int,AudioTrack]" = {}

    @staticmethod
    def load(track:"AudioTrack", track_id:int=0):
        """Loads the given track to the specified track id.
        If the track id is existed, it will be overwritten without disposing."""
        if not AudioComposer.__instance:
            AudioComposer.__instance = AudioComposer()
        return AudioComposer.__instance._load(track, track_id)

    @staticmethod
    def dispose(track_id:int):
        """Disposes the specified track id."""
        if not AudioComposer.__instance:
            AudioComposer.__instance = AudioComposer()
        return AudioComposer.__instance._dispose(track_id)

    def _load(self, track:"AudioTrack", track_id:int=0):
        if track_id in self._tracks:
            self._tracks[track_id].stop()
        self._tracks[track_id] = track
        return track

    def _dispose(self, track_id:int):
        if track_id in self._tracks:
            self._tracks[track_id].dispose()
            del self._tracks[track_id]


class AudioTrack:
    """Track session that controls the audio to be played."""

    def __init__(self, audio_data:bytes):
        """Initializes the audio track session with the given audio data bytes."""
        wave_read = wave.open(BytesIO(audio_data))
        wave_obj = simpleaudio.WaveObject.from_wave_read(wave_read)
        self._wave_obj = wave_obj
        self._play_obj = None
        self._play_start_time = None

    def _sec_to_idx(self, sec:float):
        if sec is None:
            return None
        idx = sec * self.bytes_per_second
        idx = idx // self.bytes_per_sample // self.channels
        idx = idx * self.bytes_per_sample * self.channels
        return int(min(idx, self.size) if idx >= 0 else max(-self.size, idx))

    def play(self, begin:float=None, end:float=None):
        """Starts playing. This will stops previous playing on this track first."""
        if not self._wave_obj:
            raise RuntimeError("Nothings is playable")
        begin_idx = self._sec_to_idx(begin)
        end_idx = self._sec_to_idx(end)
        data = self._wave_obj.audio_data
        if begin_idx is not None:
            data = data[begin_idx:]
        if end_idx is not None:
            data = data[:end_idx]
        if len(data) > 0:
            self._play_start_time = time.time() - begin
            self._play_obj = simpleaudio.play_buffer(data, self.channels, self.bytes_per_sample, self.sample_rate)

    def stop(self):
        """Stops playing."""
        if self._play_obj:
            self._play_obj.stop()
        self._play_obj = None
        self._play_start_time = None

    def dispose(self):
        """Releases resources."""
        self.stop()
        self._wave_obj = None

    def is_playing(self):
        """Returns `True` if the audio is playing now."""
        if self._play_obj:
            return self._play_obj.is_playing()
        return False

    def get_playing_duration(self):
        """Returns the current playing duration in seconds. Not accurate."""
        if self._play_start_time:
            return time.time() - self._play_start_time
        return 0.0

    @property
    def bytes_per_sample(self):
        """Audio's bytes per sample."""
        return self._wave_obj.bytes_per_sample

    @property
    def bytes_per_second(self):
        """Audio's bytes per second."""
        return self.bytes_per_sample * self.channels * self.sample_rate

    @property
    def channels(self):
        """Audio's number of channels."""
        return self._wave_obj.num_channels

    @property
    def duration(self, ndigits:int=3):
        """Audio's duration in seconds."""
        return round(self.size / self.bytes_per_second, ndigits)

    @property
    def sample_rate(self):
        """Audio's sample rate."""
        return self._wave_obj.sample_rate

    @property
    def size(self):
        """Audio's data size in bytes."""
        return len(self._wave_obj.audio_data)
