import math
import random
from dataclasses import dataclass
import config as cfg

@dataclass
class Flare:
	x: float
	alt: float
	vx: float
	vy: float
	life: float

class Aircraft:
	def __init__(self, screen_width=cfg.SCREEN_WIDTH):
		self.screen_width = screen_width
		self.preset_name = "F-16 Viper"
		self.apply_preset(self.preset_name)
		self.reset()

	def apply_preset(self, preset_name):
		self.preset_name = preset_name
		stats = cfg.AIRCRAFT_PRESETS.get(preset_name, cfg.AIRCRAFT_PRESETS["F-16 Viper"])
		self.max_hp = stats["max_hp"]
		self.speed_mult = stats["speed_mult"]
		self.pitch_speed = stats["pitch_speed"]
		self.missile_cd = stats["missile_cd"]
		self.bomb_cd = stats["bomb_cd"]
		self.regen_rate = stats.get("regen_rate", 0.0)
		self.stealth = stats.get("stealth", 0.0)
		self.special_type = stats.get("special", "OVERDRIVE")
		self.special_max_cd = stats.get("special_cd", 6.0)
		self.body_color = stats["color"]
		self.accent_color = stats["accent"]

	def set_screen_width(self, width):
		self.screen_width = width
		self.x = width * cfg.PLANE_X_RATIO

	def reset(self):
		self.x = self.screen_width * cfg.PLANE_X_RATIO
		self.altitude = 0.0
		self.speed = 0.0
		self.throttle = 0.0
		self.pitch = 0.0
		self.roll_angle = 0.0
		self.bank = 0.0
		self.g_force = 1.0
		self.reentry_heat = 0.0
		self.overdrive_timer = 0.0
		self.damage_smoke_timer = 0.0
		self.contrail_timer = 0.0
		self.vertical_speed = 0.0
		self.hp = self.max_hp
		self.crashed = False
		self.crash_reason = ""
		self.gear_down = True
		self.gear_progress = 1.0
		self.flares = []
		self.flare_cooldown = 0.0
		self.carrier_event = False
		self.on_carrier = False

	@property
	def hp_ratio(self):
		return self.hp / max(1, self.max_hp)

	def toggle_gear(self):
		if self.altitude > 2 or not self.gear_down:
			self.gear_down = not self.gear_down

	def deploy_flares(self):
		if self.flare_cooldown > 0 or self.altitude <= 5:
			return
		spreads = [(-45, -30), (-60, -10), (-35, -45), (-65, -25)]
		for vx_off, vy_off in spreads[:cfg.FLARE_BURST_COUNT]:
			self.flares.append(Flare(
				x=self.x - 22,
				alt=self.altitude - 5,
				vx=vx_off + random.uniform(-10, 10),
				vy=vy_off + random.uniform(-10, 10),
				life=cfg.FLARE_LIFETIME
			))
		self.flare_cooldown = cfg.FLARE_COOLDOWN

	def take_damage(self, amount, reason="SHOT DOWN!"):
		if self.crashed:
			return
		self.hp = max(0, self.hp - amount)
		self.roll_angle += random.choice((-22.0, 22.0))
		if self.hp == 0:
			self.crashed = True
			self.crash_reason = reason

	def update(self, keys, pad=None, dt=0.016, weather="CLEAR DAY", carrier=None):
		self.carrier_event = False
		if self.flare_cooldown > 0:
			self.flare_cooldown = max(0.0, self.flare_cooldown - dt)
		if self.overdrive_timer > 0:
			self.overdrive_timer = max(0.0, self.overdrive_timer - dt)

		if self.gear_down and self.gear_progress < 1.0:
			self.gear_progress = min(1.0, self.gear_progress + cfg.GEAR_SPEED * dt)
		elif not self.gear_down and self.gear_progress > 0.0:
			self.gear_progress = max(0.0, self.gear_progress - cfg.GEAR_SPEED * dt)

		if self.crashed:
			return 0.0

		pad = pad or {}

		# Stationary on Carrier Deck: Continuous repair + Catapult Launch on Throttle Up [D]
		if self.on_carrier and carrier is not None:
			self.altitude = carrier["deck_alt"]
			self.vertical_speed = 0.0
			self.pitch = 0.0
			self.roll_angle = 0.0
			self.bank = 0.0
			self.speed = 0.0
			self.hp = min(float(self.max_hp), self.hp + 15.0 * dt)

			if 'd' in keys or 'right' in keys or pad.get("throttle_up") or pad.get("throttle_axis", 0.0) > 0.3:
				self.throttle = min(100.0, self.throttle + cfg.THROTTLE_RATE * 1.5 * dt)
			elif 'a' in keys or 'left' in keys or pad.get("throttle_down"):
				self.throttle = max(0.0, self.throttle - cfg.THROTTLE_RATE * dt)

			# Catapult Launch when throttle exceeds 55%
			if self.throttle >= 55.0:
				self.on_carrier = False
				self.speed = 240.0
				self.pitch = 14.0
				self.altitude = carrier["deck_alt"] + 3.0
			return 0.0

		if self.regen_rate > 0 and self.hp < self.max_hp:
			self.hp = min(float(self.max_hp), self.hp + self.regen_rate * dt)

		throttle_input = 0.0
		if 'd' in keys or 'right' in keys or pad.get("throttle_up"):
			throttle_input = 1.0
		elif 'a' in keys or 'left' in keys or pad.get("throttle_down"):
			throttle_input = -1.0
		elif abs(pad.get("throttle_axis", 0.0)) > 0.0:
			throttle_input = pad["throttle_axis"]

		if throttle_input != 0.0:
			self.throttle = max(0.0, min(100.0, self.throttle + throttle_input * cfg.THROTTLE_RATE * dt))

		pitch_input = 0.0
		if 'w' in keys or 'up' in keys:
			pitch_input = 1.0
		elif 's' in keys or 'down' in keys:
			pitch_input = -1.0
		elif abs(pad.get("pitch_axis", 0.0)) > 0.0:
			pitch_input = pad["pitch_axis"]

		agility_mult = 0.75 + 0.25 * self.hp_ratio
		prev_pitch = self.pitch

		if pitch_input != 0.0:
			min_pitch = 0.0 if self.altitude <= 1 else -cfg.MAX_PITCH
			self.pitch = max(min_pitch, min(cfg.MAX_PITCH, self.pitch + pitch_input * self.pitch_speed * agility_mult * dt))
		else:
			self.pitch *= (0.54 ** dt)

		target_roll = (pitch_input * 62.0) if self.altitude > 6 else 0.0
		roll_rate = 1.0 - math.exp(-7.5 * dt)
		self.roll_angle += (target_roll - self.roll_angle) * roll_rate
		self.bank = max(-1.0, min(1.0, self.roll_angle / 62.0))

		pitch_rate_rad = math.radians((self.pitch - prev_pitch) / max(0.001, dt))
		centripetal_g = (self.speed * 0.514 * pitch_rate_rad) / 9.8
		self.g_force = max(-3.0, min(9.5, math.cos(math.radians(self.pitch)) + centripetal_g))

		air_density = max(0.0, 1.0 - (self.altitude / cfg.ZERO_AIR_ALT))

		engine_health_mult = 0.82 + 0.18 * self.hp_ratio
		gear_drag = cfg.GEAR_DRAG_FACTOR if self.gear_progress > 0.5 else 1.0
		if self.throttle <= 15.0:
			raw_speed = (self.throttle / 15.0) * (cfg.BASE_CRUISE_SPEED * 0.6)
		else:
			norm_t = (self.throttle - 15.0) / 85.0
			raw_speed = cfg.BASE_CRUISE_SPEED + (norm_t * 100.0 * self.speed_mult * engine_health_mult)

		overdrive_bonus = 145.0 if self.overdrive_timer > 0 else 0.0
		target_speed = (raw_speed + overdrive_bonus) * gear_drag
		gravity_speed_effect = -math.sin(math.radians(self.pitch)) * 35.0
		accel_factor = 1.0 - math.exp(-2.3 * dt)
		self.speed += ((target_speed + gravity_speed_effect) - self.speed) * accel_factor
		self.speed = max(0.0, self.speed)

		lift = (self.speed / cfg.STALL_SPEED) * math.sin(math.radians(self.pitch + 3)) * cfg.LIFT_POWER * air_density

		if self.altitude <= 0 and lift <= cfg.GRAVITY:
			self.altitude = 0.0
			self.vertical_speed = 0.0
			if self.pitch < 0:
				self.pitch = 0.0
		else:
			self.vertical_speed = (lift - cfg.GRAVITY) * 4.0
			if 1100.0 < self.altitude < 2400.0 and self.speed > 180.0:
				self.vertical_speed += math.sin(self.x + self.altitude * 0.07) * 4.5
			if weather == "THUNDERSTORM" and self.altitude < 1500.0 and self.speed > 90.0:
				self.vertical_speed += math.sin(self.x * 0.04 + self.altitude * 0.09) * 7.5
			if self.speed < cfg.STALL_SPEED and self.altitude > 0 and air_density > 0.2:
				self.vertical_speed -= (cfg.STALL_SPEED - self.speed) * 0.45
				self.pitch = max(-45.0, self.pitch - 45.0 * dt)
			self.altitude += self.vertical_speed * dt

		if 1300.0 < self.altitude < 2700.0 and self.pitch < -22.0 and self.speed > 310.0:
			self.reentry_heat = min(1.0, self.reentry_heat + 1.8 * dt)
		else:
			self.reentry_heat = max(0.0, self.reentry_heat - 1.4 * dt)

		# Carrier Approach Glide-Slope Assist (stabilizes sink & pitch when gear is down near deck)
		if carrier is not None and not carrier["serviced"] and self.gear_progress > 0.8:
			dist_to_center = carrier["x"] - self.x
			if -carrier["half_w"] <= dist_to_center <= carrier["half_w"] + 550.0 and self.altitude < 150.0:
				if self.vertical_speed < -14.0:
					self.vertical_speed += ( -14.0 - self.vertical_speed ) * (1.0 - math.exp(-6.0 * dt))
				if abs(self.pitch) > 12.0:
					self.pitch *= (0.15 ** dt)

		# Aircraft Carrier Deck Arresting Hook Check (forgiving 720px Supercarrier deck)
		if carrier is not None and abs(self.x - carrier["x"]) <= carrier["half_w"] + 25.0:
			deck_alt = carrier["deck_alt"]
			if self.altitude <= deck_alt + 6.0 and self.vertical_speed <= 4.0:
				if self.gear_progress < 0.75:
					self.crashed = True
					self.crash_reason = "CARRIER DECK CRASH! DEPLOY GEAR [G]"
				elif self.vertical_speed < cfg.MAX_SAFE_VSPEED - 14.0:
					self.crashed = True
					self.crash_reason = "HARD CARRIER IMPACT! FLARE NOSE UP"
				elif abs(self.pitch) > cfg.MAX_SAFE_PITCH + 8.0:
					self.crashed = True
					self.crash_reason = "CARRIER TAIL STRIKE! LEVEL PITCH"
				else:
					self.altitude = deck_alt
					self.vertical_speed = 0.0
					self.pitch = 0.0
					self.speed = 0.0
					self.throttle = 0.0
					self.on_carrier = True
					if not carrier["serviced"]:
						carrier["serviced"] = True
						self.hp = min(float(self.max_hp), self.hp + 60.0)
						self.flare_cooldown = 0.0
						self.carrier_event = True

		if self.altitude < 0:
			if carrier is not None and abs(self.x - carrier["x"]) <= carrier["half_w"] + 450:
				self.crashed = True
				self.crash_reason = "DITCHED AT SEA! MISSED CARRIER DECK"
			elif self.gear_progress < 0.9:
				self.crashed = True
				self.crash_reason = "BELLY LANDING! DEPLOY GEAR [G]"
			elif self.vertical_speed < cfg.MAX_SAFE_VSPEED:
				self.crashed = True
				self.crash_reason = "HARD LANDING! DESCENT TOO FAST"
			elif abs(self.pitch) > cfg.MAX_SAFE_PITCH:
				self.crashed = True
				self.crash_reason = "TAIL/NOSE STRIKE! LEVEL PITCH"
			self.altitude = 0.0
			self.vertical_speed = 0.0

		horizontal_speed = self.speed * math.cos(math.radians(self.pitch))
		dx = horizontal_speed * cfg.HORIZ_SPEED_SCALE * dt

		for f in self.flares[:]:
			f.x += (f.vx * cfg.HORIZ_SPEED_SCALE * dt) - dx
			f.alt += f.vy * dt
			f.life -= dt
			if f.life <= 0 or f.alt <= 0:
				self.flares.remove(f)

		return dx
