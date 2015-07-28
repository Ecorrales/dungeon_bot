import json
from items import *
from util import *
import random
default_characteristics = {
	"strength": 5, #how hard you hit
	"vitality": 5, #how much hp you have
	"dexterity": 5, #how much energy you have, your position in turn qeue
	"intelligence": 5, #how likely you are to cause critical effects when attacking
	"faith": 5, #how much energy you have
}

default_equipment = {
	"armor": None,
	"primary_weapon": None,
	"secondary_weapon": None,
	"ring": None,
	"talisman": None,
	"headwear": None
}

default_abilties = []

class Creature(object):
	def __init__(self, name, race, combat_class, level=1, characteristics = default_characteristics, stats=None, description=None, inventory=[], equipment=default_equipment, tags=[],abilities=[], modifiers = []):

		self.uid = get_uid()
		self.name = name
		self.race = race
		self.combat_class = combat_class
		self.description = description
		self.event = None
		self._level = level


		self.modifiers = modifiers.copy()
		self.characteristics = characteristics.copy()
		
		self.tags = tags.copy()
		self.abilities = abilities + default_abilties.copy()

		self.inventory = inventory.copy()
		self.equipment = equipment.copy()

		self.base_stats = self.get_base_stats_from_characteristics(self.characteristics)

		if stats:
			self.stats = stats.copy()
		else:
			self.stats = self.base_stats

		self.dead = False
		self.refresh_abilities()
		self.refresh_modifiers()

	def get_base_stats_from_characteristics(self, characteristics): #stats are completely derived from characteristics
		stats =  {
			"health": 0,
			"energy": 0,
			"max_health": 0,
			"max_energy": 0,
			"energy_regen": 0
		}

		stats["max_health"] = characteristics["vitality"]* 10
		stats["max_energy"] = characteristics["dexterity"]
		stats["energy_regen"] = clamp(int(characteristics["dexterity"] / 3), 2, 10)
		stats["health"] = stats["max_health"]
		stats["energy"] = stats["max_energy"]
		return stats

	@property
	def health(self):
		return self.stats["health"]

	@health.setter
	def health(self, value):
		if value > self.stats["max_health"]:
			value = self.stats["max_health"]
		if value < 0:
			value = 0
		self.stats["health"] = value

	@property
	def energy(self):
		return self.stats["energy"]

	@energy.setter
	def energy(self, value):
		if value > self.stats["max_energy"]:
			value = self.stats["max_energy"]
		if value < 0:
			value = 0
		self.stats["energy"] = value

	@property
	def primary_weapon(self):
		return self.equipment["primary_weapon"]

	@primary_weapon.setter
	def primary_weapon(self, value):
		self.equipment["primary_weapon"] = value

	@property
	def armor(self):
		return self.equipment["armor"]

	@armor.setter
	def armor(self, value):
		self.equipment["armor"] = value

	@property
	def secondary_weapon(self):
		return self.equipment["secondary_weapon"]

	@secondary_weapon.setter
	def secondary_weapon(self, value):
		self.equipment["secondary_weapon"] = value

	@property
	def ring(self):
		return self.equipment["ring"]

	@ring.setter
	def ring(self, value):
		self.equipment["ring"] = value

	@property
	def talisman(self):
		return self.equipment["talisman"]

	@talisman.setter
	def talisman(self, value):
		self.equipment["talisman"] = value

	@property
	def headwear(self):
		return self.equipment["headwear"]

	@headwear.setter
	def headwear(self, value):
		self.equipment["headwear"] = value

	@property
	def defence(self):
		base_def = diceroll("1d1")
		defence = base_def
		for key in list(self.equipment.keys()):
			if self.equipment[key] and "defence" in list(self.equipment[key].stats.keys()):
				defence += diceroll(self.equipment[key]["defence"])

		#todo defence from modifiers
		#todo defence from level perks

		return defence

	@property
	def evasion(self):
		base_ev = diceroll("1d1")
		evasion = base_ev
		for key in list(self.equipment.keys()):
			if self.equipment[key] and "evasion" in list(self.equipment[key].stats.keys()):
				evasion += diceroll(self.equipment[key]["evasion"])

		#todo evasion from modifiers
		#todo evasion from level perks
		return evasion


	@property
	def level(self):
		return self._level

	@level.setter
	def level(self, value):
		self._level = value

	def apply_combat_start_effects(self):
		pass

	def apply_combat_over_effects(self):
		self.energy = self.stats["max_energy"]

	def apply_turn_effects(self):
		#regenerate energy
		self.energy += self.stats["energy_regen"]
		#apply the effects of all modifiers

	def kill_if_nececary(self, killer=None):
		if self.health <= 0:
			return True, self.die(killer)
		return False, None

	def die(self, killer=None):
		self.dead = True
		if killer:
			return "%s is killed by %s."%(self.name, killer.name)
		return "%s dies."%(self.name)

	def examine_equipment(self):
		desc = "%s's equipment:\n"%(self.name)
		for key in self.equipment.keys():
			item = self.equipment[key]
			if item:
				desc+="%s: %s.\n"%(key, item.name)
		return desc

	def examine_inventory(self):
		desc = "%s's inventory:\n"%(self.name)
		items = []
		for i in range(len(self.inventory)):
			item = self.inventory[i]
			if item:
				items.append(str(i+1)+"."+item.name)
		return desc + ', '.join(items)

	def refresh_modifiers(self):
		pass

	def refresh_abilities(self):
		self.abilities = default_abilties
		for perk in self.level_perks:
			for ability in perk.abilities_granted:
				self.abilities.append({"granted_by":perk, "ability_name": ability})

		for modifier in self.modifiers:
			for ability in modifier.abilities_granted:
				self.abilities.append({"granted_by":modifier, "ability_name": ability})

		for key in self.equipment.keys():
			if self.equipment[key]:
				for ability in self.equipment[key].abilities_granted:
					self.abilities.append({"granted_by":self.equipment[key], "ability_name": ability})

	def examine_self(self):
		desc = ""
		if self.name:
			desc+="You see %s.\n"%(self.name)
		desc+="It's a %s %s.\n"%(self.combat_class, self.race)
		desc+="It has %d health and %d energy.\n"%(self.health, self.energy)
		desc += "It has the following abilities:\n"
		desc += ", ".join(["%s(%s)"%(ab["ability_name"], ab["granted_by"].name) for ab in self.abilities])
		if len(self.modifiers) > 0:
			desc += "It has the following modifiers:\n"
			for modifier in self.modifiers:
				desc += "  %s\n"%(modifier)
		if self.description:
			desc+="%s\n"%(self.description)
		return desc


	def to_json(self):
		big_dict = self.__dict__.copy()
		del big_dict["uid"]
		big_dict["characteristics"] = json.dumps(self.characteristics)
		# big_dict["tags"] = json.dumps(self.tags)
		del big_dict["abilities"] #abilities are not serializable
		del big_dict["modifiers"] #modifiers are derived so no point in serializing them
		big_dict["inventory"] = []
		for item in self.inventory:
			big_dict["inventory"].append(item.to_json())
		big_dict["equipment"] = default_equipment.copy()
		for key in self.equipment:
			if self.equipment[key]:
				big_dict["equipment"][key] = self.equipment[key].to_json()
		#big_dict["equipment"] = json.dumps(big_dict["equipment"])
		return big_dict

class Player(Creature):
	def __init__(self, username, name, race, combat_class, level=1, characteristics = default_characteristics, stats=None, description=None, inventory=[], equipment=default_equipment, tags=["animate", "humanoid"],abilities=[],modifiers=[], level_perks=[], experience=0, max_experience=1000):
		Creature.__init__(self, name, race, combat_class, level, characteristics, stats, description, inventory, equipment, tags, abilities, modifiers)
		self.level_perks = level_perks.copy()
		self._experience = experience
		self.max_experience = max_experience
		self.username = username

	@property
	def experience(self):
		return self._experience

	@experience.setter
	def experience(self, value):
		if value > self.max_experience:
			over_cur_level = value - (self.max_experience - self.experience)
			self.level = self.level +  1
			self.experience = over_cur_level
		else:
			self._experience = value

	@property
	def level(self):
		return self._level

	@level.setter
	def level(self, value):
		self._level = value
		self.max_experience = value * 1000

	def examine_self(self):
		desc = super(Player, self).examine_self()
		desc += "It is of level %d.\n"%(self.level)
		return desc

	@staticmethod
	def de_json(data):
		if isinstance(data, str):
			data = json.loads(data)
		data["characteristics"] = json.loads(data["characteristics"])
		stats = None
		if "stats" in list(data.keys()):
			stats = data["stats"]
			if isinstance(data["stats"], str):
				data["stats"] = json.loads(data["stats"])
				stats = data["stats"]

		for i in range(len(data["inventory"])):
			data["inventory"][i] = Item.de_json(data["inventory"][i])

		equipment = default_equipment.copy()
		eq = data["equipment"]
		for key in list(eq.keys()):
			if eq[key]:
				equipment[key] = Item.de_json(eq[key])

		data["equipment"] = equipment
		ply = Player(data.get("username"), data.get("name"), data.get("race"), data.get("combat_class"), data.get("_level"), data.get("characteristics"), stats, data.get("description"), data.get("inventory"), data.get("equipment"), data.get('tags'), [], [], data.get("level_perks"), data.get("_experience"), data.get("max_experience"))
		return ply

	def to_json(self):
		big_dict = super(Player, self).to_json()
		#big_dict["level_perks"] = json.dumps(self.level_perks)
		big_dict["username"] = self.username
		big_dict["event"] = None
		return big_dict

	def __str__(self):
		return self.examine_self()

class Enemy(Creature):
	def __init__(self, name, race, combat_class, level=1, characteristics = default_characteristics, stats=None, description=None, inventory=[], equipment=default_equipment, tags=[],abilities=[],modifiers=[], exp_value=0):
		Creature.__init__(self, name, race, combat_class, level, characteristics, stats, description, inventory, equipment, tags, abilities, modifiers)
		self.exp_value = exp_value

	def act(self):
		return "Base enemy has no AI"

	def die(self, killer=None):
		self.dead = True
		if killer:
			msg = "%s is killed by %s.\n"%(self.name, killer.name)
			if isinstance(killer, Player):
				killer.experience += self.exp_value
				msg += "%s earns %d experience.\n"%(killer.name, self.exp_value)

				drop_table = self.__class__.drop_table
				for probability in list(drop_table.keys()):
					prob = int(probability)
					got_item = random.randint(0, 100) <= prob 
					if got_item:
						item = get_item_by_name(drop_table[probability], self.__class__.loot_coolity)
						killer.inventory.append(item)
						msg += "%s got loot: %s."%(killer.name.title(), item.name)
			return msg
		return "%s dies."%(self.name)

	@staticmethod
	def de_json(data):
		data["characteristics"] = json.loads(data["characteristics"])

		stats = None
		if "stats" in list(data.keys()):
			data["stats"] = json.loads(data["stats"])
			stats = data["stats"]
					
		for i in range(len(data["inventory"])):
			data["inventory"][i] = Item.de_json(data["inventory"][i])

		equipment = default_equipment.copy()
		eq = data["equipment"]
		for key in list(eq.keys()):
			if eq[key]:
				equipment[key] = Item.de_json(eq[key])
		data["equipment"] = equipment

		en =  Enemy(data.get("name"), data.get("race"), data.get("combat_class"), data.get("level"), data.get("characteristics"), stats, data.get("description"), inventory, equipment, data.get('tags'), [], [])
		return en

