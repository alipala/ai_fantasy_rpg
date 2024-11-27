from crewai import Agent
from together import Together
from core.game_state import GameState
from langchain.chat_models.base import BaseChatModel
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class CustomTogetherModel(BaseChatModel):
    client: Any = Field(default=None)
    model_name: str = Field(default="meta-llama/Llama-3-70b-chat-hf")

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, together_client, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, 'client', together_client)

    @property
    def _llm_type(self) -> str:
        return "together"

    def _generate(self, messages: List[Dict[str, Any]], stop: List[str] | None = None) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": m["role"], "content": m["content"]} for m in messages]
        )
        return response.choices[0].message.content

    def _call(self, messages: List[Dict[str, Any]], stop: List[str] | None = None) -> str:
        return self._generate(messages, stop)

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model": self.model_name}

class WorldBuilderAgent:
    def __init__(self, api_key):
        try: 
            self.client = Together(api_key=api_key)
            self.chat_model = CustomTogetherModel(together_client=self.client)
            self.agent = Agent(
                role='World Builder',
                goal='Create rich, consistent fantasy worlds',
                backstory='Expert at creating fantasy worlds with complex hierarchies',
                allow_delegation=False,
                llm=self.chat_model
            )
        except Exception as e:
            print(f"Error initializing agent: {str(e)}")
            raise           

    def generate_world(self, concept):
        system_prompt = """
        Create interesting fantasy worlds that players would love to play in.
        Instructions:
        - Only generate in plain text without formatting
        - Use simple clear language without being flowery
        - Stay below 3-5 sentences for each description
        """
        
        world_prompt = f"""
        Generate a creative description for a unique fantasy world with an
        interesting concept around {concept}.

        Output content in the form:
        World Name: <WORLD NAME>
        World Description: <WORLD DESCRIPTION>

        World Name:"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": world_prompt}
        ]
        
        response = self.client.chat.completions.create(
            model="meta-llama/Llama-3-70b-chat-hf",
            messages=messages
        )
        
        world_output = response.choices[0].message.content.strip()
        
        # Parse the response into a structured format
        world = {
            "name": world_output.split('\n')[0].strip().replace('World Name: ', ''),
            "description": '\n'.join(world_output.split('\n')[1:]).replace('World Description:', '').strip()
        }
        
        return world

    def generate_kingdoms(self, world_data):
        try:
            system_prompt = """
            Generate exactly 3 kingdoms for this fantasy world.
            Each kingdom must be unique with rich culture and history.
            Format must be exactly:
            Kingdom Name: [name]
            Kingdom Description: [description]
            """
            
            kingdom_prompt = f"""
            Create 3 unique kingdoms for {world_data['name']}.
            Each kingdom should have a connection to the Colossi and the world's magic.

            World Context: {world_data['description']}

            Respond with exactly:
            Kingdom Name: [First Kingdom Name]
            Kingdom Description: [First Kingdom Description]

            Kingdom Name: [Second Kingdom Name]
            Kingdom Description: [Second Kingdom Description]

            Kingdom Name: [Third Kingdom Name]
            Kingdom Description: [Third Kingdom Description]
            """

            print("\nGenerating kingdoms...")
            response = self.client.chat.completions.create(
                model="meta-llama/Llama-3-70b-chat-hf",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": kingdom_prompt}
                ],
                temperature=0.7
            )
            
            kingdoms = {}
            raw_output = response.choices[0].message.content
            print(f"\nRaw kingdom response: {raw_output}")  # Debug print
            
            # Split by double newline to separate kingdoms
            kingdom_sections = [k for k in raw_output.split('\n\n') if 'Kingdom Name:' in k]
            
            for section in kingdom_sections:
                lines = section.split('\n')
                for i in range(len(lines)-1):
                    if 'Kingdom Name:' in lines[i]:
                        name = lines[i].split('Kingdom Name:')[1].strip()
                        desc = lines[i+1].split('Kingdom Description:')[1].strip()
                        kingdoms[name] = {
                            "name": name,
                            "description": desc,
                            "world": world_data['name'],
                            "towns": {}  # Initialize empty towns dict
                        }
                        print(f"Created kingdom: {name}")
            
            if not kingdoms:
                print("No kingdoms parsed from response, using backup method...")
                # Backup parsing method
                lines = raw_output.split('\n')
                current_name = None
                for line in lines:
                    if 'Kingdom Name:' in line:
                        current_name = line.split('Kingdom Name:')[1].strip()
                    elif 'Kingdom Description:' in line and current_name:
                        desc = line.split('Kingdom Description:')[1].strip()
                        kingdoms[current_name] = {
                            "name": current_name,
                            "description": desc,
                            "world": world_data['name'],
                            "towns": {}
                        }
                        print(f"Created kingdom (backup): {current_name}")

            if not kingdoms:
                raise ValueError("Failed to generate kingdoms")
                
            return kingdoms
            
        except Exception as e:
            print(f"Error generating kingdoms: {e}")
            # Return a single detailed kingdom instead of failing
            fallback_kingdom = {
                "First Kingdom": {
                    "name": "First Kingdom",
                    "description": f"The primary kingdom of {world_data['name']}, where the largest Colossi roam. The citizens have mastered the art of living atop these massive beasts, creating a unique civilization that moves with their titanic hosts.",
                    "world": world_data['name'],
                    "towns": {}
                }
            }
            return fallback_kingdom

    def generate_towns(self, world_data, kingdom_data):
        try:
            system_prompt = """
            Generate exactly 3 unique towns for a kingdom.
            Each town should have distinctive features and history.
            Format must be exactly:
            Town Name: [name]
            Town Description: [description]
            """
            
            town_prompt = f"""
            Create 3 unique towns for the kingdom of {kingdom_data['name']} in {world_data['name']}.
            Each town should reflect the kingdom's character and its relationship with the Colossi.

            Kingdom Context: {kingdom_data['description']}
            World Context: {world_data['description']}

            Respond with exactly:
            Town Name: [First Town Name]
            Town Description: [First Town Description]

            Town Name: [Second Town Name]
            Town Description: [Second Town Description]

            Town Name: [Third Town Name]
            Town Description: [Third Town Description]
            """

            print(f"\nGenerating towns for {kingdom_data['name']}...")
            response = self.client.chat.completions.create(
                model="meta-llama/Llama-3-70b-chat-hf",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": town_prompt}
                ],
                temperature=0.7
            )
            
            towns = {}
            raw_output = response.choices[0].message.content
            print(f"Raw town response received for {kingdom_data['name']}")
            
            # Split by double newline to separate towns
            town_sections = [t for t in raw_output.split('\n\n') if 'Town Name:' in t]
            
            for section in town_sections:
                try:
                    lines = section.split('\n')
                    name_line = next(line for line in lines if 'Town Name:' in line)
                    desc_line = next(line for line in lines if 'Town Description:' in line)
                    
                    name = name_line.split('Town Name:')[1].strip()
                    desc = desc_line.split('Town Description:')[1].strip()
                    
                    towns[name] = {
                        "name": name,
                        "description": desc,
                        "world": world_data['name'],
                        "kingdom": kingdom_data['name'],
                        "npcs": {}  # Initialize empty NPCs dict
                    }
                    print(f"Created town: {name}")
                except Exception as e:
                    print(f"Error parsing town section: {e}")
                    continue
            
            if not towns:
                print("No towns parsed from response, creating default town...")
                # Create at least one default town
                default_town = {
                    "Central Haven": {
                        "name": "Central Haven",
                        "description": f"The primary settlement of {kingdom_data['name']}, nestled safely on the Colossus's back.",
                        "world": world_data['name'],
                        "kingdom": kingdom_data['name'],
                        "npcs": {}
                    }
                }
                return default_town
                
            return towns
            
        except Exception as e:
            print(f"Error generating towns: {e}")
            # Return a single detailed town instead of failing
            fallback_town = {
                "Central Haven": {
                    "name": "Central Haven",
                    "description": f"The primary settlement of {kingdom_data['name']}, nestled safely on the Colossus's back.",
                    "world": world_data['name'],
                    "kingdom": kingdom_data['name'],
                    "npcs": {}
                }
            }
            return fallback_town

    def generate_npcs(self, world_data, kingdom_data, town_data):
        try:
            system_prompt = """
            Generate exactly 3 unique NPCs for a town.
            Each NPC should have a distinct personality, appearance, and role.
            Format must be exactly:
            Character Name: [name]
            Character Description: [description]
            """
            
            npc_prompt = f"""
            Create 3 unique characters for {town_data['name']} in {kingdom_data['name']}.
            Each character should reflect the town's character and the kingdom's culture.

            Town Context: {town_data['description']}
            Kingdom Context: {kingdom_data['description']}
            World Context: {world_data['description']}

            Respond with exactly:
            Character Name: [First Character Name]
            Character Description: [First Character Description]

            Character Name: [Second Character Name]
            Character Description: [Second Character Description]

            Character Name: [Third Character Name]
            Character Description: [Third Character Description]
            """

            print(f"\nGenerating NPCs for {town_data['name']}...")
            response = self.client.chat.completions.create(
                model="meta-llama/Llama-3-70b-chat-hf",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": npc_prompt}
                ],
                temperature=0.7
            )
            
            npcs = {}
            raw_output = response.choices[0].message.content
            print(f"Raw NPC response received for {town_data['name']}")
            
            # Split by double newline to separate characters
            npc_sections = [n for n in raw_output.split('\n\n') if 'Character Name:' in n]
            
            if not npc_sections:
                # Try alternative splitting method
                npc_sections = raw_output.split('Character Name:')[1:]  # Skip first empty split
            
            for section in npc_sections:
                try:
                    lines = section.split('\n')
                    if 'Character Name:' in section:
                        # Handle case where "Character Name:" is in the section
                        name_line = next(line for line in lines if 'Character Name:' in line)
                        desc_line = next(line for line in lines if 'Character Description:' in line)
                        name = name_line.split('Character Name:')[1].strip()
                        desc = desc_line.split('Character Description:')[1].strip()
                    else:
                        # Handle case where section starts directly with name
                        name = lines[0].strip()
                        desc = ' '.join(lines[1:]).replace('Character Description:', '').strip()
                    
                    if name and desc:
                        npcs[name] = {
                            "name": name,
                            "description": desc,
                            "world": world_data['name'],
                            "kingdom": kingdom_data['name'],
                            "town": town_data['name']
                        }
                        print(f"Created NPC: {name}")
                except Exception as e:
                    print(f"Error parsing NPC section: {e}")
                    continue
            
            if not npcs:
                print("No NPCs parsed from response, creating default NPCs...")
                # Create default NPCs for the town
                npcs = {
                    "Town Elder": {
                        "name": "Town Elder",
                        "description": f"A wise and respected leader of {town_data['name']}, who understands the deep connection between the town and its Colossus.",
                        "world": world_data['name'],
                        "kingdom": kingdom_data['name'],
                        "town": town_data['name']
                    },
                    "Merchant": {
                        "name": "Merchant",
                        "description": f"A charismatic trader who brings goods from across {kingdom_data['name']}, always ready with the latest news and gossip.",
                        "world": world_data['name'],
                        "kingdom": kingdom_data['name'],
                        "town": town_data['name']
                    },
                    "Guard Captain": {
                        "name": "Guard Captain",
                        "description": f"A vigilant protector of {town_data['name']}, skilled in both combat and maintaining order in a city that moves with its Colossus.",
                        "world": world_data['name'],
                        "kingdom": kingdom_data['name'],
                        "town": town_data['name']
                    }
                }
            
            return npcs
            
        except Exception as e:
            print(f"Error generating NPCs: {e}")
            # Return default NPCs instead of failing
            return {
                "Local Guide": {
                    "name": "Local Guide",
                    "description": f"A friendly resident of {town_data['name']} who helps newcomers adjust to life on the Colossus.",
                    "world": world_data['name'],
                    "kingdom": kingdom_data['name'],
                    "town": town_data['name']
                }
            }

    def build_complete_world(self, concept: str) -> Dict:
        """Build a complete world with kingdoms, towns, and NPCs."""
        try:
            print("\nStarting world generation process...")
            
            # Generate world
            world = self.generate_world(concept)
            print(f"\nCreated world: {world['name']}")
            
            # Generate kingdoms
            kingdoms = self.generate_kingdoms(world)
            world['kingdoms'] = kingdoms
            print(f"\nCreated {len(kingdoms)} kingdoms")
            
            # For each kingdom
            for kingdom_name, kingdom in kingdoms.items():
                print(f"\nGenerating content for kingdom: {kingdom_name}")
                
                # Generate towns
                towns = self.generate_towns(world, kingdom)
                kingdom['towns'] = towns
                print(f"Created {len(towns)} towns for {kingdom_name}")
                
                # For each town
                for town_name, town in towns.items():
                    print(f"Generating NPCs for town: {town_name}")
                    npcs = self.generate_npcs(world, kingdom, town)
                    town['npcs'] = npcs
                    print(f"Created {len(npcs)} NPCs for {town_name}")
            
            # Add start message
            first_kingdom = list(kingdoms.values())[0]
            first_town = list(first_kingdom['towns'].values())[0]
            first_npc = list(first_town['npcs'].values())[0]
            
            world['start'] = f"Welcome to {world['name']}! You begin your journey in {first_town['name']}, {first_town['description']} Your guide is {first_npc['name']}, {first_npc['description']}"
            
            print("\nWorld generation complete!")
            return world
            
        except Exception as e:
            print(f"\nError in world generation: {str(e)}")
            # Create a complete fallback world
            fallback_world = {
                "name": "Kyropeia",
                "description": "A realm where massive Colossi roam, carrying entire cities on their backs.",
                "kingdoms": {
                    "Luminaria": {
                        "name": "Luminaria",
                        "description": "A kingdom built upon the largest Colossus, where magic and technology blend.",
                        "world": "Kyropeia",
                        "towns": {
                            "First Town": {
                                "name": "First Town",
                                "description": "A bustling settlement on the Colossus's back.",
                                "world": "Kyropeia",
                                "kingdom": "Luminaria",
                                "npcs": {
                                    "Guide": {
                                        "name": "Guide",
                                        "description": "A knowledgeable local who helps newcomers navigate the city.",
                                        "world": "Kyropeia",
                                        "kingdom": "Luminaria",
                                        "town": "First Town"
                                    }
                                }
                            }
                        }
                    }
                }
            }
            return fallback_world