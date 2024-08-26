from pathlib import Path

from tinydb import TinyDB

CURRENT_DIR = Path(__file__).parent
DB = TinyDB(CURRENT_DIR / "pairs-game.json", indent=4)
SOLUTION_GRID_TABLE = DB.table("solution_grid")
PLAYER_GRID_TABLE = DB.table("player_grid")
INFOS_TABLE = DB.table("infos")