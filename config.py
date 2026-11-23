# Screen & Loop Settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
START_FULLSCREEN = True
PLANE_X_RATIO = 0.38
FPS_MS = 16
GROUND_HEIGHT = 80

# Aircraft Physics & Combat (Per-Second Rates)
BASE_CRUISE_SPEED = 140.0
MAX_SPEED_MULTIPLIER = 3.0
HORIZ_SPEED_SCALE = 3.6
THROTTLE_RATE = 60.0
PITCH_SPEED = 100.0
MAX_PITCH = 65.0
STALL_SPEED = 65.0
GRAVITY = 9.8
LIFT_POWER = 22.0
GEAR_SPEED = 2.5
GEAR_DRAG_FACTOR = 0.85

PLAYER_MAX_HP = 100
FLARE_COOLDOWN = 0.36
FLARE_LIFETIME = 2.2
FLARE_BURST_COUNT = 4

# 12-Aircraft Progressive Unlock Roster (with Stealth & Signature Special Weapons)
AIRCRAFT_PRESETS = {
	"F-16 Viper": {
		"cost": 0,
		"role": "Tier 1 • Special: Afterburner Overdrive [E]",
		"max_hp": 100,
		"speed_mult": 3.0,
		"pitch_speed": 100.0,
		"missile_cd": 0.50,
		"bomb_cd": 0.50,
		"regen_rate": 0.0,
		"stealth": 0.0,
		"special": "OVERDRIVE",
		"special_cd": 7.0,
		"color": "#63707E",
		"accent": "#D9381E"
	},
	"MiG-29 Fulcrum": {
		"cost": 800,
		"role": "Tier 1.5 • Special: Afterburner Overdrive [E]",
		"max_hp": 105,
		"speed_mult": 3.2,
		"pitch_speed": 112.0,
		"missile_cd": 0.48,
		"bomb_cd": 0.55,
		"regen_rate": 0.0,
		"stealth": 0.0,
		"special": "OVERDRIVE",
		"special_cd": 6.5,
		"color": "#556B7D",
		"accent": "#FF3333"
	},
	"A-10 Thunderbolt II": {
		"cost": 1200,
		"role": "Tier 2 • Special: GAU-8 Avenger Burst [E]",
		"max_hp": 185,
		"speed_mult": 2.2,
		"pitch_speed": 85.0,
		"missile_cd": 0.42,
		"bomb_cd": 0.18,
		"regen_rate": 0.0,
		"stealth": 0.0,
		"special": "GAU-8",
		"special_cd": 4.5,
		"color": "#4B5320",
		"accent": "#FFD700"
	},
	"F-15 Strike Eagle": {
		"cost": 1800,
		"role": "Tier 2 • Special: 5x Carpet Bomb Salvo [E]",
		"max_hp": 140,
		"speed_mult": 3.0,
		"pitch_speed": 94.0,
		"missile_cd": 0.30,
		"bomb_cd": 0.28,
		"regen_rate": 0.0,
		"stealth": 0.025,
		"special": "CARPET",
		"special_cd": 5.5,
		"color": "#4A5664",
		"accent": "#E69F00"
	},
	"F/A-18 Super Hornet": {
		"cost": 2600,
		"role": "Tier 3 • Special: 3x Missile Volley [E]",
		"max_hp": 135,
		"speed_mult": 3.35,
		"pitch_speed": 108.0,
		"missile_cd": 0.32,
		"bomb_cd": 0.32,
		"regen_rate": 0.0,
		"stealth": 0.075,
		"special": "VOLLEY",
		"special_cd": 5.0,
		"color": "#5C6875",
		"accent": "#00BFFF"
	},
	"YF-23 Black Widow": {
		"cost": 3800,
		"role": "Tier 3 • Special: 3x Stealth Missile Volley [E]",
		"max_hp": 115,
		"speed_mult": 3.8,
		"pitch_speed": 124.0,
		"missile_cd": 0.38,
		"bomb_cd": 0.52,
		"regen_rate": 0.0,
		"stealth": 0.325,
		"special": "VOLLEY",
		"special_cd": 4.5,
		"color": "#2B303A",
		"accent": "#00FFFF"
	},
	"F-22 Raptor": {
		"cost": 5200,
		"role": "Tier 4 • Special: 3x Raptor Missile Volley [E]",
		"max_hp": 150,
		"speed_mult": 4.0,
		"pitch_speed": 135.0,
		"missile_cd": 0.26,
		"bomb_cd": 0.36,
		"regen_rate": 0.0,
		"stealth": 0.35,
		"special": "VOLLEY",
		"special_cd": 4.0,
		"color": "#3C4652",
		"accent": "#38BDF8"
	},
	"Su-57 Felon": {
		"cost": 7000,
		"role": "Tier 4 • Special: 3x Canard Missile Volley [E]",
		"max_hp": 165,
		"speed_mult": 4.2,
		"pitch_speed": 138.0,
		"missile_cd": 0.26,
		"bomb_cd": 0.34,
		"regen_rate": 0.0,
		"stealth": 0.25,
		"special": "VOLLEY",
		"special_cd": 3.8,
		"color": "#384B59",
		"accent": "#FF3366"
	},
	"SR-71 Blackbird": {
		"cost": 9500,
		"role": "Tier 5 • Special: Tactical Laser Beam [E]",
		"max_hp": 130,
		"speed_mult": 5.8,
		"pitch_speed": 105.0,
		"missile_cd": 0.35,
		"bomb_cd": 0.60,
		"regen_rate": 0.0,
		"stealth": 0.225,
		"special": "TLS",
		"special_cd": 5.5,
		"color": "#181C24",
		"accent": "#FF4500"
	},
	"B-2 Spirit Stealth": {
		"cost": 12000,
		"role": "Tier 5 • Special: 5x Carpet Bomb Salvo [E]",
		"max_hp": 240,
		"speed_mult": 3.5,
		"pitch_speed": 88.0,
		"missile_cd": 0.25,
		"bomb_cd": 0.12,
		"regen_rate": 1.0,
		"stealth": 0.425,
		"special": "CARPET",
		"special_cd": 3.5,
		"color": "#1E222B",
		"accent": "#A855F7"
	},
	"X-37 Orbital Valkyrie": {
		"cost": 15500,
		"role": "Tier 6 • Special: Orbital Laser Beam [E]",
		"max_hp": 200,
		"speed_mult": 5.0,
		"pitch_speed": 145.0,
		"missile_cd": 0.22,
		"bomb_cd": 0.25,
		"regen_rate": 3.5,
		"stealth": 0.30,
		"special": "TLS",
		"special_cd": 4.2,
		"color": "#161B22",
		"accent": "#FFD700"
	},
	"ADF-01 Falken": {
		"cost": 25000,
		"role": "Tier 7 • Special: Heavy Tactical Laser [E]",
		"max_hp": 260,
		"speed_mult": 6.2,
		"pitch_speed": 165.0,
		"missile_cd": 0.15,
		"bomb_cd": 0.18,
		"regen_rate": 5.0,
		"stealth": 0.375,
		"special": "TLS",
		"special_cd": 3.0,
		"color": "#4A0404",
		"accent": "#00FFFF"
	}
}


# Selectable Difficulty Presets
DIFFICULTY_PRESETS = {
	"Cadet": {
		"sam_fire_chance": 0.25,
		"aa_turn_rate": 80.0,
		"aa_damage": 15,
		"enemy_fire_cd": 6.0
	},
	"Ace": {
		"sam_fire_chance": 0.45,
		"aa_turn_rate": 100.0,
		"aa_damage": 25,
		"enemy_fire_cd": 4.8
	},
	"Top Gun": {
		"sam_fire_chance": 0.70,
		"aa_turn_rate": 122.0,
		"aa_damage": 35,
		"enemy_fire_cd": 3.6
	}
}

# Ordnance Armory Store (Vulcan, Missiles, Bombs)
WEAPON_SHOP = {
	"vulcan": {
		"Standard 20mm": {
			"cost": 0,
			"desc": "Balanced 20mm rotary cannon (18 dmg)",
			"dmg": 18,
			"cd_mult": 1.0,
			"color": "#FFD700"
		},
		"Twin Rotary Gatling": {
			"cost": 1500,
			"desc": "Dual parallel barrels (2x14 dmg, wide spread)",
			"dmg": 14,
			"cd_mult": 1.05,
			"color": "#FFA500"
		},
		"30mm Depleted Uranium": {
			"cost": 2800,
			"desc": "A-10 Warthog DU armor-piercing rounds (34 dmg, pierces)",
			"dmg": 34,
			"cd_mult": 1.15,
			"color": "#ADFF2F"
		},
		"Explosive HEI Rounds": {
			"cost": 3800,
			"desc": "High-explosive incendiary shells (24 dmg + splash)",
			"dmg": 24,
			"cd_mult": 1.25,
			"color": "#FF4500"
		},
		"Hyper-Velocity Rail Slugs": {
			"cost": 5500,
			"desc": "Mach 6 tungsten rail bolts (48 dmg, full pierce)",
			"dmg": 48,
			"cd_mult": 1.45,
			"color": "#00FFFF"
		}
	},
	"missile": {
		"AIM-9 Sidewinder": {
			"cost": 0,
			"desc": "Standard heat-seeking AAM (120 dmg, 425 deg/s)",
			"dmg": 120,
			"turn_rate": 425.0,
			"cd_mult": 1.0,
			"blast": 0
		},
		"Python High-G Seeker": {
			"cost": 2000,
			"desc": "Extreme 750 deg/s off-boresight dogfight missile",
			"dmg": 135,
			"turn_rate": 750.0,
			"cd_mult": 0.95,
			"blast": 0
		},
		"Swarm Micro-Pods (3x)": {
			"cost": 4200,
			"desc": "Launches 3 agile micro-missiles per trigger pull (3x55 dmg)",
			"dmg": 55,
			"turn_rate": 560.0,
			"cd_mult": 1.25,
			"blast": 0
		},
		"Heavy Phoenix Cruise": {
			"cost": 6800,
			"desc": "Long-range warhead (280 dmg + 110px proximity blast)",
			"dmg": 280,
			"turn_rate": 380.0,
			"cd_mult": 1.55,
			"blast": 110
		}
	},
	"bomb": {
		"Mk-82 Iron Bomb": {
			"cost": 0,
			"desc": "Standard unguided 500lb bomb (70px blast)",
			"blast": 70,
			"cd_override": None
		},
		"Cluster Munition (CBU)": {
			"cost": 2200,
			"desc": "Splits at 140m alt into 4 scattering sub-bomblets",
			"blast": 65,
			"cd_override": 0.75
		},
		"JDAM Laser-Guided": {
			"cost": 4500,
			"desc": "Steers mid-air onto the nearest ground target or SAM",
			"blast": 90,
			"cd_override": 0.65
		},
		"B61 Tactical Nuke": {
			"cost": 12000,
			"desc": "650px ground obliteration + 320 Boss shockwave (3.5s CD)",
			"blast": 650,
			"cd_override": 3.5
		}
	}
}

# Landing Limits
MAX_SAFE_VSPEED = -22.0
MAX_SAFE_PITCH = 16.0

# Atmosphere & Space Thresholds (Meters)
STRATOSPHERE_ALT = 1400.0
SPACE_ALT = 2800.0
ZERO_AIR_ALT = 3000.0
STAR_FADE_START = 900.0

# Player Weapons & Lock-On
GUN_COOLDOWN = 0.06
BULLET_SPEED_ADD = 450.0
BULLET_LIFETIME = 0.9

BOMB_COOLDOWN = 0.5
BOMB_GRAVITY_MULT = 12.0

MISSILE_COOLDOWN = 0.5
MISSILE_SPEED = 680.0
MISSILE_ACCEL = 480.0
MISSILE_TURN_RATE = 425.0
MISSILE_LIFETIME = 2.8
LOCK_ON_RANGE = 1850.0
TARGET_COUNT = 5

# Enemy Jets, Slow Gunships & AA Missiles
ENEMY_JET_COUNT = 1
ENEMY_JET_SPEED = 220.0
ENEMY_FIRE_COOLDOWN = 4.8

SLOW_ENEMY_COUNT = 2
SLOW_ENEMY_SPEED = 110.0

SAM_COUNT = 2
SAM_FIRE_COOLDOWN = 4.4
SAM_FIRE_CHANCE = 0.45
SAM_LOCK_DELAY = 0.36
SAM_RANGE = 1600.0
MAX_ACTIVE_AA_MISSILES = 2

AA_MISSILE_SPEED = 490.0
AA_TURN_RATE = 100.0
AA_MISSILE_LIFETIME = 3.1
AA_MISSILE_DAMAGE = 25

# Wave Progression & Boss Settings
WAVE_REPAIR_BONUS = 25
BOSS_BASE_HP = 8000
BOSS_SPEED = 95.0
