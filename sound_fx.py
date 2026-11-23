import ctypes
import math
import os
import queue
import random
import struct
import threading
import time
import wave

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx_cache")

class SoundFX:
	def __init__(self):
		self.muted = False
		self.sound_paths = {}
		self.last_played = {}
		self.sample_rate = 22050
		self.cmd_queue = queue.Queue(maxsize=24)
		self.winmm = getattr(ctypes, "windll", None)
		if self.winmm is not None:
			self.winmm = self.winmm.winmm
			self._build_sound_bank()
			t = threading.Thread(target=self._audio_worker, daemon=True)
			t.start()

	def toggle_mute(self):
		self.muted = not self.muted

	def _write_wav(self, name, duration, sample_fn):
		os.makedirs(CACHE_DIR, exist_ok=True)
		filepath = os.path.join(CACHE_DIR, f"{name}.wav")
		self.sound_paths[name] = filepath

		# Skip rewriting if already cached, and safely ignore Windows MCI file locks
		if os.path.exists(filepath) and os.path.getsize(filepath) > 44:
			return

		num_samples = int(self.sample_rate * duration)
		try:
			with wave.open(filepath, "wb") as wf:
				wf.setnchannels(1)
				wf.setsampwidth(2)
				wf.setframerate(self.sample_rate)
				frames = bytearray()
				for i in range(num_samples):
					t = i / self.sample_rate
					env = 1.0
					if i < 180:
						env = i / 180.0
					elif num_samples - i < 220:
						env = (num_samples - i) / 220.0
					val = max(-1.0, min(1.0, sample_fn(t, duration) * env))
					frames.extend(struct.pack("<h", int(val * 24000)))
				wf.writeframes(bytes(frames))
		except PermissionError:
			pass

	def _build_sound_bank(self):
		self._write_wav(
			"vulcan", 0.055,
			lambda t, d: (0.45 * math.sin(2 * math.pi * (160 - 90 * (t / d)) * t) +
						  0.25 * random.uniform(-1, 1)) * (1.0 - t / d)
		)
		self._write_wav(
			"missile", 0.26,
			lambda t, d: (0.30 * math.sin(2 * math.pi * (320 + 680 * (t / d)) * t) +
						  0.35 * random.uniform(-1, 1) * (0.4 + 0.6 * (t / d))) * (1.0 - 0.5 * (t / d))
		)
		self._write_wav(
			"bomb", 0.24,
			lambda t, d: 0.35 * math.sin(2 * math.pi * (620 - 380 * (t / d)) * t) * (1.0 - 0.4 * (t / d))
		)
		self._write_wav(
			"flare", 0.14,
			lambda t, d: (0.35 * math.sin(2 * math.pi * (1150 + 450 * math.sin(40 * t)) * t) +
						  0.20 * random.uniform(-1, 1)) * (1.0 - t / d)
		)

		low_state = 0.0
		def explosion_fn(t, d):
			nonlocal low_state
			noise = random.uniform(-1, 1)
			low_state = 0.88 * low_state + 0.12 * noise
			boom = 0.65 * math.sin(2 * math.pi * (95 - 55 * (t / d)) * t)
			return (boom + 1.4 * low_state) * ((1.0 - t / d) ** 1.4)

		self._write_wav("explosion", 0.38, explosion_fn)

		self._write_wav(
			"warning", 0.12,
			lambda t, d: 0.32 * math.sin(2 * math.pi * (1050 if t < 0.055 else 1320) * t)
		)

		def chime_fn(t, d):
			freq = 523.25 if t < 0.09 else (659.25 if t < 0.18 else 783.99)
			return 0.35 * math.sin(2 * math.pi * freq * t) * (1.0 - 0.4 * (t / d))

		self._write_wav("wave_clear", 0.30, chime_fn)

		self._write_wav(
			"damage", 0.18,
			lambda t, d: (0.50 * math.sin(2 * math.pi * 110 * t) +
						  0.40 * random.uniform(-1, 1)) * (1.0 - t / d)
		)

	def _audio_worker(self):
		pool_sizes = {
			"vulcan": 3,
			"missile": 2,
			"bomb": 2,
			"flare": 2,
			"explosion": 3,
			"warning": 1,
			"wave_clear": 1,
			"damage": 2,
		}
		pools = {}
		indices = {}

		for name, count in pool_sizes.items():
			filepath = self.sound_paths.get(name)
			if not filepath or not os.path.exists(filepath):
				continue
			aliases = []
			for i in range(count):
				alias = f"sf_{name}_{i}"
				self.winmm.mciSendStringW(f'open "{filepath}" type waveaudio alias {alias}', None, 0, None)
				aliases.append(alias)
			pools[name] = aliases
			indices[name] = 0

		while True:
			effect = self.cmd_queue.get()
			if self.muted or effect not in pools:
				continue
			aliases = pools[effect]
			idx = indices[effect]
			alias = aliases[idx]
			indices[effect] = (idx + 1) % len(aliases)
			self.winmm.mciSendStringW(f"play {alias} from 0", None, 0, None)

	def play(self, effect):
		if self.muted or self.winmm is None or effect not in self.sound_paths:
			return

		now = time.perf_counter()
		min_gap = 0.07 if effect == "vulcan" else 0.04
		if now - self.last_played.get(effect, 0.0) < min_gap:
			return

		self.last_played[effect] = now
		try:
			self.cmd_queue.put_nowait(effect)
		except queue.Full:
			pass
