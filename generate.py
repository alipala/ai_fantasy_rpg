# generate.py
import json

def generate_npc_inventories(worlds_file, inventory_file):
    # Load worlds data
    with open(worlds_file, 'r') as f:
        data = json.load(f)
        worlds_data = data.get('worlds', {})
        
    # Load existing inventories
    with open(inventory_file, 'r') as f:
        existing_inventories = json.load(f)

    # Create base inventory templates based on roles
    inventory_templates = {
        "Builder": [
            "10 gold",
            "Craftsman's hammer",
            "Set of precision tools",
            "Blueprint journal",
            "Enchanted measuring tape"
        ],
        "Whisperer": [
            "10 gold",
            "Mystic communication crystal",
            "Essence collector",
            "Book of whispered secrets",
            "Spirit-touched amulet"
        ],
        "Brave": [
            "10 gold",
            "Enchanted shield",
            "Warrior's medallion",
            "Healing poultice",
            "Courage charm"
        ],
        "Wise": [
            "10 gold",
            "Ancient tome",
            "Wisdom crystal",
            "Scroll case",
            "Memory stones"
        ],
        "Wanderer": [
            "10 gold",
            "Traveler's compass",
            "Weather-worn map",
            "Survival kit",
            "Lucky charm"
        ]
    }

    new_inventories = {"inventories": {}}

    # Iterate through all worlds and NPCs
    for world_name, world in worlds_data.items():
        kingdoms = world.get('kingdoms', {})
        for kingdom_name, kingdom in kingdoms.items():
            towns = kingdom.get('towns', {})
            for town_name, town in towns.items():
                npcs = town.get('npcs', {})
                for npc_name, npc in npcs.items():
                    if npc_name in existing_inventories['inventories']:
                        # Keep existing inventory
                        new_inventories['inventories'][npc_name] = existing_inventories['inventories'][npc_name]
                    else:
                        # Generate new inventory based on NPC's role
                        role = npc_name.split()[-1]  # Get the role from name (e.g., "the Builder")
                        base_items = inventory_templates.get(role, inventory_templates["Wanderer"]).copy()
                        
                        # Add location-specific items based on world
                        location_items = []
                        if "Ignisia" in world_name:
                            location_items = ["Fire-resistant cloak", "Magma compass"]
                        elif "Aquaria" in world_name:
                            location_items = ["Water breathing charm", "Pearl compass"]
                        elif "Mechanica" in world_name:
                            location_items = ["Clockwork assistant", "Steam-powered toolkit"]
                        elif "Terranova" in world_name:
                            location_items = ["Nature's blessing stone", "Living compass"]
                        elif "Etheria" in world_name:
                            location_items = ["Ethereal crystal", "Void compass"]
                        
                        # Combine base items with location items
                        inventory = base_items
                        if location_items:
                            inventory.extend(location_items)
                        new_inventories['inventories'][npc_name] = inventory[:5]  # Keep max 5 items

    # Save the new inventory file
    output_file = 'shared_data/inventory.json'
    with open(output_file, 'w') as f:
        json.dump(new_inventories, f, indent=2)
    print(f"Generated new inventory file: {output_file}")

    return new_inventories

if __name__ == "__main__":
    worlds_file = 'shared_data/game_world.json'
    inventory_file = 'shared_data/inventory.txt'
    new_inventories = generate_npc_inventories(worlds_file, inventory_file)