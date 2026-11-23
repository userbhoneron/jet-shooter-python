# ================= PART 1 START =================
import math
import random
from dataclasses import dataclass
import config as cfg

@dataclass
class Cloud:
	x: float
	y: float
	size: float

@dataclass
class Star:
	x: float
	y: float
	size: int

@dataclass
class WindStreak:
	x: float
	y: float
	length: float

class GameRenderer:
	def __init__(self, canvas, width=cfg.SCREEN_WIDTH, height=cfg.SCREEN_HEIGHT):
		self.canvas = canvas
		self.width = width
		self.height = height
		self.ground_height = cfg.GROUND_HEIGHT
		self.scroll_x = 0.0
		self.radar_angle = 0.0
		self.lightning_timer = 0.0
		self.clouds = [Cloud(random.randint(0, width), random.randint(60, 420), random.randint(55, 115)) for _ in range(10)]
		self.stars = [Star(random.randint(0, width), random.randint(0, height), random.choice((1, 2, 3))) for _ in range(140)]
		self.wind_streaks = [WindStreak(random.randint(0, width), random.randint(40, height - 100), random.randint(18, 45)) for _ in range(22)]
		self.raindrops = [(random.randint(0, width), random.randint(0, height)) for _ in range(85)]
		self.mountains = [(i * 220, random.randint(75, 155)) for i in range(12)]

	def resize(self, width, height):
		if width > 100 and height > 100 and (width != self.width or height != self.height):
			self.width = width
			self.height = height
			self.stars = [Star(random.randint(0, width), random.randint(0, height), random.choice((1, 2, 3))) for _ in range(140)]
			self.wind_streaks = [WindStreak(random.randint(0, width), random.randint(40, height - 100), random.randint(18, 45)) for _ in range(22)]
			self.raindrops = [(random.randint(0, width), random.randint(0, height)) for _ in range(85)]

	def update_environment(self, dx, weather="CLEAR DAY", dt=0.016):
		self.scroll_x += dx
		self.radar_angle = (self.radar_angle + 4.5) % 360.0
		if self.lightning_timer > 0:
			self.lightning_timer = max(0.0, self.lightning_timer - dt)
		elif weather == "THUNDERSTORM" and random.random() < 0.006:
			self.lightning_timer = 0.14

		for cloud in self.clouds:
			cloud.x -= dx * 0.35
			if cloud.x < -140:
				cloud.x = self.width + 70
				cloud.y = random.randint(60, 420)

		for ws in self.wind_streaks:
			ws.x -= max(4.0, dx * 1.45)
			if ws.x < -60:
				ws.x = self.width + random.randint(20, 120)
				ws.y = random.randint(30, max(120, self.height - 90))

		if weather == "THUNDERSTORM":
			for i, (rx, ry) in enumerate(self.raindrops):
				rx -= max(8.0, dx * 0.9 + 6.0)
				ry += 18.0
				if rx < 0:
					rx += self.width
				if ry > self.height:
					ry -= self.height
				self.raindrops[i] = (rx, ry)

	def get_sky_color(self, altitude, weather="CLEAR DAY"):
		if self.lightning_timer > 0:
			return "#B8D4F0"
		if altitude >= cfg.SPACE_ALT:
			return "#040410"

		t = min(1.0, altitude / cfg.STRATOSPHERE_ALT)
		if weather == "GOLDEN SUNSET":
			r = int(235 * (1 - t) + 28 * t)
			g = int(115 * (1 - t) + 18 * t)
			b = int(65 * (1 - t) + 75 * t)
		elif weather == "NIGHT RAID":
			r = int(10 * (1 - t) + 4 * t)
			g = int(18 * (1 - t) + 6 * t)
			b = int(42 * (1 - t) + 18 * t)
		elif weather == "THUNDERSTORM":
			r = int(48 * (1 - t) + 14 * t)
			g = int(58 * (1 - t) + 22 * t)
			b = int(72 * (1 - t) + 52 * t)
		else:
			r = int(125 * (1 - t) + 12 * t)
			g = int(198 * (1 - t) + 28 * t)
			b = int(238 * (1 - t) + 118 * t)
		return f"#{r:02x}{g:02x}{b:02x}"

	def alt_to_screen_y(self, alt, camera_y_offset):
		return self.height - self.ground_height - 15 - (alt - camera_y_offset)

	def rotate_points(self, cx, cy, points, angle_deg):
		rad = math.radians(angle_deg)
		cos_a, sin_a = math.cos(rad), math.sin(rad)
		rotated = []
		for px, py in points:
			rx = cx + (px * cos_a - py * sin_a)
			ry = cy + (px * sin_a + py * cos_a)
			rotated.extend([rx, ry])
		return rotated
# ================= PART 2 START =================
	def draw_fighter_jet(self, plane, cx, cy):
		angle_deg = -plane.pitch
		bank = plane.bank
		hp_ratio = plane.hp_ratio
		name = plane.preset_name

		if plane.reentry_heat > 0.05 and not plane.crashed:
			heat_r = 28 + plane.reentry_heat * 18
			plasma_pts = [(34, -heat_r * 0.7), (58 + plane.reentry_heat * 10, 0), (34, heat_r * 0.7), (46, 0)]
			plasma_col = "#FF4500" if plane.reentry_heat < 0.6 else "#FFD700"
			self.canvas.create_polygon(self.rotate_points(cx, cy, plasma_pts, angle_deg), fill=plasma_col, outline="#FF2200", width=2)

		if plane.throttle > 8 and not plane.crashed:
			t_norm = plane.throttle / 100.0
			flame_len = 14 + (t_norm * 48) + random.randint(-4, 5)
			if name in ("X-37 Orbital Valkyrie", "ADF-01 Falken"):
				outer_col, mid_col = "#8A2BE2", "#00FFFF"
			elif name == "SR-71 Blackbird":
				outer_col, mid_col = "#FF1E56", "#FFAC41"
			else:
				outer_col = "#1E90FF" if plane.throttle > 82 else "#FF4500"
				mid_col = "#00FFFF" if plane.throttle > 82 else "#FFA500"

			outer_flame = [(-38, -4.5), (-38 - flame_len, 0), (-38, 4.5)]
			mid_flame = [(-38, -2.8), (-38 - flame_len * 0.68, 0), (-38, 2.8)]
			self.canvas.create_polygon(self.rotate_points(cx, cy, outer_flame, angle_deg), fill=outer_col, outline="")
			self.canvas.create_polygon(self.rotate_points(cx, cy, mid_flame, angle_deg), fill=mid_col, outline="")

			if plane.throttle > 70:
				for step in (0.22, 0.45, 0.68):
					dx_pos = -38 - flame_len * step
					dw = 4.5 * (1.0 - step * 0.6)
					diamond = [(dx_pos + dw, 0), (dx_pos, -dw * 0.65), (dx_pos - dw, 0), (dx_pos, dw * 0.65)]
					self.canvas.create_polygon(self.rotate_points(cx, cy, diamond, angle_deg), fill="#FFFFFF", outline="")

		if bank > 0.12 and name != "B-2 Spirit Stealth":
			far_span = 16 * bank
			far_wing = [(-20, -3), (-6, -3 - far_span), (6, -3 - far_span), (14, -3)]
			self.canvas.create_polygon(self.rotate_points(cx, cy, far_wing, angle_deg), fill="#2C353F", outline="#151A20")

		if plane.gear_progress > 0.05:
			drop = 15 * plane.gear_progress
			for gx in (22, -14):
				strut = self.rotate_points(cx, cy, [(gx, 4), (gx - 2, 4 + drop)], angle_deg)
				self.canvas.create_line(strut, fill="#D0D7DE", width=2)
				wx, wy = self.rotate_points(cx, cy, [(gx - 2, 4 + drop)], angle_deg)
				self.canvas.create_oval(wx - 4.5, wy - 4.5, wx + 4.5, wy + 4.5, fill="#111111", outline="#999999")

		damage_deform = 0.62 if hp_ratio < 0.35 else 1.0
		tail_h = (22 * damage_deform) - abs(bank) * 4
		tail_shift = bank * 3.5

		if name != "B-2 Spirit Stealth":
			if name in ("YF-23 Black Widow", "F-22 Raptor"):
				tail = [(-36, -5), (-32, -tail_h * 0.9 + tail_shift), (-20, -tail_h * 0.9 + tail_shift), (-14, -5)]
			elif name in ("F-15 Strike Eagle", "MiG-29 Fulcrum", "F/A-18 Super Hornet"):
				tail_back = [(-38, -6), (-42, -tail_h + tail_shift - 2), (-29, -tail_h + tail_shift - 2), (-18, -6)]
				self.canvas.create_polygon(self.rotate_points(cx, cy, tail_back, angle_deg), fill="#333C46", outline="#111111")
				tail = [(-33, -6), (-36, -tail_h + tail_shift), (-23, -tail_h + tail_shift), (-13, -6)]
			elif name == "X-37 Orbital Valkyrie":
				tail = [(-38, -6), (-44, -tail_h * 1.05 + tail_shift), (-30, -tail_h * 1.05 + tail_shift), (-16, -6)]
			elif name == "SR-71 Blackbird":
				tail = [(-36, -4), (-34, -tail_h * 0.78 + tail_shift), (-22, -tail_h * 0.78 + tail_shift), (-14, -4)]
			else:
				tail = [(-35, -6), (-40, -tail_h + tail_shift), (-26, -tail_h + tail_shift), (-15, -6)]

			self.canvas.create_polygon(self.rotate_points(cx, cy, tail, angle_deg), fill="#47525E", outline="#1A2026")
			if hp_ratio >= 0.35:
				tail_tip = [(-39, -tail_h + tail_shift + 3), (-40, -tail_h + tail_shift), (-26, -tail_h + tail_shift), (-25, -tail_h + tail_shift + 3)]
				self.canvas.create_polygon(self.rotate_points(cx, cy, tail_tip, angle_deg), fill=plane.accent_color, outline="")

		body_color = "#8B1A1A" if plane.crashed else plane.body_color
		if name == "B-2 Spirit Stealth":
			fuselage = [(-34, -2), (-18, -6), (12, -5), (44, 2), (10, 6), (-18, 4), (-26, 7), (-34, 2)]
			self.canvas.create_polygon(self.rotate_points(cx, cy, fuselage, angle_deg), fill=body_color, outline="#0D0F14", width=1.5)
		elif name == "SR-71 Blackbird":
			fuselage = [(-44, -3), (-34, -5), (22, -5), (62, 1), (22, 4), (-36, 4), (-44, 2)]
			self.canvas.create_polygon(self.rotate_points(cx, cy, fuselage, angle_deg), fill=body_color, outline="#FF4500", width=1)
		elif name == "A-10 Thunderbolt II":
			fuselage = [(-38, -5), (-32, -8), (16, -8), (34, -3), (44, 1), (32, 6), (-32, 6), (-38, 3)]
			self.canvas.create_polygon(self.rotate_points(cx, cy, fuselage, angle_deg), fill=body_color, outline="#181D23", width=1.5)
			pod = [(-26, -13), (-8, -13), (-6, -7), (-28, -7)]
			self.canvas.create_polygon(self.rotate_points(cx, cy, pod, angle_deg), fill="#384018", outline="#111111")
			gau8 = self.rotate_points(cx, cy, [(42, 3), (52, 4)], angle_deg)
			self.canvas.create_line(gau8, fill="#CCCCCC", width=3)
		elif name == "X-37 Orbital Valkyrie":
			fuselage = [(-38, -6), (-32, -10), (14, -10), (34, -5), (52, 2), (32, 8), (-34, 8), (-38, 5)]
			self.canvas.create_polygon(self.rotate_points(cx, cy, fuselage, angle_deg), fill="#E8EEF5", outline="#181D23", width=1.5)
			belly = [(-36, 4), (34, 4), (52, 2), (32, 8), (-34, 8)]
			self.canvas.create_polygon(self.rotate_points(cx, cy, belly, angle_deg), fill="#161B22", outline="")
		elif name in ("Su-57 Felon", "ADF-01 Falken"):
			fuselage = [(-39, -4), (-32, -7), (15, -7), (32, -3), (55, 1), (30, 5), (-33, 5), (-39, 3)]
			self.canvas.create_polygon(self.rotate_points(cx, cy, fuselage, angle_deg), fill=body_color, outline="#181D23", width=1.5)
			canard = [(14, 0), (22, 6), (28, 6), (25, 0)]
			self.canvas.create_polygon(self.rotate_points(cx, cy, canard, angle_deg), fill=plane.accent_color, outline="#111111")
		else:
			fuselage = [(-38, -4), (-33, -7), (12, -7), (28, -3), (50, 1), (28, 5), (8, 7), (-18, 6), (-33, 5), (-38, 3)]
			self.canvas.create_polygon(self.rotate_points(cx, cy, fuselage, angle_deg), fill=body_color, outline="#181D23", width=1.5)

		if name not in ("X-37 Orbital Valkyrie", "B-2 Spirit Stealth", "SR-71 Blackbird"):
			spine = [(-30, -6), (10, -6), (24, -3), (-30, -3)]
			self.canvas.create_polygon(self.rotate_points(cx, cy, spine, angle_deg), fill="#7D8B99", outline="")
			radome = [(34, -2), (52, 1), (34, 4)]
			self.canvas.create_polygon(self.rotate_points(cx, cy, radome, angle_deg), fill="#2B323B", outline="")

		if hp_ratio < 0.65:
			scorch1 = [(-26, -4), (-14, -6), (-10, 2), (-24, 3)]
			self.canvas.create_polygon(self.rotate_points(cx, cy, scorch1, angle_deg), fill="#222222", outline="")
			crack = self.rotate_points(cx, cy, [(-18, -5), (-12, 0), (-16, 4)], angle_deg)
			self.canvas.create_line(crack, fill="#FF6600" if hp_ratio < 0.35 else "#111111", width=1.5)
		if hp_ratio < 0.35:
			scorch2 = [(4, -3), (18, -4), (15, 4), (2, 3)]
			self.canvas.create_polygon(self.rotate_points(cx, cy, scorch2, angle_deg), fill="#1A1A1A", outline="#FF4500")

		if name not in ("B-2 Spirit Stealth", "SR-71 Blackbird"):
			intake = [(2, 4), (16, 4), (13, 8), (0, 8)]
			self.canvas.create_polygon(self.rotate_points(cx, cy, intake, angle_deg), fill="#232931", outline="#111111")

		wing_dmg = -3.5 if hp_ratio < 0.35 else 0.0
		near_span = max(3.0, 13.0 + bank * 6.5 + wing_dmg)

		if name in ("Su-57 Felon", "ADF-01 Falken"):
			wing = [(-18, 1), (4, near_span + 3), (16, near_span + 3), (9, 1)]
			rail = [(3, near_span + 3), (17, near_span + 3)]
		elif name == "A-10 Thunderbolt II":
			wing = [(-14, 1), (-12, near_span + 4), (6, near_span + 4), (8, 1)]
			rail = [(-13, near_span + 4), (7, near_span + 4)]
		elif name == "B-2 Spirit Stealth":
			wing = [(-26, 2), (-10, near_span + 4), (4, near_span + 4), (26, 2)]
			rail = [(-10, near_span + 4), (4, near_span + 4)]
		elif name in ("YF-23 Black Widow", "F-22 Raptor", "SR-71 Blackbird"):
			wing = [(-28, 1), (-8, near_span + 1), (4, near_span + 1), (18, 1)]
			rail = [(-9, near_span + 1), (5, near_span + 1)]
		elif name == "X-37 Orbital Valkyrie":
			wing = [(-34, 2), (-14, near_span + 3), (4, near_span + 3), (24, 2)]
			rail = [(-15, near_span + 3), (5, near_span + 3)]
		else:
			wing = [(-22, 1), (-9, near_span), (6, near_span), (11, 1)]
			rail = [(-11, near_span), (8, near_span)]

		wing_col = "#CBD5E1" if name == "X-37 Orbital Valkyrie" else ("#14171F" if name == "B-2 Spirit Stealth" else "#414B56")
		self.canvas.create_polygon(self.rotate_points(cx, cy, wing, angle_deg), fill=wing_col, outline="#181D23")
		self.canvas.create_line(self.rotate_points(cx, cy, rail, angle_deg), fill=plane.accent_color, width=2.5)

		if name == "X-37 Orbital Valkyrie":
			canopy = [(16, -9), (22, -11), (31, -8), (34, -5)]
			canopy_col = "#FFD700"
		elif name == "ADF-01 Falken":
			canopy = [(8, -6), (18, -9), (34, -5), (28, -3)]
			canopy_col = "#00FFFF"
		elif name == "B-2 Spirit Stealth":
			canopy = [(12, -5), (18, -7), (28, -4), (24, -3)]
			canopy_col = "#A855F7"
		else:
			canopy = [(4, -7), (11, -13.5), (22, -12.5), (28, -5)]
			canopy_col = "#00BFFF"
		glint = [(11, -11.5), (19, -11), (17, -9), (10, -9.5)]
		self.canvas.create_polygon(self.rotate_points(cx, cy, canopy, angle_deg), fill=canopy_col, outline="#181D23")
		self.canvas.create_polygon(self.rotate_points(cx, cy, glint, angle_deg), fill="#E0FFFF", outline="")
# ================= PART 3 START =================
	def draw_enemy_jet(self, cx, cy):
		flame_len = 18 + random.randint(-3, 5)
		self.canvas.create_polygon(cx + 36, cy - 3, cx + 36 + flame_len, cy, cx + 36, cy + 3, fill="#FF3300", outline="#FFFF00")
		fuselage = [(36, -4), (31, -7), (-12, -7), (-28, -3), (-48, 1), (-28, 5), (31, 5), (36, 3)]
		flat_f = [coord for px, py in fuselage for coord in (cx + px, cy + py)]
		self.canvas.create_polygon(flat_f, fill="#8B1A1A", outline="#111111", width=1.5)
		self.canvas.create_line(cx - 24, cy, cx + 28, cy, fill="#FF4444", width=2)
		self.canvas.create_polygon(cx + 34, cy - 6, cx + 38, cy - 22, cx + 24, cy - 22, cx + 16, cy - 6, fill="#601010", outline="#111111")
		self.canvas.create_polygon(cx + 22, cy + 1, cx + 7, cy + 13, cx - 8, cy + 13, cx - 10, cy + 1, fill="#4A0C0C", outline="#111111")
		self.canvas.create_polygon(cx - 4, cy - 7, cx - 11, cy - 13, cx - 22, cy - 12, cx - 26, cy - 5, fill="#FFD700", outline="#111111")

	def draw_slow_gunship(self, cx, cy):
		self.canvas.create_oval(cx - 48, cy - 4, cx - 38, cy + 4, fill="#FF6600", outline="")
		self.canvas.create_rectangle(cx - 44, cy - 10, cx + 34, cy + 10, fill="#4E632B", outline="#111111", width=1.5)
		self.canvas.create_rectangle(cx - 40, cy - 4, cx + 30, cy + 2, fill="#637D37", outline="")
		self.canvas.create_polygon(cx + 34, cy - 10, cx + 52, cy + 2, cx + 34, cy + 10, fill="#38471E", outline="#111111")
		self.canvas.create_polygon(cx - 44, cy - 10, cx - 50, cy - 26, cx - 34, cy - 26, cx - 24, cy - 10, fill="#38471E", outline="#111111")
		self.canvas.create_polygon(cx - 16, cy + 2, cx - 2, cy + 18, cx + 15, cy + 18, cx + 20, cy + 2, fill="#2A3615", outline="#111111")
		self.canvas.create_rectangle(cx + 24, cy - 8, cx + 36, cy - 2, fill="#FFA500", outline="#111111")

	def draw_orbital_satellite(self, sat, cx, cy):
		wing_h = 16 + 10 * abs(math.cos(math.radians(sat.panel_angle)))
		self.canvas.create_rectangle(cx - 10, cy - wing_h - 8, cx + 10, cy - 8, fill="#1E3A8A", outline="#38BDF8", width=1.5)
		self.canvas.create_rectangle(cx - 10, cy + 8, cx + 10, cy + wing_h + 8, fill="#1E3A8A", outline="#38BDF8", width=1.5)
		self.canvas.create_line(cx, cy - wing_h - 8, cx, cy + wing_h + 8, fill="#CBD5E1", width=2)
		self.canvas.create_rectangle(cx - 12, cy - 9, cx + 12, cy + 9, fill="#D97706", outline="#FDE047", width=1.5)
		self.canvas.create_arc(cx - 22, cy - 10, cx - 8, cy + 10, start=90, extent=180, fill="#E2E8F0", outline="#FFFFFF")
		self.canvas.create_oval(cx + 10, cy - 3, cx + 16, cy + 3, fill="#00FF66", outline="")
		self.canvas.create_text(cx, cy - wing_h - 18, text="RECON SAT [+1000₵]", fill="#38BDF8", font=("Consolas", 8, "bold"))

	def draw_space_drone(self, cx, cy):
		flame = 22 + random.randint(-4, 6)
		self.canvas.create_polygon(cx + 30, cy - 3, cx + 30 + flame, cy, cx + 30, cy + 3, fill="#A855F7", outline="#00FFFF")
		hull = [(-44, 0), (-14, -9), (26, -7), (34, 0), (26, 7), (-14, 9)]
		flat = [coord for px, py in hull for coord in (cx + px, cy + py)]
		self.canvas.create_polygon(flat, fill="#1E1B4B", outline="#38BDF8", width=1.5)
		self.canvas.create_polygon(cx - 18, cy, cx + 12, cy - 16, cx + 22, cy, fill="#312E81", outline="#818CF8")
		self.canvas.create_polygon(cx - 18, cy, cx + 12, cy + 16, cx + 22, cy, fill="#312E81", outline="#818CF8")
		self.canvas.create_oval(cx - 26, cy - 3, cx - 14, cy + 3, fill="#FF0055", outline="#FFFF00")

	def draw_boss_fortress(self, boss, cx, cy):
		self.canvas.create_polygon(cx + 80, cy - 6, cx + 115 + random.randint(0, 12), cy, cx + 80, cy + 6, fill="#FF4500", outline="#FFFF00")
		hull = [
			(84, -14), (65, -24), (-45, -24), (-92, -6),
			(-108, 4), (-75, 18), (65, 18), (84, 10)
		]
		flat_h = [coord for px, py in hull for coord in (cx + px, cy + py)]
		self.canvas.create_polygon(flat_h, fill="#2F3542", outline="#111111", width=2)
		self.canvas.create_polygon(cx - 35, cy - 24, cx - 20, cy - 38, cx + 15, cy - 38, cx + 28, cy - 24, fill="#57606F", outline="#111111")
		self.canvas.create_polygon(cx + 55, cy - 24, cx + 75, cy - 48, cx + 88, cy - 48, cx + 80, cy - 24, fill="#B22222", outline="#111111")
		self.canvas.create_oval(cx - 65, cy - 6, cx - 42, cy + 8, fill="#FF2222", outline="#FFFF00", width=2)
		self.canvas.create_rectangle(cx - 45, cy + 14, cx - 10, cy + 24, fill="#1E272E", outline="#FF4444")

		bar_w = 170
		hp_ratio = max(0.0, boss.hp / boss.max_hp)
		enraged = hp_ratio <= 0.5
		bar_col = "#FF8C00" if enraged else "#FF2222"
		title = f"⚠ SKY FORTRESS [ENRAGED]: {boss.hp}/{boss.max_hp} HP ⚠" if enraged else f"SKY FORTRESS: {boss.hp}/{boss.max_hp} HP"
		self.canvas.create_rectangle(cx - bar_w // 2, cy - 64, cx + bar_w // 2, cy - 52, fill="#111111", outline="#FFFF00" if enraged else "white")
		self.canvas.create_rectangle(cx - bar_w // 2 + 2, cy - 62, cx - bar_w // 2 + int((bar_w - 4) * hp_ratio), cy - 54, fill=bar_col, outline="")
		self.canvas.create_text(cx, cy - 74, text=title, fill="#FF6600" if enraged else "#FFFF00", font=("Consolas", 10, "bold"))

	def draw_aircraft_carrier(self, carrier, ground_y):
		cx = carrier["x"]
		hw = carrier["half_w"]
		if cx < -hw - 80 or cx > self.width + hw + 80:
			return

		water_left = max(0, cx - 950)
		water_right = min(self.width, cx + 950)
		if water_right > water_left:
			self.canvas.create_rectangle(water_left, ground_y, water_right, self.height, fill="#0B3B66", outline="")
			self.canvas.create_rectangle(water_left, ground_y, water_right, ground_y + 10, fill="#1E6091", outline="")

		deck_y = ground_y - carrier["deck_alt"]

		self.canvas.create_rectangle(cx + 25, deck_y - 34, cx + 78, deck_y, fill="#4B5563", outline="#111111", width=1.5)
		self.canvas.create_rectangle(cx + 32, deck_y - 26, cx + 70, deck_y - 18, fill="#00FFFF", outline="#111111")
		self.canvas.create_line(cx + 52, deck_y - 34, cx + 52, deck_y - 52, fill="#CCCCCC", width=2)
		self.canvas.create_oval(cx + 49, deck_y - 55, cx + 55, deck_y - 49, fill="#FF2222", outline="")

		hull_pts = [
			cx - hw + 18, ground_y + 6,
			cx - hw - 12, deck_y + 4,
			cx + hw + 22, deck_y + 4,
			cx + hw - 16, ground_y + 6
		]
		self.canvas.create_polygon(hull_pts, fill="#374151", outline="#111827", width=2)
		self.canvas.create_rectangle(cx - hw - 16, deck_y - 3, cx + hw + 24, deck_y + 4, fill="#1F2937", outline="#9CA3AF", width=1)

		for sx in range(int(cx - hw + 12), int(cx + hw - 10), 34):
			self.canvas.create_line(sx, deck_y, sx + 16, deck_y, fill="#FACC15", width=2)
		for wx in (-125, -100, -75, -50):
			self.canvas.create_line(cx + wx, deck_y - 4, cx + wx, deck_y + 2, fill="#EF4444", width=2)

		beacon_col = "#00FF66" if not carrier["serviced"] else "#888888"
		self.canvas.create_oval(cx - hw - 14, deck_y - 12, cx - hw - 4, deck_y - 2, fill=beacon_col, outline="#FFFFFF")

		if not carrier["serviced"]:
			stern_x = cx - hw - 10
			self.canvas.create_line(
				stern_x - 360, deck_y - 95, stern_x, deck_y - 4,
				fill="#00FF66", width=2, dash=(8, 6)
			)

		self.canvas.create_text(cx, deck_y + 16, text="CVN-76 REARM & REPAIR DECK", fill="#00FFFF", font=("Consolas", 9, "bold"))
# ================= PART 4 START =================
	def draw_cloud(self, cx, screen_y, size):
		self.canvas.create_oval(cx + 6, screen_y + size * 0.22, cx + size * 1.45, screen_y + size * 0.68, fill="#CBD8E6", outline="")
		self.canvas.create_oval(cx, screen_y + size * 0.1, cx + size * 0.75, screen_y + size * 0.58, fill="#F4F9FF", outline="")
		self.canvas.create_oval(cx + size * 0.35, screen_y, cx + size * 1.15, screen_y + size * 0.55, fill="#FFFFFF", outline="")
		self.canvas.create_oval(cx + size * 0.8, screen_y + size * 0.12, cx + size * 1.5, screen_y + size * 0.58, fill="#F4F9FF", outline="")

	def draw_explosion(self, ex, ey, exp):
		progress = min(1.0, exp.age / exp.max_age)
		r = exp.radius
		if exp.is_nuke:
			self.canvas.create_oval(ex - r * 1.35, ey - r * 1.35, ex + r * 1.35, ey + r * 1.35, fill="", outline="#FFD700", width=3)
		self.canvas.create_oval(ex - r, ey - r, ex + r, ey + r, fill="#3B3330", outline="#554433")
		if progress < 0.85:
			r2 = r * (0.85 - progress * 0.3)
			self.canvas.create_oval(ex - r2, ey - r2, ex + r2, ey + r2, fill="#FF5500", outline="#FFA500")
		if progress < 0.45:
			r3 = r * (0.5 - progress * 0.6)
			self.canvas.create_oval(ex - r3, ey - r3, ex + r3, ey + r3, fill="#FFFFE0", outline="")

	def draw_cockpit_radar(self, plane, weapons, enemies, carrier=None):
		r = 62
		rcx = self.width - 88
		rcy = 225
		max_range = 2400.0

		self.canvas.create_oval(rcx - r - 4, rcy - r - 4, rcx + r + 4, rcy + r + 4, fill="#06120B", outline="#00FF66", width=2)
		self.canvas.create_oval(rcx - r // 2, rcy - r // 2, rcx + r // 2, rcy + r // 2, fill="", outline="#0A3D1F", width=1)
		self.canvas.create_line(rcx - r, rcy, rcx + r, rcy, fill="#0A3D1F", width=1)
		self.canvas.create_line(rcx, rcy - r, rcx, rcy + r, fill="#0A3D1F", width=1)

		sweep_rad = math.radians(self.radar_angle)
		self.canvas.create_line(rcx, rcy, rcx + r * math.cos(sweep_rad), rcy + r * math.sin(sweep_rad), fill="#00FF66", width=1.5)

		def plot_blip(world_x, world_alt, color, size=3, diamond=False):
			dx = (world_x - plane.x) / max_range
			dy = -(world_alt - plane.altitude) / max_range
			dist = math.hypot(dx, dy)
			if dist > 0.94:
				dx = (dx / dist) * 0.94
				dy = (dy / dist) * 0.94
			bx = rcx + dx * r
			by = rcy + dy * r
			if diamond:
				self.canvas.create_polygon(bx, by - size - 2, bx + size + 2, by, bx, by + size + 2, bx - size - 2, by, fill=color, outline="white")
			else:
				self.canvas.create_oval(bx - size, by - size, bx + size, by + size, fill=color, outline="")

		for target in weapons.targets:
			plot_blip(target.x, 0, "#55AA55", size=2)
		for sam in enemies.sams:
			plot_blip(sam.x, 0, "#FFD700", size=3)
		for slow in enemies.slow_enemies:
			plot_blip(slow.x, slow.alt, "#FF8C00", size=3)
		for jet in enemies.jets:
			plot_blip(jet.x, jet.alt, "#FF2222", size=3.5)
		for drone in enemies.space_drones:
			plot_blip(drone.x, drone.alt, "#C084FC", size=3.5)
		for sat in enemies.satellites:
			plot_blip(sat.x, sat.alt, "#38BDF8", size=3.5, diamond=True)
		if enemies.boss is not None:
			plot_blip(enemies.boss.x, enemies.boss.alt, "#FF00FF", size=4, diamond=True)
		for m in enemies.aa_missiles:
			plot_blip(m.x, m.alt, "#FFFFFF", size=3, diamond=True)
		if carrier is not None and abs(carrier["x"] - plane.x) <= max_range:
			plot_blip(carrier["x"], carrier["deck_alt"], "#00FFFF", size=4, diamond=True)

		self.canvas.create_polygon(rcx + 5, rcy, rcx - 4, rcy - 3, rcx - 2, rcy, rcx - 4, rcy + 3, fill="#00FFFF", outline="")
		self.canvas.create_text(rcx, rcy + r + 12, text="RADAR 2.4KM", fill="#00FF66", font=("Consolas", 8, "bold"))

	def draw_lock_reticle(self, target, camera_y_offset):
		if target is None:
			return
		tx = target.x
		t_alt = getattr(target, 'alt', 12.0)
		ty = self.alt_to_screen_y(t_alt, camera_y_offset)
		if -40 <= tx <= self.width + 40 and -40 <= ty <= self.height + 40:
			r = 26
			self.canvas.create_polygon(
				tx, ty - r, tx + r, ty, tx, ty + r, tx - r, ty,
				fill="", outline="#00FFFF", width=2
			)
			self.canvas.create_text(tx, ty - r - 10, text="LOCK [K]", fill="#00FFFF", font=("Consolas", 9, "bold"))

	def draw_offscreen_missile_indicator(self, ax, ay, dist_meters):
		margin = 42
		ix = max(margin, min(self.width - margin, ax))
		iy = max(margin, min(self.height - margin, ay))

		angle_to_msl = math.degrees(math.atan2(ay - iy, ax - ix))
		arrow_pts = [(16, 0), (-10, -11), (-4, 0), (-10, 11)]
		rotated_arrow = self.rotate_points(ix, iy, arrow_pts, angle_to_msl)

		self.canvas.create_polygon(rotated_arrow, fill="#FF1E1E", outline="#FFFF00", width=2)

		label_x = ix + 22 if ix < self.width // 2 else ix - 22
		anchor = "w" if ix < self.width // 2 else "e"
		bg_x1 = label_x - 4 if anchor == "w" else label_x - 86
		bg_x2 = label_x + 86 if anchor == "w" else label_x + 4
		self.canvas.create_rectangle(bg_x1, iy - 12, bg_x2, iy + 12, fill="#1A0000", outline="#FF3333", width=1.5)
		self.canvas.create_text(
			label_x, iy, anchor=anchor,
			text=f"MSL {int(dist_meters)}m",
			fill="#FFFF00", font=("Consolas", 10, "bold")
		)
# ================= PART 5 START =================
	def render_menu(self, mission, pad_connected):
		self.canvas.delete("all")
		self.canvas.configure(bg="#0B1320")
		cx = self.width // 2

		for star in self.stars[:75]:
			self.canvas.create_oval(star.x, star.y, star.x + star.size, star.y + star.size, fill="#88AACC", outline="")

		self.canvas.create_text(cx, 44, text="SKY FURY: INTERCEPTOR v1.0", fill="#00FF66", font=("Consolas", 28, "bold"))
		self.canvas.create_text(
			cx, 80,
			text=f"COIN BALANCE: {mission.coins} ₵   |   HIGH SCORE: {mission.high_score}   |   BEST WAVE: {mission.best_wave}",
			fill="#FFD700", font=("Consolas", 13, "bold")
		)

		tab_label = "[TAB] SWITCH TO HANGAR ROSTER" if mission.in_armory else "[TAB] OPEN ORDNANCE ARMORY STORE"
		tab_col = "#FFA500" if mission.in_armory else "#00FFFF"
		self.canvas.create_text(cx, 104, text=tab_label, fill=tab_col, font=("Consolas", 11, "bold"))

		panel_w = 680

		if mission.in_armory:
			self.canvas.create_rectangle(cx - panel_w // 2, 122, cx + panel_w // 2, 435, fill="#111C2E", outline="#FFA500", width=2)

			cat_labels = {"vulcan": "VULCAN CANNON", "missile": "AIR-TO-AIR MISSILE", "bomb": "AIR-TO-GROUND BOMB"}
			cat_texts = []
			for idx, c_key in enumerate(mission.weapon_categories):
				label = cat_labels[c_key]
				cat_texts.append(f"[{label}]" if idx == mission.selected_weapon_cat_idx else f" {label} ")
			self.canvas.create_text(cx, 142, text="  |  ".join(cat_texts), fill="#FFD700", font=("Consolas", 11, "bold"))
			self.canvas.create_text(cx, 162, text="[A / D] Switch Category   •   [W / S] Select Ordnance", fill="#88AACC", font=("Consolas", 9))

			cat = mission.current_weapon_cat
			items = mission.weapon_lists[cat]
			sel_w_idx = mission.selected_weapon_idx[cat]

			for row, w_name in enumerate(items):
				w_stats = cfg.WEAPON_SHOP[cat][w_name]
				unlocked = mission.is_weapon_unlocked(cat, w_name)
				equipped = (mission.equipped_weapons[cat] == w_name)
				selected = (row == sel_w_idx)
				y_pos = 200 + row * 48

				if selected:
					outline_col = "#00FF66" if equipped else ("#00FFFF" if unlocked else "#FFD700")
					self.canvas.create_rectangle(
						cx - panel_w // 2 + 16, y_pos - 19, cx + panel_w // 2 - 16, y_pos + 21,
						fill="#1B324B", outline=outline_col, width=2
					)

				prefix = "▶ " if selected else "  "
				if equipped:
					tag = "[EQUIPPED]"
					tag_col = "#00FF66"
				elif unlocked:
					tag = "[UNLOCKED]"
					tag_col = "#00FFFF"
				else:
					tag = f"[BUY • {w_stats['cost']} ₵]"
					tag_col = "#FFA500"

				name_col = ("#00FFFF" if unlocked else "#FFD700") if selected else ("#CCCCCC" if unlocked else "#888888")
				self.canvas.create_text(cx - panel_w // 2 + 28, y_pos - 6, anchor="w", text=f"{prefix}{w_name}", fill=name_col, font=("Consolas", 11, "bold"))
				self.canvas.create_text(cx + panel_w // 2 - 28, y_pos - 6, anchor="e", text=tag, fill=tag_col, font=("Consolas", 10, "bold"))
				self.canvas.create_text(cx - panel_w // 2 + 48, y_pos + 10, anchor="w", text=w_stats["desc"], fill="#99B8D9", font=("Consolas", 9))

			self.canvas.create_rectangle(cx - panel_w // 2, 448, cx + panel_w // 2, 514, fill="#111C2E", outline="#00FFFF", width=2)
			self.canvas.create_text(cx, 464, text=f"ACTIVE LOADOUT FOR {mission.aircraft_name.upper()}", fill="#00FFFF", font=("Consolas", 10, "bold"))
			eq = mission.equipped_weapons
			self.canvas.create_text(
				cx, 488,
				text=f"GUN: {eq['vulcan']}   |   MSL: {eq['missile']}   |   BOMB: {eq['bomb']}",
				fill="#FFFFFF", font=("Consolas", 9, "bold")
			)

			cur_w = mission.current_weapon_name
			if mission.equipped_weapons[cat] == cur_w:
				action_txt = f"{cur_w.upper()} IS CURRENTLY EQUIPPED"
				action_col = "#00FF66"
			elif mission.is_weapon_unlocked(cat, cur_w):
				action_txt = f"PRESS [ENTER] OR [SPACE] TO EQUIP {cur_w.upper()}"
				action_col = "#00FFFF"
			else:
				cost = cfg.WEAPON_SHOP[cat][cur_w]["cost"]
				action_txt = f"PRESS [ENTER] TO BUY & EQUIP {cur_w.upper()} ({cost} ₵)"
				action_col = "#FFD700"

		else:
			self.canvas.create_rectangle(cx - panel_w // 2, 122, cx + panel_w // 2, 428, fill="#111C2E", outline="#00FF66", width=2)
			total_jets = len(mission.aircraft_names)
			sel_idx = mission.selected_aircraft_idx
			self.canvas.create_text(
				cx, 140,
				text=f"HANGAR ROSTER ({sel_idx + 1}/{total_jets})  [W / S TO SCROLL]",
				fill="#00FFFF", font=("Consolas", 11, "bold")
			)

			visible_slots = 5
			start_idx = max(0, min(sel_idx - 2, total_jets - visible_slots))
			end_idx = min(total_jets, start_idx + visible_slots)

			for row, idx in enumerate(range(start_idx, end_idx)):
				name = mission.aircraft_names[idx]
				stats = cfg.AIRCRAFT_PRESETS[name]
				unlocked = mission.is_unlocked(name)
				y_pos = 176 + row * 50
				selected = (idx == sel_idx)
				if selected:
					outline_col = "#00FFFF" if unlocked else "#FFD700"
					self.canvas.create_rectangle(cx - panel_w // 2 + 16, y_pos - 19, cx + panel_w // 2 - 16, y_pos + 21, fill="#1B324B", outline=outline_col, width=2)

				prefix = "▶ " if selected else "  "
				tag = "[UNLOCKED]" if unlocked else f"[LOCKED • {stats['cost']} ₵]"
				name_col = ("#00FFFF" if unlocked else "#FFD700") if selected else ("#CCCCCC" if unlocked else "#888888")

				self.canvas.create_text(cx - panel_w // 2 + 28, y_pos - 6, anchor="w", text=f"{prefix}{name}", fill=name_col, font=("Consolas", 12, "bold"))
				self.canvas.create_text(cx + panel_w // 2 - 28, y_pos - 6, anchor="e", text=tag, fill="#00FF66" if unlocked else "#FFA500", font=("Consolas", 10, "bold"))
				self.canvas.create_text(
					cx - panel_w // 2 + 48, y_pos + 11, anchor="w",
					text=f"{stats['role']} | HP: {stats['max_hp']} | Top: {int(140 + 100 * stats['speed_mult'])} kts",
					fill="#99B8D9", font=("Consolas", 9)
				)

			if start_idx > 0:
				self.canvas.create_text(cx + panel_w // 2 - 18, 140, text="▲", fill="#FFFF00", font=("Consolas", 11, "bold"))
			if end_idx < total_jets:
				self.canvas.create_text(cx + panel_w // 2 - 18, 414, text="▼", fill="#FFFF00", font=("Consolas", 11, "bold"))

			self.canvas.create_rectangle(cx - panel_w // 2, 442, cx + panel_w // 2, 514, fill="#111C2E", outline="#00FF66", width=2)
			self.canvas.create_text(cx, 458, text="DIFFICULTY LEVEL  [A / D]", fill="#FFFF00", font=("Consolas", 11, "bold"))
			diff_display = []
			for idx, d_name in enumerate(mission.difficulty_names):
				diff_display.append(f"[{d_name.upper()}]" if idx == mission.selected_difficulty_idx else f" {d_name} ")
			self.canvas.create_text(cx, 488, text="    ".join(diff_display), fill="#00FF66", font=("Consolas", 14, "bold"))

			sel_name = mission.aircraft_name
			if mission.is_unlocked(sel_name):
				action_txt = "PRESS [ENTER] OR [SPACE] TO LAUNCH"
				action_col = "#FFFFFF"
			else:
				cost = cfg.AIRCRAFT_PRESETS[sel_name]["cost"]
				action_txt = f"PRESS [ENTER] TO UNLOCK {sel_name.upper()} ({cost} ₵)"
				action_col = "#FFD700"

		self.canvas.create_text(cx, 545, text=action_txt, fill=action_col, font=("Consolas", 16, "bold"))
		if mission.menu_notice_timer > 0 and mission.menu_notice:
			self.canvas.create_text(cx, 576, text=mission.menu_notice, fill="#FF6666" if "NEED" in mission.menu_notice else "#00FF66", font=("Consolas", 12, "bold"))
		else:
			pad_txt = "GAMEPAD: CONNECTED" if pad_connected else "KEYBOARD + GAMEPAD READY  |  [F1] +10,000 ₵ TEST CHEAT"
			self.canvas.create_text(cx, 576, text=pad_txt, fill="#00FFFF", font=("Consolas", 10, "bold"))
# ================= PART 6 START =================
	def draw_hud(self, plane, weapons, enemies, mission, carrier=None):
		self.canvas.create_rectangle(15, 15, 385, 355, fill="#0A0F14", stipple="gray50", outline="#00FF66")
		gear_status = "DOWN" if plane.gear_progress >= 0.99 else ("UP" if plane.gear_progress <= 0.01 else "MOVING")
		zone = "SPACE" if plane.altitude >= cfg.SPACE_ALT - 200 else ("STRATOSPHERE" if plane.altitude >= cfg.STRATOSPHERE_ALT else "TROPOSPHERE")
		flare_status = "READY (4x)" if plane.flare_cooldown <= 0 else f"RELOAD ({plane.flare_cooldown:.1f}s)"
		lock_status = "LOCKED [K]" if weapons.locked_target is not None else "SCANNING"
		hull_state = "NOMINAL" if plane.hp_ratio >= 0.65 else ("DAMAGED" if plane.hp_ratio >= 0.35 else "CRITICAL!")
		sp_status = "READY!" if weapons.special_cooldown <= 0 else f"{weapons.special_cooldown:.1f}s"

		hud_text = (
			f"AIRCRAFT : {plane.preset_name} [{mission.difficulty_name}]\n"
			f"GUN/MSL  : {weapons.equipped_vulcan[:13]} | {weapons.equipped_missile[:13]}\n"
			f"ORDNANCE : {weapons.equipped_bomb}\n"
			f"{mission.get_objective_text()}\n"
			f"WEATHER  : {mission.weather}\n"
			f"SCORE    : {weapons.score} (BEST: {mission.high_score})\n"
			f"COINS    : {mission.coins} ₵\n"
			f"ARMOR HP : {int(plane.hp)}/{plane.max_hp} [{hull_state}]\n"
			f"SPCL [E] : {plane.special_type} [{sp_status}] | STEALTH: {int(plane.stealth * 100)}%\n"
			f"THROTTLE : {int(plane.throttle)}% | {int(plane.speed)} kts\n"
			f"ALTITUDE : {int(plane.altitude)} m [{zone}]\n"
			f"PITCH    : {int(plane.pitch)}° | G-LOAD: {plane.g_force:.1f}G\n"
			f"GEAR [G] : {gear_status} | FLARE [F]: {flare_status}\n"
			f"RADAR    : {lock_status}"
		)
		self.canvas.create_text(25, 25, anchor="nw", text=hud_text, fill="#00FF66", font=("Consolas", 10, "bold"))

		self.canvas.create_text(
			self.width - 20, 20, anchor="ne",
			text=(
				"FLIGHT & COMBAT CONTROLS:\n"
				"[W / S] Pitch Nose Up/Down\n"
				"[D / A] Throttle Up/Down\n"
				"[G] Landing Gear | [F] 4x Flares\n"
				"[Space / J] Vulcan Cannon\n"
				"[K / M] Homing Missile | [L] Bomb\n"
				"[E] Signature Special Weapon\n"
				"[N] Mute | [F11] Fullscreen | [H] Hangar"
			),
			fill="#00FF66", font=("Consolas", 10, "bold"), justify="right"
		)

		if mission.wave_banner_timer > 0 and not plane.crashed:
			cx = self.width // 2
			self.canvas.create_rectangle(cx - 260, 82, cx + 260, 138, fill="#0D1B2A", outline="#00FFFF", width=2)
			self.canvas.create_text(cx, 100, text=mission.banner_title, fill="#FFFF00", font=("Consolas", 15, "bold"))
			self.canvas.create_text(cx, 122, text=mission.banner_subtitle, fill="#00FFFF", font=("Consolas", 11, "bold"))

		if enemies.aa_missiles and not plane.crashed:
			closest = min(math.hypot(m.x - plane.x, m.alt - plane.altitude) for m in enemies.aa_missiles)
			flash = int(closest) % 40 < 24
			box_fill = "#660000" if flash else "#220000"
			border_col = "#FFFF00" if flash else "#FF3333"
			cx = self.width // 2
			self.canvas.create_rectangle(cx - 275, 26, cx + 275, 68, fill=box_fill, outline=border_col, width=3)
			self.canvas.create_text(
				cx, 47,
				text=f"⚠ MISSILE INBOUND ({int(closest)}m)! DEPLOY FLARES [F] ⚠",
				fill="#FFFF00" if flash else "#FF4444", font=("Consolas", 15, "bold")
			)
		elif carrier is not None and not plane.crashed:
			dist_to_deck = carrier["x"] - plane.x
			if 160.0 < dist_to_deck < 2400.0 and not carrier["serviced"]:
				cx = self.width // 2
				self.canvas.create_rectangle(cx - 310, 26, cx + 310, 68, fill="#082436", outline="#00FFFF", width=2)
				self.canvas.create_text(
					cx, 47,
					text=f"⚓ CARRIER AHEAD ({int(dist_to_deck)}m) — DEPLOY GEAR [G] & SLOW TO LAND ⚓",
					fill="#00FFFF", font=("Consolas", 13, "bold")
				)

		if plane.crashed:
			self.canvas.create_text(
				self.width // 2, self.height // 2,
				text=(
					f"AIRCRAFT DESTROYED!\n{plane.crash_reason}\n"
					f"REACHED WAVE {mission.wave} | SCORE: {weapons.score} | COINS: {mission.coins} ₵\n"
					f"Press [R] to Retry or [H] for Hangar"
				),
				fill="#FF3333", font=("Consolas", 20, "bold"), justify="center"
			)
		elif plane.altitude < 120 and plane.vertical_speed < -5 and not plane.gear_down:
			self.canvas.create_text(
				self.width // 2, 155,
				text="PULL UP / DEPLOY LANDING GEAR [G]!",
				fill="#FF3333", font=("Consolas", 15, "bold")
			)

		self.draw_cockpit_radar(plane, weapons, enemies, carrier)
# ================= PART 7 START =================
	def render(self, plane, weapons, enemies, mission, carrier=None):
		self.canvas.delete("all")
		weather = mission.weather
		self.canvas.configure(bg=self.get_sky_color(plane.altitude, weather))

		if weather == "NIGHT RAID":
			star_visibility = 1.0
		elif plane.altitude > cfg.STAR_FADE_START:
			star_visibility = min(1.0, (plane.altitude - cfg.STAR_FADE_START) / 1500.0)
		else:
			star_visibility = 0.0

		if star_visibility > 0:
			for i in range(int(len(self.stars) * star_visibility)):
				star = self.stars[i]
				self.canvas.create_oval(star.x, star.y, star.x + star.size, star.y + star.size, fill="white", outline="")

		if plane.altitude > 1750.0:
			aurora_alpha = min(1.0, (plane.altitude - 1750.0) / 700.0)
			wave_shift = self.scroll_x * 0.08
			for band in range(3):
				base_y = 75 + band * 48
				pts = []
				for sx in range(0, self.width + 120, 120):
					wy = base_y + math.sin((sx + wave_shift) * 0.008 + band * 1.4) * 28
					pts.extend([sx, wy])
				col = "#00FF99" if band != 1 else "#A855F7"
				self.canvas.create_line(pts, fill=col, width=int(6 * aurora_alpha) + 2, smooth=True)

		if weather == "THUNDERSTORM" and plane.altitude < cfg.STRATOSPHERE_ALT:
			for rx, ry in self.raindrops:
				self.canvas.create_line(rx, ry, rx - 8, ry + 16, fill="#7FA6C9", width=1)
		elif plane.speed > 170 and plane.altitude < cfg.SPACE_ALT - 200:
			streak_col = "#A0C8E8" if plane.altitude < cfg.STRATOSPHERE_ALT else "#4A6B8C"
			for ws in self.wind_streaks:
				self.canvas.create_line(ws.x, ws.y, ws.x + ws.length, ws.y, fill=streak_col, width=1)

		camera_y_offset = max(0, plane.altitude - (self.height * 0.35))

		if plane.altitude < cfg.STRATOSPHERE_ALT + 200:
			for cloud in self.clouds:
				screen_y = cloud.y + camera_y_offset
				if -80 < screen_y < self.height:
					self.draw_cloud(cloud.x, screen_y, cloud.size)

		ground_y = self.height - self.ground_height + camera_y_offset
		if ground_y < self.height + 160:
			mtn_span = 220 * len(self.mountains)
			mtn_scroll = (self.scroll_x * 0.22) % mtn_span
			for base_x, peak_h in self.mountains:
				mx = base_x - mtn_scroll
				if mx < -260:
					mx += mtn_span
				if mx < self.width + 260:
					self.canvas.create_polygon(
						mx - 160, ground_y,
						mx, ground_y - peak_h,
						mx + 160, ground_y,
						fill="#2D4A53" if plane.altitude < cfg.STRATOSPHERE_ALT else "#182830",
						outline=""
					)
					if peak_h > 115:
						self.canvas.create_polygon(
							mx - 42, ground_y - peak_h + 30,
							mx, ground_y - peak_h,
							mx + 42, ground_y - peak_h + 30,
							fill="#DCE6F0", outline=""
						)

		if ground_y < self.height:
			self.canvas.create_rectangle(0, ground_y, self.width, self.height, fill="#226B3A", outline="")
			self.canvas.create_rectangle(0, ground_y + 26, self.width, self.height, fill="#19522C", outline="")
			self.canvas.create_rectangle(0, ground_y, self.width, ground_y + 24, fill="#26292E", outline="#111111")
			stripe_offset = -(self.scroll_x % 90)
			for sx in range(int(stripe_offset), self.width, 90):
				self.canvas.create_rectangle(sx, ground_y + 10, sx + 45, ground_y + 14, fill="#E6E6E6", outline="")
				self.canvas.create_oval(sx, ground_y + 1, sx + 4, ground_y + 5, fill="#FFD700", outline="")

			for target in weapons.targets:
				if -50 < target.x < self.width + 50:
					self.canvas.create_rectangle(target.x - 18, ground_y - 14, target.x + 18, ground_y, fill="#B22222", outline="black")
					self.canvas.create_polygon(target.x - 22, ground_y - 14, target.x + 22, ground_y - 14, target.x, ground_y - 24, fill="#8B0000", outline="black")

			for sam in enemies.sams:
				if -50 < sam.x < self.width + 50:
					self.canvas.create_rectangle(sam.x - 20, ground_y - 12, sam.x + 20, ground_y, fill="#4B5320", outline="black")
					self.canvas.create_line(sam.x - 6, ground_y - 12, sam.x - 18, ground_y - 28, fill="#D4AF37", width=4)
					self.canvas.create_line(sam.x + 6, ground_y - 12, sam.x - 6, ground_y - 28, fill="#D4AF37", width=4)

			if carrier is not None:
				self.draw_aircraft_carrier(carrier, ground_y)
# ================= PART 8 START =================
		for s in weapons.smoke:
			sy = self.alt_to_screen_y(s.alt, camera_y_offset)
			if -30 <= s.x <= self.width + 30 and -30 <= sy <= self.height + 30:
				fade = s.age / s.max_age
				if s.tint == "cyan":
					color = "#80FFFF" if fade < 0.35 else ("#B0C4DE" if fade < 0.7 else "#778899")
				elif s.tint == "fire":
					color = "#FF4500" if fade < 0.4 else ("#FFA500" if fade < 0.7 else "#333333")
				elif s.tint == "dark":
					color = "#444444" if fade < 0.5 else "#262626"
				else:
					color = "#F0F8FF" if fade < 0.4 else ("#B8C4D0" if fade < 0.75 else "#788896")
				self.canvas.create_oval(s.x - s.radius, sy - s.radius, s.x + s.radius, sy + s.radius, fill=color, outline="")

		for jet in enemies.jets:
			jy = self.alt_to_screen_y(jet.alt, camera_y_offset)
			if -60 < jet.x < self.width + 60 and -50 < jy < self.height:
				self.draw_enemy_jet(jet.x, jy)

		for met in enemies.meteors:
			my = self.alt_to_screen_y(met.alt, camera_y_offset)
			if -80 < met.x < self.width + 80 and -80 < my < self.height + 80:
				self.canvas.create_line(met.x + 28, my - 12, met.x, my, fill="#FF6600", width=int(met.size))
				self.canvas.create_oval(met.x - met.size, my - met.size, met.x + met.size, my + met.size, fill="#FDE047", outline="#FF4500")

		for sat in enemies.satellites:
			sy = self.alt_to_screen_y(sat.alt, camera_y_offset)
			if -80 < sat.x < self.width + 80 and -80 < sy < self.height + 80:
				self.draw_orbital_satellite(sat, sat.x, sy)

		for drone in enemies.space_drones:
			dy = self.alt_to_screen_y(drone.alt, camera_y_offset)
			if -80 < drone.x < self.width + 80 and -80 < dy < self.height + 80:
				self.draw_space_drone(drone.x, dy)

		for slow in enemies.slow_enemies:
			sy = self.alt_to_screen_y(slow.alt, camera_y_offset)
			if -70 < slow.x < self.width + 70 and -50 < sy < self.height:
				self.draw_slow_gunship(slow.x, sy)

		if enemies.boss is not None:
			by = self.alt_to_screen_y(enemies.boss.alt, camera_y_offset)
			if -140 < enemies.boss.x < self.width + 140:
				self.draw_boss_fortress(enemies.boss, enemies.boss.x, by)

		self.draw_lock_reticle(weapons.locked_target, camera_y_offset)

		plane_y = self.alt_to_screen_y(plane.altitude, camera_y_offset)
		plane_y = max(120, min(self.height - self.ground_height - 15, plane_y))
		self.draw_fighter_jet(plane, plane.x, plane_y)

		if weapons.laser_timer > 0 and not plane.crashed:
			rad = math.radians(-plane.pitch)
			lx1 = plane.x + 50 * math.cos(rad)
			ly1 = plane_y + 50 * math.sin(rad)
			lx2 = lx1 + 1600 * math.cos(rad)
			ly2 = ly1 + 1600 * math.sin(rad)
			self.canvas.create_line(lx1, ly1, lx2, ly2, fill="#00FFFF", width=11)
			self.canvas.create_line(lx1, ly1, lx2, ly2, fill="#FFFFFF", width=4)

		for f in plane.flares:
			fy = self.alt_to_screen_y(f.alt, camera_y_offset)
			self.canvas.create_oval(f.x - 11, fy - 11, f.x + 11, fy + 11, fill="#FF8C00", outline="")
			self.canvas.create_oval(f.x - 7, fy - 7, f.x + 7, fy + 7, fill="#FFFF00", outline="")
			self.canvas.create_oval(f.x - 4, fy - 4, f.x + 4, fy + 4, fill="#FFFFFF", outline="")

		for b in weapons.bullets:
			by = self.alt_to_screen_y(b.alt, camera_y_offset)
			b_angle = math.atan2(-b.vy, b.vx)
			streak_len = 24 if b.heavy else 16
			tx = b.x - streak_len * math.cos(b_angle)
			ty = by - streak_len * math.sin(b_angle)
			self.canvas.create_line(
				tx, ty, b.x, by,
				fill=b.color,
				width=4.0 if b.heavy else 2.5
			)

		for bomb in weapons.bombs:
			by = self.alt_to_screen_y(bomb.alt, camera_y_offset)
			b_fill = "#FFD700" if bomb.bomb_type == "B61 Tactical Nuke" else "#222222"
			b_out = "#FF4500" if bomb.bomb_type == "B61 Tactical Nuke" else "#CCCCCC"
			self.canvas.create_oval(bomb.x - 8, by - 4, bomb.x + 8, by + 4, fill=b_fill, outline=b_out, width=1.5)

		for m in weapons.missiles:
			my = self.alt_to_screen_y(m.alt, camera_y_offset)
			rad = math.radians(-m.angle)
			tx = m.x - 16 * math.cos(rad)
			ty = my - 16 * math.sin(rad)
			self.canvas.create_line(tx, ty, m.x, my, fill=m.color, width=3)
			self.canvas.create_oval(tx - 3.5, ty - 3.5, tx + 3.5, ty + 3.5, fill="#FF4500", outline="")

		for m in enemies.aa_missiles:
			ay = self.alt_to_screen_y(m.alt, camera_y_offset)
			dist = math.hypot(m.x - plane.x, m.alt - plane.altitude)
			if 0 <= m.x <= self.width and 0 <= ay <= self.height:
				rad = math.radians(-m.angle)
				tx = m.x - 16 * math.cos(rad)
				ty = ay - 16 * math.sin(rad)
				self.canvas.create_line(tx, ty, m.x, ay, fill="#FF2222", width=3.5)
				self.canvas.create_oval(tx - 4, ty - 4, tx + 4, ty + 4, fill="#FFFF00", outline="#FF4500")
			else:
				self.draw_offscreen_missile_indicator(m.x, ay, dist)

		for exp in weapons.explosions:
			ey = self.alt_to_screen_y(exp.alt, camera_y_offset)
			self.draw_explosion(exp.x, ey, exp)

		if weapons.nuke_flash_timer > 0:
			self.canvas.create_rectangle(0, 0, self.width, self.height, fill="#FFFFFF", stipple="gray50", outline="")

		self.draw_hud(plane, weapons, enemies, mission, carrier)
