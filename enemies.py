import math
import random
from dataclasses import dataclass
import config as cfg

@dataclass
class EnemyJet:
	x: float
	alt: float
	speed: float
	cooldown: float

@dataclass
class SlowEnemy:
	x: float
	alt: float
	speed: float

@dataclass
class SamSite:
	x: float
	cooldown: float
	engaged_this_pass: bool = False
	lock_timer: float = 0.0

@dataclass
class BossGunship:
	x: float
	alt: float
	hp: int
	max_hp: int
	cooldown: float
	bob_timer: float = 0.0

@dataclass
class AAMissile:
	x: float
	alt: float
	angle: float
	speed: float
	life: float

@dataclass
class OrbitalSatellite:
	x: float
	alt: float
	speed: float
	panel_angle: float = 0.0

@dataclass
class SpaceDrone:
	x: float
	alt: float
	speed: float
	cooldown: float

@dataclass
class SpaceMeteor:
	x: float
	alt: float
	vx: float
	vy: float
	size: float

class EnemySystem:
	def __init__(self, screen_width=cfg.SCREEN_WIDTH):
		self.screen_width = screen_width
		self.reset()

	def reset(self):
		self.jets = [
			EnemyJet(
				x=self.screen_width + random.randint(500, 1600) + i * 900,
				alt=random.randint(300, 1100),
				speed=cfg.ENEMY_JET_SPEED,
				cooldown=random.uniform(1.5, 3.0)
			)
			for i in range(cfg.ENEMY_JET_COUNT)
		]
		self.slow_enemies = [
			SlowEnemy(
				x=self.screen_width + random.randint(300, 1200) + i * 650,
				alt=random.randint(180, 850),
				speed=cfg.SLOW_ENEMY_SPEED
			)
			for i in range(cfg.SLOW_ENEMY_COUNT)
		]
		self.sams = [
			SamSite(
				x=random.randint(1400, 3800) + i * 1200,
				cooldown=random.uniform(0.5, 1.5)
			)
			for i in range(cfg.SAM_COUNT)
		]
		self.boss = None
		self.aa_missiles = []
		self.satellites = [
			OrbitalSatellite(
				x=self.screen_width + random.randint(800, 2600) + i * 1800,
				alt=random.randint(2550, 2950),
				speed=185.0
			)
			for i in range(2)
		]
		self.space_drones = [
			SpaceDrone(
				x=self.screen_width + random.randint(1000, 2400) + i * 1500,
				alt=random.randint(2150, 2850),
				speed=310.0,
				cooldown=random.uniform(1.8, 3.2)
			)
			for i in range(2)
		]
		self.meteors = [
			SpaceMeteor(
				x=random.randint(200, self.screen_width + 1200),
				alt=random.randint(2200, 3100),
				vx=-random.uniform(260.0, 420.0),
				vy=-random.uniform(95.0, 175.0),
				size=random.uniform(4.0, 8.0)
			)
			for _ in range(4)
		]

	def spawn_boss(self, wave_num):
		scaled_hp = cfg.BOSS_BASE_HP + (wave_num // 3 - 1) * 500
		self.boss = BossGunship(
			x=self.screen_width + 260,
			alt=650.0,
			hp=scaled_hp,
			max_hp=scaled_hp,
			cooldown=1.6
		)

	def spawn_aa_missile(self, x, alt, target_x, target_alt, forward_chase=False, angle_offset=0.0):
		cap = 4 if self.boss is not None else cfg.MAX_ACTIVE_AA_MISSILES
		if len(self.aa_missiles) >= cap:
			return
		angle = math.degrees(math.atan2(target_alt - alt, target_x - x)) + angle_offset
		if forward_chase:
			angle = max(12.0, min(75.0, angle))
		self.aa_missiles.append(AAMissile(x, alt, angle, cfg.AA_MISSILE_SPEED, cfg.AA_MISSILE_LIFETIME))
	def update(self, plane, weapons, mission, plane_dx, dt=0.016):
		diff = mission.difficulty_stats
		player_vx = max(10.0, plane.speed * math.cos(math.radians(plane.pitch)))

		# 1. Boss Encounter
		if self.boss is not None:
			enraged = self.boss.hp <= (self.boss.max_hp * 0.5)
			dist_mult = 0.34 if enraged else 0.40
			desired_x = plane.x + (self.screen_width * dist_mult)
			self.boss.x += (desired_x - self.boss.x) * (1.0 - math.exp(-2.4 * dt))

			self.boss.bob_timer += dt * (1.65 if enraged else 1.2)
			bob_amp = 210.0 if enraged else 150.0
			target_alt = max(220.0, min(1450.0, plane.altitude + math.sin(self.boss.bob_timer * 1.5) * bob_amp))
			self.boss.alt += (target_alt - self.boss.alt) * (1.0 - math.exp(-2.2 * dt))

			self.boss.cooldown -= dt
			if self.boss.cooldown <= 0 and not plane.crashed:
				lead_x = plane.x + (player_vx * 0.55)
				spread = (-16.0, 0.0, 16.0) if enraged else (-11.0, 11.0)
				for ang_off in spread:
					self.spawn_aa_missile(self.boss.x - 55, self.boss.alt - 15, lead_x, plane.altitude, angle_offset=ang_off)
				base_cd = max(1.6, diff["enemy_fire_cd"] * 0.55)
				self.boss.cooldown = base_cd * (0.75 if enraged else 1.0)

		# 2. Fast Enemy Fighter Jets
		for jet in self.jets:
			jet.x -= (jet.speed * cfg.HORIZ_SPEED_SCALE * dt) + plane_dx
			jet.cooldown -= dt

			if plane.altitude < cfg.STRATOSPHERE_ALT + 400:
				alt_diff = plane.altitude - jet.alt
				jet.alt += max(-60.0 * dt, min(60.0 * dt, alt_diff * 0.75 * dt))

			if jet.cooldown <= 0 and plane.x + 250 < jet.x < self.screen_width + 450 and not plane.crashed:
				if random.random() > plane.stealth * 0.55:
					lead_x = plane.x + (player_vx * 0.6)
					self.spawn_aa_missile(jet.x - 25, jet.alt, lead_x, plane.altitude)
				jet.cooldown = diff["enemy_fire_cd"]

			if jet.x < -200:
				jet.x = self.screen_width + random.randint(800, 2000)
				jet.alt = random.randint(250, 1200)
				jet.cooldown = random.uniform(2.0, 3.6)

		# 3. Slow Patrol Gunships
		for slow in self.slow_enemies:
			slow.x += (slow.speed * cfg.HORIZ_SPEED_SCALE * dt) - plane_dx
			if slow.x < -250 or slow.x > self.screen_width + 1800:
				slow.x = self.screen_width + random.randint(250, 950)
				slow.alt = max(160, min(1100, plane.altitude + random.randint(-200, 250)))

		# 4. Ground SAM Sites
		effective_sam_range = cfg.SAM_RANGE * (1.0 - plane.stealth * 0.55)
		effective_sam_chance = diff["sam_fire_chance"] * (1.0 - plane.stealth * 0.65)
		effective_lock_delay = cfg.SAM_LOCK_DELAY + (plane.stealth * 0.45)

		for sam in self.sams:
			sam.x -= plane_dx
			if sam.cooldown > 0:
				sam.cooldown = max(0.0, sam.cooldown - dt)

			behind_dist = plane.x - sam.x
			just_passed = (20 <= behind_dist <= 340)
			slant_dist = math.hypot(behind_dist, plane.altitude)

			if just_passed and slant_dist < effective_sam_range and plane.altitude > 40 and not plane.crashed:
				if not sam.engaged_this_pass:
					sam.engaged_this_pass = True
					if sam.cooldown <= 0 and random.random() <= effective_sam_chance:
						sam.lock_timer = effective_lock_delay

			if sam.lock_timer > 0:
				sam.lock_timer = max(0.0, sam.lock_timer - dt)
				if sam.lock_timer == 0 and not plane.crashed:
					chase_target_x = plane.x + (player_vx * 0.45)
					chase_target_alt = max(40.0, plane.altitude + (plane.vertical_speed * 0.5))
					self.spawn_aa_missile(sam.x, 18, chase_target_x, chase_target_alt, forward_chase=True)
					sam.cooldown = cfg.SAM_FIRE_COOLDOWN

			if sam.x < -400:
				sam.x = self.screen_width + random.randint(900, 2200)
				sam.cooldown = random.uniform(0.4, 1.2)
				sam.engaged_this_pass = False
				sam.lock_timer = 0.0

		# 5. Homing AA Missiles
		flare_decoy_radius = 450.0 + (plane.stealth * 240.0)
		stealth_turn_penalty = max(0.35, 1.0 - plane.stealth * 0.52)

		for m in self.aa_missiles[:]:
			target_x, target_alt = plane.x, plane.altitude
			decoyed = False

			if plane.flares:
				nearest_flare = min(plane.flares, key=lambda f: math.hypot(f.x - m.x, f.alt - m.alt))
				if math.hypot(nearest_flare.x - m.x, nearest_flare.alt - m.alt) < flare_decoy_radius:
					target_x, target_alt = nearest_flare.x, nearest_flare.alt
					decoyed = True

			if m.x < plane.x + 250 or decoyed:
				desired_angle = math.degrees(math.atan2(target_alt - m.alt, target_x - m.x))
				angle_diff = (desired_angle - m.angle + 180) % 360 - 180
				turn_mult = 1.15 if decoyed else stealth_turn_penalty
				max_turn = diff["aa_turn_rate"] * turn_mult * dt
				m.angle += max(-max_turn, min(max_turn, angle_diff))

			rad = math.radians(m.angle)
			chase_speed = max(m.speed, plane.speed + 135.0)
			m.x += (chase_speed * math.cos(rad) * cfg.HORIZ_SPEED_SCALE * dt) - plane_dx
			m.alt += chase_speed * math.sin(rad) * dt
			m.life -= dt

			if random.random() < 0.65:
				weapons.spawn_smoke(m.x - 12 * math.cos(rad), m.alt - 12 * math.sin(rad), radius=4.0, max_age=0.65, tint="light")

			if not plane.crashed and math.hypot(m.x - plane.x, m.alt - plane.altitude) < 26:
				weapons.spawn_explosion(plane.x, plane.altitude, 45)
				plane.take_damage(diff["aa_damage"], "SHOT DOWN BY AA MISSILE!")
				self.aa_missiles.remove(m)
				continue

			if m.life <= 0 or m.alt <= 0 or m.x < -450 or m.x > self.screen_width + 450:
				weapons.spawn_explosion(m.x, max(0, m.alt), 25)
				self.aa_missiles.remove(m)

		# 6. Near-Space Orbital Satellites (2550m - 2950m)
		for sat in self.satellites:
			sat.x -= (sat.speed * cfg.HORIZ_SPEED_SCALE * dt) + plane_dx
			sat.panel_angle = (sat.panel_angle + 45.0 * dt) % 360.0
			if sat.x < -300:
				sat.x = self.screen_width + random.randint(1600, 3400)
				sat.alt = random.randint(2550, 2950)

		# 7. Hypersonic Orbital Space Drones (2150m - 2850m)
		for drone in self.space_drones:
			drone.x -= (drone.speed * cfg.HORIZ_SPEED_SCALE * dt) + plane_dx
			drone.cooldown -= dt

			if plane.altitude >= 1850.0:
				alt_diff = plane.altitude - drone.alt
				drone.alt += max(-95.0 * dt, min(95.0 * dt, alt_diff * 1.1 * dt))

			if (drone.cooldown <= 0 and plane.altitude >= 1900.0
					and plane.x + 220 < drone.x < self.screen_width + 450 and not plane.crashed):
				if random.random() > plane.stealth * 0.5:
					lead_x = plane.x + (player_vx * 0.5)
					self.spawn_aa_missile(drone.x - 24, drone.alt, lead_x, plane.altitude)
				drone.cooldown = max(2.4, diff["enemy_fire_cd"] * 0.72)

			if drone.x < -250:
				drone.x = self.screen_width + random.randint(1200, 2600)
				drone.alt = random.randint(2150, 2850)
				drone.cooldown = random.uniform(1.8, 3.2)

		# 8. Orbital Meteors / Micrometeorite Hazard (2000m+)
		for met in self.meteors:
			met.x += (met.vx * cfg.HORIZ_SPEED_SCALE * dt) - plane_dx
			met.alt += met.vy * dt
			if not plane.crashed and math.hypot(met.x - plane.x, met.alt - plane.altitude) < 24 + met.size:
				weapons.spawn_explosion(plane.x, plane.altitude, 40)
				plane.take_damage(20, "STRUCK BY ORBITAL METEORITE!")
				met.x = self.screen_width + random.randint(400, 1500)
				met.alt = random.randint(2350, 3100)
			elif met.alt < 1850 or met.x < -200:
				met.x = self.screen_width + random.randint(200, 1400)
				met.alt = random.randint(2350, 3100)
