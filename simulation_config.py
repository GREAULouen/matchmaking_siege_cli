import os
import json
import jsonschema
from jsonschema import validate


def load_simulation_parameters(path='simulation_config.json'):
    """loads simulations parameters from a given json file"""

    assert path.endswith('.json'), 'expecting a .json file'

    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found")

    with open(path, 'r') as file:
        config = json.load(file)

    print(f"Loaded from JSON file {path}:")
    print(f"{config}")

    schema = {
        "type": "object",
        "properties": {
            "game_min_duration": {"type": "number"},                   # Minimum game duration (seconds)
            "game_max_duration": {"type": "number"},                   # Maximum game duration (seconds)
            "min_wait_before_requeue": {"type": "number"},             # Minimum wait after finishing a game
            "max_wait_before_requeue": {"type": "number"},             # Maximum wait after finishing a game
            "duel_win_bonus": {"type": "number"},                      # Elo bonus for winning a duel
            "duel_loss_penalty": {"type": "number"},                   # Elo penalty for losing a duel
            "group_min": {"type": "number"},                           # Minimum players needed for a group match
            "group_max": {"type": "number"},                           # Maximum players in a group match
            "group_win_bonus": {"type": "number"},                     # Elo bonus for winning a group game
            "group_loss_penalty": {"type": "number"},                  # Elo penalty for losing a group game
        },
        "required": [
            "game_min_duration",
            "game_max_duration",
            "min_wait_before_requeue",
            "max_wait_before_requeue",
            "duel_win_bonus",
            "duel_loss_penalty",
            "group_min",
            "group_max",
            "group_win_bonus",
            "group_loss_penalty"
        ],
        "additionalProperties": False
    }

    validate(config, schema)

    return config