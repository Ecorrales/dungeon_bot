from util import *
class Item(object):
	def __init__(self, name, description, item_type,  stats = {},  abilities_granted = [], modifiers_granted = [], requirements = None):
		self.name = name
		self.description = description
		self.requirements = requirements.copy()
		self.item_type = item_type
		self.uid = get_uid()
		self.abilities_granted = abilities_granted.copy()
		self.stats = stats.copy()
		self.modifiers_granted = modifiers_granted.copy()

	def use(self, target):
		return "Can't use %s."%(self.name)

	def equip(self, target):
		if self.item_type == "consumable":
			return "Can't equip %s."%(self.name)

		if target[self.item_type] == self:
			return "Already equipped %s."%(self.name)

		if target[self.item_type]:
			temp = target[self.item_type]
			temp.unequip(target)

		target[self.item_type] = self
		for item in target.inventory:
			if item == self:
				target.inventory.remove(item)

		target.refresh_abilities()
		return "Succesfully equipped %s."%(self.name)
		

	def unequip(self, target):
		if self.item_type == "consumable":
			return "Can't unequip %s."%(self.name)
		if target[self.item_type] == self:
			target[self.item_type] = None
			target.inventory.append(self)
			target.refresh_abilities()
			return "Succesfully unequipped %s."%(self.name)
		return "Not equipped!"

	def destroy(self, target):
		self.unequip(target)
		for item in target.inventory:
			if item == self:
				target.inventory.remove(item)
		del self
		return "Succesfully destroyed."

	def examine_self(self):
		desc = "%s, a %s.\n"%(self.name.title(), self.item_type )
		if self.requirements:
			desc += "Requirements to use:\n"+str(self.requirements)+'\n'
		desc += "Stats:\n"+str(self.stats) +'\n'
		desc += "Abilities:\n"+str(self.abilities_granted)+'\n'
		desc += "Modifiers granted:\n"+str(self.modifiers_granted)+'\n'
		return desc

	def to_json(self):
		big_dict = self.__dict__.copy()
		big_dict["requirements"] = self.requirements
		big_dict["abilities_granted"] = self.abilities_granted
		big_dict["stats"] = self.stats
		big_dict["modifiers_granted"] = self.modifiers_granted
		return big_dict

	@staticmethod
	def de_json(data):
		if data.get("item_type") == "primary_weapon":
			return PrimaryWeapon.de_json(data)
		print('wrong item type')



default_weapon_stats= {
	"damage" : "1d1",
	"accuracy" : "1d1",
}

default_weapon_requirements = {
	"strength": 0, 
	"vitality": 0, 
	"dexterity": 0,
	"intelligence": 0, 
	"faith": 0, 
}	

default_weapon_abilities = []
class PrimaryWeapon(Item):
	def __init__(self, name, description, item_type="primary_weapon", stats=default_weapon_stats, abilities_granted = default_weapon_abilities, modifiers_granted = [], requirements = default_weapon_requirements):
		Item.__init__(self, name, description, item_type, stats, abilities_granted, modifiers_granted, requirements)

	@staticmethod
	def get_randomized_item(coolity, stats, item_args):
		real_stats = stats.copy()
		damage_range = stats["damage"]
		accuracy_range = stats["accuracy"]
		real_stats["damage"] = get_dice_in_range(damage_range, coolity) 
		real_stats["accuracy"] = get_dice_in_range(accuracy_range, coolity)
		if not "modifiers_granted" in list(item_args.keys()):
			 item_args["modifiers_granted"] = []
		if not "requirements" in list(item_args.keys()):
			 item_args["requirements"] = []
		if not "abilities_granted" in list(item_args.keys()):
			 item_args["abilities_granted"] = []
		return PrimaryWeapon(item_args["name"], item_args["description"], "primary_weapon", real_stats, item_args["abilities_granted"], item_args["modifiers_granted"], item_args["requirements"])

	@staticmethod
	def de_json(data):
		return PrimaryWeapon(data.get('name'), data.get('description'), data.get("item_type"), data.get('stats'), data.get("abilities_granted"), data.get("modifiers_granted"), data.get("requirements"))

class SecondaryWeapon(Item):
	def __init__(self, name, description, item_type="secondary_weapon", stats=default_weapon_stats, abilities_granted = default_weapon_abilities, modifiers_granted = [], requirements = default_weapon_requirements):
		Item.__init__(self, name, description, item_type, stats, abilities_granted, modifiers_granted, requirements)

	@staticmethod
	def get_randomized_item(stats, item_args, coolity):
		real_stats = stats.copy()
		if "damage" in list(stats.keys()): #its a damaging weapon, like a dagger
			damage_range = stats["damage"]
			accuracy_range = stats["accuracy"]
			real_stats["damage"] = get_dice_in_range(damage_range, coolity) 
			real_stats["accuracy"] = get_dice_in_range(accuracy_range, coolity)
		if "defence" in list(stats.keys()): #its a shield
			defence_range = stats["defence"]
			evasion_range = stats["evasion"]
			real_stats["defence"] = get_dice_in_range(defence_range, coolity) 
			real_stats["evasion"] = get_dice_in_range(evasion_range, coolity)
		if not "modifiers_granted" in list(item_args.keys()):
			 item_args["modifiers_granted"] = []
		if not "requirements" in list(item_args.keys()):
			 item_args["requirements"] = []
		if not "abilities_granted" in list(item_args.keys()):
			 item_args["abilities_granted"] = []
		return SecondaryWeapon(item_args["name"], item_args["description"], "primary_weapon", real_stats, item_args["abilities_granted"], item_args["modifiers_granted"], item_args["requirements"])

	@staticmethod
	def de_json(data):
		return PrimaryWeapon(data.get('name'), data.get('description'), data.get("item_type"), data.get('stats'), data.get("abilities_granted"), data.get("modifiers_granted"), data.get("requirements"))

def get_item_by_name(name, coolity=0):
	item_args = None
	item_stats = None
	item_type = None
	for key in list(item_listing.keys()):
		for item in list(item_listing[key].keys()):
			if item == name:
				item_args = item_listing[key][item]["args"]
				item_stats = item_listing[key][item]["stats"]
				item_type = key

	if item_type == "primary_weapon":
		return PrimaryWeapon.get_randomized_item(item_stats, item_args, coolity)
	elif item_type == "secondary_weapon":
		return SecondaryWeapon.get_randomized_item(item_stats, item_args, coolity)
	return "Unknown item"

item_listing = { 
	"primary_weapon":{
		"club": {"stats": {"damage" : ["1d3","2d6"], "accuracy" : ["3d6","5d6"]} , "args":{"name":"club", "description":"A rough wooden club, good enough to break a skull!", "abilities_granted":["smash"]}}
	},
	"secondary_weapon":{
		"dagger": {"stats": {"damage" : ["1d3","1d6"], "accuracy" : ["2d6","5d6"]} , "args":{"name":"dagger", "description":"Stabby stab!", "abilities_granted":["stab", "cut", "quick stab", "quick cut"]}},
		"shield": {"stats": {"defence" : ["1d3","5d6"], "evasion" : ["-2d6","-1d3"]} , "args":{"name":"shield", "description":"A shield.", "abilities_granted":["shield up", "bash"]}},
	}

}