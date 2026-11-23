import ctypes
from ctypes import wintypes

class JOYINFOEX(ctypes.Structure):
	_fields_ = [
		("dwSize", wintypes.DWORD),
		("dwFlags", wintypes.DWORD),
		("dwXpos", wintypes.DWORD),
		("dwYpos", wintypes.DWORD),
		("dwZpos", wintypes.DWORD),
		("dwRpos", wintypes.DWORD),
		("dwUpos", wintypes.DWORD),
		("dwVpos", wintypes.DWORD),
		("dwButtons", wintypes.DWORD),
		("dwButtonNumber", wintypes.DWORD),
		("dwPOV", wintypes.DWORD),
		("dwReserved1", wintypes.DWORD),
		("dwReserved2", wintypes.DWORD),
	]

class GamepadController:
	def __init__(self, joy_id=0):
		self.joy_id = joy_id
		self.connected = False
		self.prev_buttons = 0
		self.winmm = getattr(ctypes, "windll", None)
		if self.winmm is not None:
			self.winmm = self.winmm.winmm

	def _normalize_axis(self, raw_val, deadzone=0.22):
		# Windows joystick axes range from 0 to 65535 (center = 32767.5)
		norm = (raw_val - 32767.5) / 32767.5
		if abs(norm) < deadzone:
			return 0.0
		return max(-1.0, min(1.0, norm))

	def poll(self):
		state = {
			"connected": False,
			"pitch_axis": 0.0,
			"throttle_axis": 0.0,
			"throttle_up": False,
			"throttle_down": False,
			"fire_gun": False,
			"fire_missile": False,
			"drop_bomb": False,
			"deploy_flares": False,
			"toggle_gear": False,
			"restart": False,
			"fire_special": False,
		}

		if self.winmm is None:
			return state

		info = JOYINFOEX()
		info.dwSize = ctypes.sizeof(JOYINFOEX)
		info.dwFlags = 0x000000FF  # JOY_RETURNALL

		res = self.winmm.joyGetPosEx(self.joy_id, ctypes.byref(info))
		if res != 0:
			self.connected = False
			self.prev_buttons = 0
			return state

		self.connected = True
		state["connected"] = True

		# Left Stick Y-Axis: Up = Pitch Up (+), Down = Pitch Down (-)
		ly = self._normalize_axis(info.dwYpos)
		state["pitch_axis"] = -ly

		# Left Stick X-Axis: Right = Throttle Up (+), Left = Throttle Down (-)
		lx = self._normalize_axis(info.dwXpos)
		state["throttle_axis"] = lx

		# D-Pad overrides (dwPOV is in hundredths of a degree; 65535 = centered)
		pov = info.dwPOV
		if pov != 65535:
			if pov in (0, 4500, 31500):
				state["pitch_axis"] = 1.0
			elif pov in (13500, 18000, 22500):
				state["pitch_axis"] = -1.0
			if pov in (4500, 9000, 13500):
				state["throttle_up"] = True
			elif pov in (22500, 27000, 31500):
				state["throttle_down"] = True

		# Triggers on Xbox/XInput via winmm Z-axis (LT > 38000, RT < 27000) or Shoulder Buttons
		z_norm = self._normalize_axis(info.dwZpos, deadzone=0.22)
		if z_norm < -0.1:
			state["throttle_up"] = True
		elif z_norm > 0.1:
			state["throttle_down"] = True

		btns = info.dwButtons
		just_pressed = btns & ~self.prev_buttons
		self.prev_buttons = btns

		# Button bitmasks: 1=A, 2=B, 4=X, 8=Y, 16=LB, 32=RB, 64=Back, 128=Start
		if btns & 32:
			state["throttle_up"] = True
		if btns & 1:
			state["fire_gun"] = True
		if just_pressed & 4:
			state["fire_missile"] = True
		if just_pressed & 2:
			state["drop_bomb"] = True
		if just_pressed & 8:
			state["deploy_flares"] = True
		if just_pressed & 16:
			state["toggle_gear"] = True
		if just_pressed & 64:
			state["fire_special"] = True
		if just_pressed & 128:
			state["restart"] = True

		return state
