from tinydb import Query

from constants import INFOS_TABLE, SOLUTION_GRID_TABLE, PLAYER_GRID_TABLE


class Game:

    def __init__(self, solution_grid: list[dict], player_grid: list[dict],
                 level: int, nb_tries: int = 0, best_score: int = 0):
        self.solution_grid = solution_grid
        self.player_grid = player_grid
        self.level = level
        self.nb_tries = nb_tries
        self.best_score = best_score
        self.letters = list(solution_grid[0].keys())
        self.nb_values_to_find = self.__get_nb_values_to_find()

    def __get_nb_values_to_find(self) -> int:
        nb_values_to_find = 0
        for i, row in enumerate(self.solution_grid):
            for column in row:
                if self.player_grid[i][column] != self.solution_grid[i][column]:
                    nb_values_to_find += 1
        return nb_values_to_find

    def __upsert_infos(self):
        INFOS_TABLE.upsert({"level": self.level,
                            "nb_tries": self.nb_tries,
                            "best_score": self.best_score},
                           Query().level == self.level)

    def save(self):
        self.__delete_grids()
        SOLUTION_GRID_TABLE.insert_multiple(self.solution_grid)
        PLAYER_GRID_TABLE.insert_multiple(self.player_grid)
        self.__upsert_infos()

    def delete(self):
        self.__delete_grids()
        self.nb_tries = 0
        self.__upsert_infos()

    def update_best_score(self):
        self.best_score = self.nb_tries
        self.__upsert_infos()

    @staticmethod
    def __delete_grids():
        SOLUTION_GRID_TABLE.truncate()
        PLAYER_GRID_TABLE.truncate()