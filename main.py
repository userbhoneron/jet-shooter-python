import time
import tkinter as tk
import config as cfg
from aircraft import Aircraft
from weapons import WeaponSystem
from enemies import EnemySystem
from mission import MissionManager
from renderer import GameRenderer
from gamepad import GamepadController
from sound_fx import SoundFX

class FlightSimApp:
	def __init__(self, root):
		self.root = root
		self.root.title("Sky Fury: Interceptor")
		self.fullscreen = cfg.START_FULLSCREEN
		self.root.attributes("-fullscreen", self.fullscreen)

		self.canvas = tk.Canvas(root, width=cfg.SCREEN_WIDTH, height=cfg.SCREEN_HEIGHT, bg="#87CEEB", highlightthickness=0)
		self.canvas.pack(fill=tk.BOTH, expand=True)

		self.mission = MissionManager()
		self.plane = Aircraft()
		self.weapons = WeaponSystem()
		self.enemies = EnemySystem()
		self.renderer = GameRenderer(self.canvas)
		self.gamepad = GamepadController()
		self.sfx = SoundFX()
		self.keys = set()

		self.carrier = {
			"x": 5200.0,
			"half_w": 360.0,
			"deck_alt": 24.0,
			"serviced": False
		}

		self.in_menu = True
		self.menu_nav_cooldown = 0.0
		self.warning_beep_timer = 0.0
		self.last_time = time.perf_counter()

		self.root.bind("<KeyPress>", self.key_down)
		self.root.bind("<KeyRelease>", self.key_up)
		self.canvas.bind("<Configure>", self.on_resize)

		self.loop()

	def on_resize(self, event):
		self.renderer.resize(event.width, event.height)
		self.plane.set_screen_width(event.width)
		self.weapons.screen_width = event.width
		self.enemies.screen_width = event.width

	def toggle_fullscreen(self, force_state=None):
		self.fullscreen = not self.fullscreen if force_state is None else force_state
		self.root.attributes("-fullscreen", self.fullscreen)

	def launch_mission(self):
		self.plane.apply_preset(self.mission.aircraft_name)
		self.plane.reset()
		self.weapons.apply_loadout(self.mission.equipped_weapons)
		self.weapons.reset()
		self.enemies.reset()
		self.mission.reset()
		self.carrier = {
			"x": 5200.0,
			"half_w": 360.0,
			"deck_alt": 24.0,
			"serviced": False
		}
		self.in_menu = False
		self.last_time = time.perf_counter()

	def try_launch_or_unlock(self):
		if self.mission.in_armory:
			status = self.mission.try_buy_or_equip_weapon()
			if status in ("unlocked", "equipped"):
				self.sfx.play("wave_clear")
			else:
				self.sfx.play("damage")
			return

		status = self.mission.try_unlock_selected()
		if status == "unlocked":
			self.sfx.play("wave_clear")
			return
		elif status == "insufficient":
			self.sfx.play("damage")
			return
		self.launch_mission()

	def key_down(self, event):
		key = event.keysym.lower()
		self.keys.add(key)

		if key == 'f11':
			self.toggle_fullscreen()
			return
		elif key == 'f1':
			self.mission.add_cheat_coins(10000)
			if not self.in_menu and not self.plane.crashed:
				self.plane.hp = self.plane.max_hp
			self.sfx.play("wave_clear")
			return
		elif key == 'escape' and self.fullscreen:
			self.toggle_fullscreen(False)
			return
		elif key == 'n':
			self.sfx.toggle_mute()
			return

		if self.in_menu:
			if key == 'tab':
				self.mission.in_armory = not self.mission.in_armory
				self.sfx.play("wave_clear")
				return "break"
			if self.mission.in_armory:
				if key in ('a', 'left'):
					self.mission.cycle_weapon_cat(-1)
				elif key in ('d', 'right'):
					self.mission.cycle_weapon_cat(1)
				elif key in ('w', 'up'):
					self.mission.cycle_weapon_item(-1)
				elif key in ('s', 'down'):
					self.mission.cycle_weapon_item(1)
				elif key in ('return', 'space', 'j'):
					self.try_launch_or_unlock()
			else:
				if key in ('w', 'up'):
					self.mission.cycle_aircraft(-1)
				elif key in ('s', 'down'):
					self.mission.cycle_aircraft(1)
				elif key in ('a', 'left'):
					self.mission.cycle_difficulty(-1)
				elif key in ('d', 'right'):
					self.mission.cycle_difficulty(1)
				elif key in ('return', 'space', 'j'):
					self.try_launch_or_unlock()
			return

		if self.plane.crashed:
			if key == 'r':
				self.launch_mission()
			elif key == 'h':
				self.in_menu = True
			return

		if key == 'g':
			self.plane.toggle_gear()
		elif key in ('f', 'shift_l', 'shift_r'):
			if self.plane.flare_cooldown <= 0 and self.plane.altitude > 5:
				self.plane.deploy_flares()
				self.sfx.play("flare")
		elif key in ('k', 'm'):
			if self.weapons.missile_cooldown <= 0:
				self.weapons.fire_missile(self.plane, self.enemies)
				self.sfx.play("missile")
		elif key in ('l', 'b'):
			if self.weapons.bomb_cooldown <= 0 and self.plane.altitude > 10:
				self.weapons.drop_bomb(self.plane)
				self.sfx.play("bomb")
		elif key == 'e':
			sfx_name = self.weapons.fire_special(self.plane, self.enemies)
			if sfx_name:
				self.sfx.play(sfx_name)

	def key_up(self, event):
		self.keys.discard(event.keysym.lower())

	def loop(self):
		now = time.perf_counter()
		dt = min(0.1, max(0.001, now - self.last_time))
		self.last_time = now

		pad = self.gamepad.poll()

		if self.in_menu:
			if self.mission.menu_notice_timer > 0:
				self.mission.menu_notice_timer = max(0.0, self.mission.menu_notice_timer - dt)

			if self.menu_nav_cooldown > 0:
				self.menu_nav_cooldown = max(0.0, self.menu_nav_cooldown - dt)
			else:
				if pad["toggle_gear"]:
					self.mission.in_armory = not self.mission.in_armory
					self.menu_nav_cooldown = 0.25
				elif self.mission.in_armory:
					if pad["pitch_axis"] > 0.5:
						self.mission.cycle_weapon_item(-1)
						self.menu_nav_cooldown = 0.22
					elif pad["pitch_axis"] < -0.5:
						self.mission.cycle_weapon_item(1)
						self.menu_nav_cooldown = 0.22
					elif pad["throttle_axis"] < -0.5 or pad["throttle_down"]:
						self.mission.cycle_weapon_cat(-1)
						self.menu_nav_cooldown = 0.22
					elif pad["throttle_axis"] > 0.5 or pad["throttle_up"]:
						self.mission.cycle_weapon_cat(1)
						self.menu_nav_cooldown = 0.22
				else:
					if pad["pitch_axis"] > 0.5:
						self.mission.cycle_aircraft(-1)
						self.menu_nav_cooldown = 0.22
					elif pad["pitch_axis"] < -0.5:
						self.mission.cycle_aircraft(1)
						self.menu_nav_cooldown = 0.22
					elif pad["throttle_axis"] < -0.5 or pad["throttle_down"]:
						self.mission.cycle_difficulty(-1)
						self.menu_nav_cooldown = 0.22
					elif pad["throttle_axis"] > 0.5 or pad["throttle_up"]:
						self.mission.cycle_difficulty(1)
						self.menu_nav_cooldown = 0.22

			if pad["fire_gun"] or pad["restart"]:
				if self.menu_nav_cooldown <= 0:
					self.try_launch_or_unlock()
					self.menu_nav_cooldown = 0.25

			self.renderer.render_menu(self.mission, pad["connected"])
			self.root.after(cfg.FPS_MS, self.loop)
			return

		if self.plane.crashed:
			if pad["restart"]:
				self.launch_mission()
			elif pad["toggle_gear"]:
				self.in_menu = True

		if not self.plane.crashed:
			if pad["toggle_gear"]:
				self.plane.toggle_gear()
			if pad["deploy_flares"] and self.plane.flare_cooldown <= 0 and self.plane.altitude > 5:
				self.plane.deploy_flares()
				self.sfx.play("flare")
			if pad["fire_missile"] and self.weapons.missile_cooldown <= 0:
				self.weapons.fire_missile(self.plane, self.enemies)
				self.sfx.play("missile")
			if pad["drop_bomb"] and self.weapons.bomb_cooldown <= 0 and self.plane.altitude > 10:
				self.weapons.drop_bomb(self.plane)
				self.sfx.play("bomb")
			if pad.get("fire_special"):
				sfx_name = self.weapons.fire_special(self.plane, self.enemies)
				if sfx_name:
					self.sfx.play(sfx_name)
			if 'space' in self.keys or 'j' in self.keys or pad["fire_gun"]:
				if self.weapons.gun_cooldown <= 0:
					self.weapons.fire_vulcan(self.plane)
					self.sfx.play("vulcan")

		prev_hp = int(self.plane.hp)
		prev_explosions = len(self.weapons.explosions)

		dx = self.plane.update(self.keys, pad, dt, self.mission.weather, self.carrier)
		self.carrier["x"] -= dx
		if self.carrier["x"] < -450:
			self.carrier["x"] = self.renderer.width + 5200.0
			self.carrier["serviced"] = False

		if self.plane.carrier_event:
			self.weapons.score += 500
			self.weapons.special_cooldown = 0.0
			self.mission.banner_title = "⚓ CARRIER ARRESTED LANDING! ⚓"
			self.mission.banner_subtitle = "+60 HP REPAIRED | SPECIAL REARMED | +500 COINS!"
			self.mission.wave_banner_timer = 3.2
			self.sfx.play("wave_clear")

		self.renderer.update_environment(dx, self.mission.weather, dt)
		self.enemies.update(self.plane, self.weapons, self.mission, dx, dt)
		self.weapons.update(self.plane, dx, self.enemies, self.mission, dt)

		if int(self.plane.hp) < prev_hp:
			self.sfx.play("damage")
		elif len(self.weapons.explosions) > prev_explosions:
			self.sfx.play("explosion")

		if self.enemies.aa_missiles and not self.plane.crashed:
			self.warning_beep_timer -= dt
			if self.warning_beep_timer <= 0:
				self.sfx.play("warning")
				self.warning_beep_timer = 0.55
		else:
			self.warning_beep_timer = 0.0

		wave_advanced = self.mission.update(self.plane, self.weapons.score, dt)
		if wave_advanced:
			self.sfx.play("wave_clear")
			if self.mission.is_boss_wave:
				self.enemies.spawn_boss(self.mission.wave)

		self.renderer.render(self.plane, self.weapons, self.enemies, self.mission, self.carrier)

		self.root.after(cfg.FPS_MS, self.loop)

if __name__ == "__main__":
	root = tk.Tk()
	app = FlightSimApp(root)
	root.mainloop()
