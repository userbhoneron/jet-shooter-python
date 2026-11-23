# ================= PART 1 START =================
import math
import random
from dataclasses import dataclass, field
import config as cfg

@dataclass
class Bullet:
	x: float
	alt: float
	vx: float
	vy: float
	life: float
	dmg: int = 18
	color: str = "#FFD700"
	pierce: bool = False
	splash: int = 0
	heavy: bool = False
	hit_ids: set = field(default_factory=set)

@dataclass
class Bomb:
	x: float
	alt: float
	vx: float
	vy: float
	bomb_type: str = "Mk-82 Iron Bomb"
	blast: int = 70
	is_submunition: bool = False

@dataclass
class PlayerMissile:
	x: float
	alt: float
	angle: float
	speed: float
	life: float
	target: object = None
	dmg: int = 120
	turn_rate: float = 425.0
	blast: int = 0
	color: str = "#00FFFF"
	smoke_timer: float = 0.0

@dataclass
class SmokeParticle:
	x: float
	alt: float
	radius: float
	age: float
	max_age: float
	tint: str = "light"

@dataclass
class Explosion:
	x: float
	alt: float
	radius: float
	max_radius: float
	age: float = 0.0
	max_age: float = 0.45
	is_nuke: bool = False

@dataclass
class GroundTarget:
	x: float
	alt: float = 0.0

class WeaponSystem:
	def __init__(self, screen_width=cfg.SCREEN_WIDTH):
		self.screen_width = screen_width
		self.equipped_vulcan = "Standard 20mm"
		self.equipped_missile = "AIM-9 Sidewinder"
		self.equipped_bomb = "Mk-82 Iron Bomb"
		self.reset()

	def apply_loadout(self, equipped_dict):
		self.equipped_vulcan = equipped_dict.get("vulcan", "Standard 20mm")
		self.equipped_missile = equipped_dict.get("missile", "AIM-9 Sidewinder")
		self.equipped_bomb = equipped_dict.get("bomb", "Mk-82 Iron Bomb")

	def reset(self):
		self.bullets = []
		self.bombs = []
		self.missiles = []
		self.smoke = []
		self.explosions = []
		self.targets = [GroundTarget(random.randint(600, 3500)) for _ in range(cfg.TARGET_COUNT)]
		self.locked_target = None
		self.score = 0
		self.gun_cooldown = 0.0
		self.missile_cooldown = 0.0
		self.bomb_cooldown = 0.0
		self.special_cooldown = 0.0
		self.nuke_flash_timer = 0.0
		self.laser_timer = 0.0
		self.laser_tick = 0.0
		self.carpet_queue = 0
		self.carpet_timer = 0.0
		self.gau_queue = 0
		self.gau_timer = 0.0

	def spawn_smoke(self, x, alt, radius=4.0, max_age=0.65, tint="light"):
		if len(self.smoke) < 200:
			self.smoke.append(SmokeParticle(x, alt, radius, 0.0, max_age, tint))

	def acquire_lock(self, plane, enemies):
		candidates = []
		if enemies.boss is not None and enemies.boss.x > plane.x + 60:
			candidates.append((enemies.boss, enemies.boss.x, enemies.boss.alt))
		for jet in enemies.jets:
			if jet.x > plane.x + 60:
				candidates.append((jet, jet.x, jet.alt))
		for slow in enemies.slow_enemies:
			if slow.x > plane.x + 60:
				candidates.append((slow, slow.x, slow.alt))
		for sam in enemies.sams:
			if sam.x > plane.x + 60:
				candidates.append((sam, sam.x, 12.0))
		for drone in enemies.space_drones:
			if drone.x > plane.x + 60:
				candidates.append((drone, drone.x, drone.alt))
		for sat in enemies.satellites:
			if sat.x > plane.x + 60:
				candidates.append((sat, sat.x, sat.alt))

		max_lock = 2600.0 if self.equipped_missile == "Heavy Phoenix Cruise" else cfg.LOCK_ON_RANGE
		best_target = None
		best_dist = max_lock
		for obj, tx, t_alt in candidates:
			dist = math.hypot(tx - plane.x, t_alt - plane.altitude)
			if dist < best_dist:
				best_dist = dist
				best_target = obj
		self.locked_target = best_target


	def fire_special(self, plane, enemies):
		if self.special_cooldown > 0 or plane.crashed:
			return None

		sp = plane.special_type
		self.special_cooldown = plane.special_max_cd

		if sp == "TLS":
			self.laser_timer = 0.65
			self.laser_tick = 0.0
			return "missile"
		elif sp == "CARPET":
			if plane.altitude <= 12:
				self.special_cooldown = 0.0
				return None
			self.carpet_queue = 5
			self.carpet_timer = 0.0
			return "bomb"
		elif sp == "GAU-8":
			self.gau_queue = 12
			self.gau_timer = 0.0
			return "vulcan"
		elif sp == "VOLLEY":
			rad = math.radians(plane.pitch)
			nose_x = plane.x + 32 * math.cos(rad)
			nose_alt = plane.altitude + 32 * math.sin(rad) - 4
			init_speed = max(cfg.MISSILE_SPEED, plane.speed + 200.0)
			targets = [self.locked_target]
			for obj in [enemies.boss] + enemies.jets + enemies.slow_enemies + enemies.sams:
				if obj is not None and obj not in targets and obj.x > plane.x + 60:
					targets.append(obj)
			for i, angle_off in enumerate((-12.0, 0.0, 12.0)):
				tgt = targets[i % len(targets)] if targets else None
				self.missiles.append(PlayerMissile(
					x=nose_x, alt=nose_alt, angle=plane.pitch + angle_off,
					speed=init_speed, life=cfg.MISSILE_LIFETIME, target=tgt,
					dmg=120, turn_rate=460.0, color="#00FFFF"
				))
			return "missile"
		elif sp == "OVERDRIVE":
			plane.overdrive_timer = 3.0
			plane.flare_cooldown = 0.0
			return "flare"
		return None

	def fire_vulcan(self, plane, heavy=False):
		if not heavy and self.gun_cooldown > 0:
			return
		v_stats = cfg.WEAPON_SHOP["vulcan"].get(self.equipped_vulcan, cfg.WEAPON_SHOP["vulcan"]["Standard 20mm"])
		rad = math.radians(plane.pitch)
		nose_x = plane.x + 48 * math.cos(rad)
		nose_alt = plane.altitude + 48 * math.sin(rad)

		if heavy:
			shot_rad = math.radians(plane.pitch + random.uniform(-1.5, 1.5))
			muzzle_speed = (plane.speed + cfg.BULLET_SPEED_ADD * 1.35) * cfg.HORIZ_SPEED_SCALE
			self.bullets.append(Bullet(
				x=nose_x, alt=nose_alt,
				vx=muzzle_speed * math.cos(shot_rad), vy=muzzle_speed * math.sin(shot_rad),
				life=cfg.BULLET_LIFETIME, dmg=42, color="#ADFF2F", pierce=True, heavy=True
			))
			return

		v_name = self.equipped_vulcan
		dmg = v_stats["dmg"]
		col = v_stats["color"]
		pierce = v_name in ("30mm Depleted Uranium", "Hyper-Velocity Rail Slugs")
		splash = 35 if v_name == "Explosive HEI Rounds" else 0
		speed_add = cfg.BULLET_SPEED_ADD * (1.85 if v_name == "Hyper-Velocity Rail Slugs" else (1.2 if v_name == "30mm Depleted Uranium" else 1.0))
		muzzle_speed = (plane.speed + speed_add) * cfg.HORIZ_SPEED_SCALE

		if v_name == "Twin Rotary Gatling":
			for off_alt, off_ang in ((-4.0, -1.2), (4.0, 1.2)):
				s_rad = math.radians(plane.pitch + off_ang)
				self.bullets.append(Bullet(
					x=nose_x, alt=nose_alt + off_alt,
					vx=muzzle_speed * math.cos(s_rad), vy=muzzle_speed * math.sin(s_rad),
					life=cfg.BULLET_LIFETIME, dmg=dmg, color=col, heavy=False
				))
		else:
			self.bullets.append(Bullet(
				x=nose_x, alt=nose_alt,
				vx=muzzle_speed * math.cos(rad), vy=muzzle_speed * math.sin(rad),
				life=cfg.BULLET_LIFETIME, dmg=dmg, color=col,
				pierce=pierce, splash=splash, heavy=(v_name in ("30mm Depleted Uranium", "Hyper-Velocity Rail Slugs"))
			))

		self.gun_cooldown = cfg.GUN_COOLDOWN * v_stats["cd_mult"]

	def drop_bomb(self, plane, bypass_cd=False):
		if (not bypass_cd and self.bomb_cooldown > 0) or plane.altitude <= 10:
			return
		b_name = "Mk-82 Iron Bomb" if bypass_cd else self.equipped_bomb
		b_stats = cfg.WEAPON_SHOP["bomb"].get(b_name, cfg.WEAPON_SHOP["bomb"]["Mk-82 Iron Bomb"])
		rad = math.radians(plane.pitch)
		self.bombs.append(Bomb(
			x=plane.x,
			alt=plane.altitude - 6,
			vx=plane.speed * math.cos(rad),
			vy=plane.speed * math.sin(rad) - 5.0,
			bomb_type=b_name,
			blast=b_stats["blast"]
		))
		if not bypass_cd:
			self.bomb_cooldown = b_stats["cd_override"] if b_stats["cd_override"] is not None else plane.bomb_cd

	def fire_missile(self, plane, enemies=None):
		if self.missile_cooldown > 0:
			return
		m_name = self.equipped_missile
		m_stats = cfg.WEAPON_SHOP["missile"].get(m_name, cfg.WEAPON_SHOP["missile"]["AIM-9 Sidewinder"])
		rad = math.radians(plane.pitch)
		nose_x = plane.x + 30 * math.cos(rad)
		nose_alt = plane.altitude + 30 * math.sin(rad) - 4
		init_speed = max(cfg.MISSILE_SPEED, plane.speed + 180.0)

		if m_name == "Swarm Micro-Pods (3x)":
			targets = [self.locked_target]
			if enemies is not None:
				for obj in [enemies.boss] + enemies.jets + enemies.slow_enemies + enemies.sams:
					if obj is not None and obj not in targets and obj.x > plane.x + 60:
						targets.append(obj)
			for i, ang_off in enumerate((-10.0, 0.0, 10.0)):
				tgt = targets[i % len(targets)] if targets else None
				self.missiles.append(PlayerMissile(
					x=nose_x, alt=nose_alt, angle=plane.pitch + ang_off,
					speed=init_speed * 1.08, life=cfg.MISSILE_LIFETIME, target=tgt,
					dmg=m_stats["dmg"], turn_rate=m_stats["turn_rate"],
					blast=m_stats["blast"], color="#FF00FF"
				))
		else:
			m_col = "#FFD700" if m_name == "Heavy Phoenix Cruise" else ("#00FF66" if m_name == "Python High-G Seeker" else "#00FFFF")
			self.missiles.append(PlayerMissile(
				x=nose_x, alt=nose_alt, angle=plane.pitch,
				speed=init_speed, life=cfg.MISSILE_LIFETIME, target=self.locked_target,
				dmg=m_stats["dmg"], turn_rate=m_stats["turn_rate"],
				blast=m_stats["blast"], color=m_col
			))

		self.missile_cooldown = plane.missile_cd * m_stats["cd_mult"]
	# ================= PART 2A START =================
	def spawn_explosion(self, x, alt, max_rad, is_nuke=False):
		max_age = 1.35 if is_nuke else 0.5
		self.explosions.append(Explosion(x, alt, 10.0 if is_nuke else 6.0, max_rad, 0.0, max_age, is_nuke))
		smoke_count = 16 if is_nuke else 4
		for _ in range(smoke_count):
			self.spawn_smoke(
				x + random.uniform(-45 if is_nuke else -14, 45 if is_nuke else 14),
				alt + random.uniform(4, 55 if is_nuke else 18),
				radius=random.uniform(16, 30) if is_nuke else random.uniform(7, 13),
				max_age=random.uniform(1.4, 2.2) if is_nuke else random.uniform(0.7, 1.1),
				tint="fire" if is_nuke else "dark"
			)

	def detonate_nuke(self, impact_x, plane, enemies, mission):
		self.nuke_flash_timer = 0.28
		self.spawn_explosion(impact_x, 0, 260, is_nuke=True)
		self.check_ground_hit(impact_x, 650, enemies, mission)

		for jet in enemies.jets:
			if abs(jet.x - impact_x) < 620 and jet.alt < 950:
				self.spawn_explosion(jet.x, jet.alt, 75)
				jet.x = self.screen_width + random.randint(900, 2200)
				jet.alt = random.randint(250, 1300)
				self.score += 500
				mission.record_kill("air")

		for slow in enemies.slow_enemies:
			if abs(slow.x - impact_x) < 620 and slow.alt < 950:
				self.spawn_explosion(slow.x, slow.alt, 80)
				slow.x = self.screen_width + random.randint(500, 1400)
				slow.alt = random.randint(180, 850)
				self.score += 300
				mission.record_kill("air")

		if enemies.boss is not None and abs(enemies.boss.x - impact_x) < 700:
			self.check_air_hit(enemies.boss.x, enemies.boss.alt, 120, 320, enemies, mission)

		if not plane.crashed and math.hypot(plane.x - impact_x, plane.altitude) < 280:
			plane.take_damage(15, "CAUGHT IN OWN NUCLEAR BLAST!")

	def check_ground_hit(self, impact_x, blast_radius, enemies, mission):
		for target in self.targets:
			if abs(target.x - impact_x) < blast_radius:
				self.spawn_explosion(target.x, 0, 75)
				target.x = self.screen_width + random.randint(600, 2000)
				self.score += 100
				mission.record_kill("ground")

		for sam in enemies.sams:
			if abs(sam.x - impact_x) < blast_radius:
				self.spawn_explosion(sam.x, 10, 80)
				sam.x = self.screen_width + random.randint(900, 2400)
				self.score += 250
				mission.record_kill("ground")

	def check_air_hit(self, px, p_alt, hit_radius, damage, enemies, mission, ignore_ids=None):
		if enemies.boss is not None:
			b_id = id(enemies.boss)
			if (not ignore_ids or b_id not in ignore_ids) and math.hypot(enemies.boss.x - px, enemies.boss.alt - p_alt) < hit_radius + 42:
				if ignore_ids is not None:
					ignore_ids.add(b_id)
				enemies.boss.hp -= damage
				self.spawn_explosion(px, p_alt, 38)
				if enemies.boss.hp <= 0:
					for _ in range(5):
						self.spawn_explosion(
							enemies.boss.x + random.uniform(-50, 50),
							enemies.boss.alt + random.uniform(-25, 25),
							110
						)
					enemies.boss = None
					self.score += 2000
					mission.record_kill("boss")
				return True

		for jet in enemies.jets:
			j_id = id(jet)
			if (not ignore_ids or j_id not in ignore_ids) and math.hypot(jet.x - px, jet.alt - p_alt) < hit_radius:
				if ignore_ids is not None:
					ignore_ids.add(j_id)
				self.spawn_explosion(jet.x, jet.alt, 70)
				jet.x = self.screen_width + random.randint(800, 2000)
				jet.alt = random.randint(250, 1300)
				self.score += 500
				mission.record_kill("air")
				return True

		for slow in enemies.slow_enemies:
			s_id = id(slow)
			if (not ignore_ids or s_id not in ignore_ids) and math.hypot(slow.x - px, slow.alt - p_alt) < hit_radius + 8:
				if ignore_ids is not None:
					ignore_ids.add(s_id)
				self.spawn_explosion(slow.x, slow.alt, 75)
				slow.x = self.screen_width + random.randint(400, 1200)
				slow.alt = random.randint(180, 850)
				self.score += 300
				mission.record_kill("air")
				return True

		for sat in enemies.satellites:
			sat_id = id(sat)
			if (not ignore_ids or sat_id not in ignore_ids) and math.hypot(sat.x - px, sat.alt - p_alt) < hit_radius + 14:
				if ignore_ids is not None:
					ignore_ids.add(sat_id)
				self.spawn_explosion(sat.x, sat.alt, 85)
				sat.x = self.screen_width + random.randint(1800, 3500)
				sat.alt = random.randint(2550, 2950)
				self.score += 1000
				mission.record_kill("air")
				return True

		for drone in enemies.space_drones:
			d_id = id(drone)
			if (not ignore_ids or d_id not in ignore_ids) and math.hypot(drone.x - px, drone.alt - p_alt) < hit_radius + 6:
				if ignore_ids is not None:
					ignore_ids.add(d_id)
				self.spawn_explosion(drone.x, drone.alt, 75)
				drone.x = self.screen_width + random.randint(1200, 2600)
				drone.alt = random.randint(2150, 2850)
				self.score += 750
				mission.record_kill("air")
				return True
		return False

	def _process_laser_beam(self, plane, enemies, mission, dt):
		self.laser_timer = max(0.0, self.laser_timer - dt)
		self.laser_tick -= dt
		if self.laser_tick > 0:
			return
		self.laser_tick = 0.08

		rad = math.radians(plane.pitch)
		dx, dy = math.cos(rad), math.sin(rad)
		nose_x = plane.x + 50 * dx
		nose_alt = plane.altitude + 50 * dy

		def point_to_ray_dist(tx, t_alt):
			vx, vy = tx - nose_x, t_alt - nose_alt
			proj = vx * dx + vy * dy
			if proj < 0 or proj > 1600:
				return 9999.0
			return abs(vx * dy - vy * dx)

		if enemies.boss is not None and point_to_ray_dist(enemies.boss.x, enemies.boss.alt) < 55:
			self.check_air_hit(enemies.boss.x, enemies.boss.alt, 60, 45, enemies, mission)
		for jet in enemies.jets:
			if point_to_ray_dist(jet.x, jet.alt) < 38:
				self.check_air_hit(jet.x, jet.alt, 50, 100, enemies, mission)
		for slow in enemies.slow_enemies:
			if point_to_ray_dist(slow.x, slow.alt) < 42:
				self.check_air_hit(slow.x, slow.alt, 50, 100, enemies, mission)
		for sat in enemies.satellites:
			if point_to_ray_dist(sat.x, sat.alt) < 46:
				self.check_air_hit(sat.x, sat.alt, 50, 100, enemies, mission)
		for drone in enemies.space_drones:
			if point_to_ray_dist(drone.x, drone.alt) < 40:
				self.check_air_hit(drone.x, drone.alt, 50, 100, enemies, mission)
		for target in self.targets:
			if point_to_ray_dist(target.x, 0) < 35:
				self.check_ground_hit(target.x, 40, enemies, mission)
		for sam in enemies.sams:
			if point_to_ray_dist(sam.x, 12) < 35:
				self.check_ground_hit(sam.x, 40, enemies, mission)


		rad = math.radians(plane.pitch)
		dx, dy = math.cos(rad), math.sin(rad)
		nose_x = plane.x + 50 * dx
		nose_alt = plane.altitude + 50 * dy

		def point_to_ray_dist(tx, t_alt):
			vx, vy = tx - nose_x, t_alt - nose_alt
			proj = vx * dx + vy * dy
			if proj < 0 or proj > 1600:
				return 9999.0
			return abs(vx * dy - vy * dx)

		if enemies.boss is not None and point_to_ray_dist(enemies.boss.x, enemies.boss.alt) < 55:
			self.check_air_hit(enemies.boss.x, enemies.boss.alt, 60, 45, enemies, mission)
		for jet in enemies.jets:
			if point_to_ray_dist(jet.x, jet.alt) < 38:
				self.check_air_hit(jet.x, jet.alt, 50, 100, enemies, mission)
		for slow in enemies.slow_enemies:
			if point_to_ray_dist(slow.x, slow.alt) < 42:
				self.check_air_hit(slow.x, slow.alt, 50, 100, enemies, mission)
		for target in self.targets:
			if point_to_ray_dist(target.x, 0) < 35:
				self.check_ground_hit(target.x, 40, enemies, mission)
		for sam in enemies.sams:
			if point_to_ray_dist(sam.x, 12) < 35:
				self.check_ground_hit(sam.x, 40, enemies, mission)
	# ================= PART 2B START =================
	def update(self, plane, plane_dx, enemies, mission, dt=0.016):
		if self.gun_cooldown > 0: self.gun_cooldown = max(0.0, self.gun_cooldown - dt)
		if self.missile_cooldown > 0: self.missile_cooldown = max(0.0, self.missile_cooldown - dt)
		if self.bomb_cooldown > 0: self.bomb_cooldown = max(0.0, self.bomb_cooldown - dt)
		if self.special_cooldown > 0: self.special_cooldown = max(0.0, self.special_cooldown - dt)
		if self.nuke_flash_timer > 0: self.nuke_flash_timer = max(0.0, self.nuke_flash_timer - dt)

		if self.carpet_queue > 0 and not plane.crashed:
			self.carpet_timer -= dt
			if self.carpet_timer <= 0:
				self.drop_bomb(plane, bypass_cd=True)
				self.carpet_queue -= 1
				self.carpet_timer = 0.08

		if self.gau_queue > 0 and not plane.crashed:
			self.gau_timer -= dt
			if self.gau_timer <= 0:
				self.fire_vulcan(plane, heavy=True)
				self.gau_queue -= 1
				self.gau_timer = 0.02

		if self.laser_timer > 0 and not plane.crashed:
			self._process_laser_beam(plane, enemies, mission, dt)

		self.acquire_lock(plane, enemies)

		if not plane.crashed and plane.altitude > 8:
			rad_p = math.radians(plane.pitch)
			tail_x = plane.x - 36 * math.cos(rad_p)
			tail_alt = plane.altitude - 36 * math.sin(rad_p)

			if plane.hp_ratio < 0.65:
				plane.damage_smoke_timer += dt
				interval = 0.03 if plane.hp_ratio < 0.35 else 0.065
				if plane.damage_smoke_timer >= interval:
					plane.damage_smoke_timer = 0.0
					tint = "fire" if (plane.hp_ratio < 0.35 and random.random() < 0.45) else "dark"
					self.spawn_smoke(tail_x, tail_alt, radius=5.5, max_age=0.75, tint=tint)

			if abs(plane.g_force) > 2.4 and plane.altitude < cfg.STRATOSPHERE_ALT:
				plane.contrail_timer += dt
				if plane.contrail_timer >= 0.025:
					plane.contrail_timer = 0.0
					self.spawn_smoke(tail_x, tail_alt - 6, radius=2.5, max_age=0.45, tint="light")

		for target in self.targets:
			target.x -= plane_dx
			if target.x < -100:
				target.x = self.screen_width + random.randint(400, 1800)

		for b in self.bullets[:]:
			b.x += (b.vx * dt) - plane_dx
			b.alt += b.vy * dt
			b.life -= dt
			hit = self.check_air_hit(b.x, b.alt, 34 if b.heavy else 30, b.dmg, enemies, mission, ignore_ids=b.hit_ids if b.pierce else None)
			if hit:
				if b.splash > 0:
					self.spawn_explosion(b.x, b.alt, b.splash)
				if not b.pierce:
					self.bullets.remove(b)
					continue
			if b.alt <= 0:
				self.spawn_explosion(b.x, 0, max(16, b.splash) if not b.heavy else 26)
				self.check_ground_hit(b.x, max(24, b.splash) if not b.heavy else 38, enemies, mission)
				self.bullets.remove(b)
			elif b.life <= 0:
				self.bullets.remove(b)

		for bomb in self.bombs[:]:
			if bomb.bomb_type == "Cluster Munition (CBU)" and not bomb.is_submunition and bomb.alt <= 140.0 and bomb.vy < 0:
				for vx_off in (-55.0, -18.0, 18.0, 55.0):
					self.bombs.append(Bomb(
						x=bomb.x, alt=bomb.alt, vx=bomb.vx + vx_off, vy=bomb.vy - 10.0,
						bomb_type="CBU Submunition", blast=65, is_submunition=True
					))
				self.spawn_explosion(bomb.x, bomb.alt, 32)
				self.bombs.remove(bomb)
				continue

			if bomb.bomb_type == "JDAM Laser-Guided":
				g_candidates = [t.x for t in self.targets] + [s.x for s in enemies.sams]
				if g_candidates:
					nearest_gx = min(g_candidates, key=lambda gx: abs(gx - bomb.x))
					diff_x = nearest_gx - bomb.x
					if abs(diff_x) < 420:
						bomb.x += max(-260.0 * dt, min(260.0 * dt, diff_x * 3.5 * dt))

			bomb.x += (bomb.vx * cfg.HORIZ_SPEED_SCALE * dt) - plane_dx
			bomb.vy -= cfg.GRAVITY * cfg.BOMB_GRAVITY_MULT * dt
			bomb.alt += bomb.vy * dt

			if bomb.alt <= 0:
				if bomb.bomb_type == "B61 Tactical Nuke":
					self.detonate_nuke(bomb.x, plane, enemies, mission)
				else:
					self.spawn_explosion(bomb.x, 0, bomb.blast)
					self.check_ground_hit(bomb.x, bomb.blast, enemies, mission)
				self.bombs.remove(bomb)

		for m in self.missiles[:]:
			if m.target is not None:
				tx = m.target.x
				t_alt = getattr(m.target, 'alt', 12.0)
				if tx > -150:
					target_vx_px = getattr(m.target, 'speed', 0.0) * cfg.HORIZ_SPEED_SCALE
					if hasattr(m.target, 'cooldown') and hasattr(m.target, 'alt'):
						target_vx_px = -target_vx_px
					rel_vx_px = target_vx_px - (plane_dx / dt)

					dist = math.hypot(tx - m.x, t_alt - m.alt)
					time_to_hit = dist / max(150.0, m.speed * cfg.HORIZ_SPEED_SCALE)
					lead_x = tx + (rel_vx_px * min(time_to_hit, 0.35))

					desired_angle = math.degrees(math.atan2(t_alt - m.alt, lead_x - m.x))
					angle_diff = (desired_angle - m.angle + 180) % 360 - 180
					max_turn = m.turn_rate * dt
					m.angle += max(-max_turn, min(max_turn, angle_diff))

			rad = math.radians(m.angle)
			m.speed = max(m.speed + cfg.MISSILE_ACCEL * dt, plane.speed + 240.0)
			m.x += (m.speed * math.cos(rad) * cfg.HORIZ_SPEED_SCALE * dt) - plane_dx
			m.alt += m.speed * math.sin(rad) * dt
			m.life -= dt

			m.smoke_timer += dt
			if m.smoke_timer >= 0.025:
				m.smoke_timer = 0.0
				self.spawn_smoke(m.x - 12 * math.cos(rad), m.alt - 12 * math.sin(rad), radius=3.5, max_age=0.55, tint="cyan")

			hit_set = set()
			if self.check_air_hit(m.x, m.alt, 42, m.dmg, enemies, mission, ignore_ids=hit_set):
				if m.blast > 0:
					self.spawn_explosion(m.x, m.alt, m.blast)
					self.check_air_hit(m.x, m.alt, m.blast, m.dmg // 2, enemies, mission, ignore_ids=hit_set)
				self.missiles.remove(m)
			elif m.alt <= 16:
				blast_r = max(70, m.blast)
				self.spawn_explosion(m.x, 0, blast_r)
				self.check_ground_hit(m.x, blast_r, enemies, mission)
				self.missiles.remove(m)
			elif m.life <= 0:
				self.missiles.remove(m)


		for s in self.smoke[:]:
			s.x -= plane_dx * 0.85
			s.alt += 6.0 * dt
			s.radius += 14.0 * dt
			s.age += dt
			if s.age >= s.max_age:
				self.smoke.remove(s)

		for exp in self.explosions[:]:
			exp.age += dt
			progress = min(1.0, exp.age / exp.max_age)
			exp.radius = 6.0 + (exp.max_radius - 6.0) * (1.0 - (1.0 - progress) ** 2)
			if exp.age >= exp.max_age:
				self.explosions.remove(exp)
