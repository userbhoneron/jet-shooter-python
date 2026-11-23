import json
import os
import config as cfg

SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscore.json")

class MissionManager:
	def __init__(self):
		self.aircraft_names = list(cfg.AIRCRAFT_PRESETS.keys())
		self.difficulty_names = list(cfg.DIFFICULTY_PRESETS.keys())

		self.weapon_categories = ["vulcan", "missile", "bomb"]
		self.weapon_lists = {
			cat: list(cfg.WEAPON_SHOP[cat].keys())
			for cat in self.weapon_categories
		}

		self.selected_aircraft_idx = 0
		self.selected_difficulty_idx = 1  # Default: Ace
		self.in_armory = False
		self.selected_weapon_cat_idx = 0
		self.selected_weapon_idx = {"vulcan": 0, "missile": 0, "bomb": 0}

		self.high_score = 0
		self.best_wave = 1
		self.coins = 0
		self.unlocked_aircraft = ["F-16 Viper"]
		self.unlocked_weapons = {
			"vulcan": ["Standard 20mm"],
			"missile": ["AIM-9 Sidewinder"],
			"bomb": ["Mk-82 Iron Bomb"]
		}
		self.equipped_weapons = {
			"vulcan": "Standard 20mm",
			"missile": "AIM-9 Sidewinder",
			"bomb": "Mk-82 Iron Bomb"
		}

		self.menu_notice = ""
		self.menu_notice_timer = 0.0
		self.load_progress()
		self.reset()

	def load_progress(self):
		if os.path.exists(SAVE_FILE):
			try:
				with open(SAVE_FILE, "r", encoding="utf-8") as f:
					data = json.load(f)
					self.high_score = int(data.get("high_score", 0))
					self.best_wave = int(data.get("best_wave", 1))
					self.coins = int(data.get("coins", 0))
					saved_jets = data.get("unlocked_aircraft", ["F-16 Viper"])
					if isinstance(saved_jets, list) and saved_jets:
						self.unlocked_aircraft = saved_jets
					saved_weps = data.get("unlocked_weapons")
					if isinstance(saved_weps, dict):
						for cat in self.weapon_categories:
							if cat in saved_weps and saved_weps[cat]:
								self.unlocked_weapons[cat] = saved_weps[cat]
					saved_eq = data.get("equipped_weapons")
					if isinstance(saved_eq, dict):
						for cat in self.weapon_categories:
							if saved_eq.get(cat) in cfg.WEAPON_SHOP[cat]:
								self.equipped_weapons[cat] = saved_eq[cat]
			except (OSError, ValueError):
				pass

	def save_progress(self):
		try:
			with open(SAVE_FILE, "w", encoding="utf-8") as f:
				json.dump({
					"high_score": self.high_score,
					"best_wave": self.best_wave,
					"coins": self.coins,
					"unlocked_aircraft": self.unlocked_aircraft,
					"unlocked_weapons": self.unlocked_weapons,
					"equipped_weapons": self.equipped_weapons
				}, f, indent=2)
		except OSError:
			pass

	@property
	def aircraft_name(self):
		return self.aircraft_names[self.selected_aircraft_idx]

	@property
	def difficulty_name(self):
		return self.difficulty_names[self.selected_difficulty_idx]

	@property
	def difficulty_stats(self):
		return cfg.DIFFICULTY_PRESETS[self.difficulty_name]

	@property
	def current_weapon_cat(self):
		return self.weapon_categories[self.selected_weapon_cat_idx]

	@property
	def current_weapon_name(self):
		cat = self.current_weapon_cat
		return self.weapon_lists[cat][self.selected_weapon_idx[cat]]

	def is_unlocked(self, name):
		return name in self.unlocked_aircraft or cfg.AIRCRAFT_PRESETS[name]["cost"] == 0

	def is_weapon_unlocked(self, cat, name):
		return name in self.unlocked_weapons[cat] or cfg.WEAPON_SHOP[cat][name]["cost"] == 0

	def try_unlock_selected(self):
		name = self.aircraft_name
		if self.is_unlocked(name):
			return "already"
		cost = cfg.AIRCRAFT_PRESETS[name]["cost"]
		if self.coins >= cost:
			self.coins -= cost
			self.unlocked_aircraft.append(name)
			self.save_progress()
			self.menu_notice = f"UNLOCKED {name.upper()}!"
			self.menu_notice_timer = 2.5
			return "unlocked"
		else:
			needed = cost - self.coins
			self.menu_notice = f"NEED {needed} MORE COINS TO UNLOCK {name.upper()}!"
			self.menu_notice_timer = 2.5
			return "insufficient"

	def try_buy_or_equip_weapon(self):
		cat = self.current_weapon_cat
		name = self.current_weapon_name
		if self.is_weapon_unlocked(cat, name):
			self.equipped_weapons[cat] = name
			self.save_progress()
			self.menu_notice = f"EQUIPPED {name.upper()}!"
			self.menu_notice_timer = 2.0
			return "equipped"
		cost = cfg.WEAPON_SHOP[cat][name]["cost"]
		if self.coins >= cost:
			self.coins -= cost
			self.unlocked_weapons[cat].append(name)
			self.equipped_weapons[cat] = name
			self.save_progress()
			self.menu_notice = f"PURCHASED & EQUIPPED {name.upper()}!"
			self.menu_notice_timer = 2.5
			return "unlocked"
		else:
			needed = cost - self.coins
			self.menu_notice = f"NEED {needed} MORE COINS FOR {name.upper()}!"
			self.menu_notice_timer = 2.5
			return "insufficient"

	def add_cheat_coins(self, amount=10000):
		self.coins += amount
		self.save_progress()
		self.menu_notice = f"DEV CHEAT: +{amount} COINS ADDED!"
		self.menu_notice_timer = 2.5

	def cycle_aircraft(self, delta):
		self.selected_aircraft_idx = (self.selected_aircraft_idx + delta) % len(self.aircraft_names)

	def cycle_difficulty(self, delta):
		self.selected_difficulty_idx = (self.selected_difficulty_idx + delta) % len(self.difficulty_names)

	def cycle_weapon_cat(self, delta):
		self.selected_weapon_cat_idx = (self.selected_weapon_cat_idx + delta) % len(self.weapon_categories)

	def cycle_weapon_item(self, delta):
		cat = self.current_weapon_cat
		items = self.weapon_lists[cat]
		self.selected_weapon_idx[cat] = (self.selected_weapon_idx[cat] + delta) % len(items)

	def reset(self):
		self.wave = 1
		self.last_score = 0
		self.weather_modes = ["CLEAR DAY", "GOLDEN SUNSET", "NIGHT RAID", "THUNDERSTORM"]
		self.weather = "CLEAR DAY"
		self.wave_banner_timer = 0.0
		self.banner_title = ""
		self.banner_subtitle = ""
		self.setup_wave(1)

	def setup_wave(self, wave_num):
		self.wave = wave_num
		self.is_boss_wave = (wave_num % 3 == 0)
		self.weather = self.weather_modes[(wave_num - 1) % len(self.weather_modes)]

		self.req_ground = 2 + (wave_num // 2) if not self.is_boss_wave else 0
		self.req_air = 2 + wave_num if not self.is_boss_wave else 0
		self.req_boss = 1 if self.is_boss_wave else 0

		self.kills_ground = 0
		self.kills_air = 0
		self.kills_boss = 0

		if self.is_boss_wave:
			self.banner_title = f"⚠ WAVE {wave_num}: BOSS [{self.weather}] ⚠"
			self.banner_subtitle = "DESTROY THE SKY FORTRESS COMMAND SHIP!"
		else:
			self.banner_title = f"WAVE {wave_num}: {self.weather}"
			self.banner_subtitle = f"DESTROY {self.req_air} AIRCRAFT & {self.req_ground} GROUND TARGETS"
		self.wave_banner_timer = 3.2

	def record_kill(self, category):
		if category == "ground":
			self.kills_ground += 1
		elif category == "air":
			self.kills_air += 1
		elif category == "boss":
			self.kills_boss += 1

	def is_wave_complete(self):
		if self.is_boss_wave:
			return self.kills_boss >= self.req_boss
		return self.kills_ground >= self.req_ground and self.kills_air >= self.req_air

	def get_objective_text(self):
		if self.is_boss_wave:
			return f"OBJ [WAVE {self.wave} BOSS]: SKY FORTRESS {self.kills_boss}/{self.req_boss}"
		return f"OBJ [WAVE {self.wave}]: AIR {self.kills_air}/{self.req_air} | GND {self.kills_ground}/{self.req_ground}"

	def update(self, plane, current_score, dt):
		if current_score > self.last_score:
			earned = current_score - self.last_score
			self.coins += earned
			self.last_score = current_score
			if current_score > self.high_score:
				self.high_score = current_score
			self.save_progress()

		if self.wave_banner_timer > 0:
			self.wave_banner_timer = max(0.0, self.wave_banner_timer - dt)

		if not plane.crashed and self.is_wave_complete():
			next_wave = self.wave + 1
			if next_wave > self.best_wave:
				self.best_wave = next_wave
			self.save_progress()
			plane.hp = min(plane.max_hp, plane.hp + cfg.WAVE_REPAIR_BONUS)
			self.setup_wave(next_wave)
			return True
		return False
