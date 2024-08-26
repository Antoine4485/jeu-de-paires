import re
import string
from math import sqrt
from os import system, name
from random import choice, shuffle

import colorama
import yaml
from tinydb import Query

from constants import INFOS_TABLE, SOLUTION_GRID_TABLE, PLAYER_GRID_TABLE, CURRENT_DIR
from game import Game


class PairsGame:

    def __init__(self):
        self.__config = self.__get_config()
        self.__game = self.__get_saved_game()
        while True:
            if not self.__play():
                return

    def __play(self) -> bool:
        self.__pair_of_cards = []
        # self.__pair_of_cards_copy : variable utilisée pour l'affichage de la couleur de fond de la paire de cartes.
        # Si on utilisait self.__pair_of_cards à la place, la couleur de fond ne serait pas visible dans le cas où les
        # deux cartes seraient différentes.
        self.__pair_of_cards_copy = []

        # initialisation d'un nouveau jeu
        if not self.__game:
            self.__game = self.__get_new_game(self.__ask_level())
        elif not self.__ask_continue_saved_game():
            self.__delete_game()
            self.__game = self.__get_new_game(self.__ask_level())

        # jeu
        while self.__game.nb_values_to_find > 0:
            _try = self.__try()
            if _try == "Q":
                self.__game.save()
                return False
            if _try == "N":
                self.__delete_game()
                return True

        text = "Partie gagnée !"
        if self.__game.nb_tries < self.__game.best_score:
            text = "Record battu !"
        play_again = self.__ask_play_again(text)

        if self.__game.best_score == 0 or self.__game.nb_tries < self.__game.best_score:
            self.__game.update_best_score()

        self.__delete_game()
        return play_again

    def __try(self) -> str | bool:
        self.__pair_of_cards = []

        for i in range(2):
            choice = self.__ask_card_choice()
            if choice in ("Q", "N"):
                return choice
            self.__pair_of_cards.append(choice)
            self.__pair_of_cards_copy = self.__pair_of_cards.copy()

        # cas où les cartes sont identiques
        if self.__game.solution_grid[self.__pair_of_cards[0][0]][self.__pair_of_cards[0][1]] == \
                self.__game.solution_grid[self.__pair_of_cards[1][0]][self.__pair_of_cards[1][1]]:
            # on ajoute ces cartes à la grille du joueur
            for card in self.__pair_of_cards:
                self.__game.player_grid[card[0]][card[1]] = self.__game.solution_grid[card[0]][card[1]]
            self.__pair_of_cards_copy = []
            self.__game.nb_values_to_find -= 2

        self.__game.nb_tries += 1
        return True

    def __delete_game(self):
        self.__game.delete()
        self.__game = None

    def __ask_continue_saved_game(self) -> bool:
        while True:
            rep = self.__input("Reprendre la partie ? O/N : ").upper()
            if rep in ("O", "N"):
                return False if rep == "N" else True

    def __ask_play_again(self, text) -> bool:
        while True:
            rep = self.__input(f"{text}\n\nNouvelle partie ? O/N : ").upper()
            if rep in ("O", "N"):
                return False if rep == "N" else True

    def __ask_card_choice(self) -> str | tuple[int, str]:
        while True:
            try:
                choice = self.__input("Votre choix : ").upper()
                if choice in ("Q", "N"):
                    return choice
                digit = int("".join(re.findall(r"\d", choice))) - 1
                letter = "".join(re.findall(r"\D", choice))
                if digit not in range(len(self.__game.letters)) or letter not in self.__game.letters:
                    continue
                choice = (digit, letter)
                if self.__game.player_grid[digit][letter] == self.__config["verso"] and choice not in self.__pair_of_cards:
                    return choice
            except ValueError:
                continue

    def __ask_level(self) -> int:
        while True:
            try:
                text = f"""
Ce jeu est un jeu de mémoire où il faut trouver des paires de cartes identiques.

Le principe est le suivant :

A chaque tour vous devez entrer les coordonnées, par exemple A1 ou C7 (en majuscules ou en minuscules, avec la lettre 
avant ou après le chiffre) + Entrée pour révéler une carte, puis en entrer une autre afin de trouver la bonne paire. 
Si les cartes sont identiques elles restent visibles sinon elles se retournent. Le jeu est terminé quand toutes les 
cartes sont retournées.

Une fois la partie commencée, vous pourrez à tout moment la quitter et la sauvegarder en tapant Q + Entrée au lieu de
saisir une coordonnée, ou en commencer une nouvelle en tapant N + Entrée.

Pour augmenter la taille du texte, vous pouvez faire Ctrl + zoom (touche "+" sur le clavier ou molette de la souris).

-------------------------------------------------------------------

Choisissez un niveau de difficulté entre 1 (très facile) et {len(self.__config["niveau"])} (très difficile) : """
                level = int(self.__input(text))
                if level in range(1, len(self.__config["niveau"]) + 1):
                    return level
            except ValueError:
                continue

    def __show_player_grid(self):
        values_cell_width = 2
        other_cell_width = values_cell_width + 1

        draw = f"{"":{other_cell_width}}"
        for column_name in self.__game.letters:
            draw += f"{" " + column_name:^{other_cell_width}}"
        draw += "\n\n"
        for i, line in enumerate(self.__game.player_grid):
            draw += f"{str(i + 1) + " ":>{other_cell_width}}"
            for letter, value in line.items():
                if (i, letter) in self.__pair_of_cards_copy:
                    value = (colorama.Back.LIGHTBLACK_EX + self.__game.solution_grid[i][letter] + " "
                             + colorama.Style.RESET_ALL)
                draw += f"{value:^{values_cell_width}}"
            draw += "\n\n"

        print(draw)

    def __show_screen(self):
        self.__clear_screen()
        print("JEU DE PAIRES\n")
        if not self.__game:
            return
        infos_game = [f"Niveau {self.__game.level}"]
        if self.__game.best_score:
            infos_game.append(f"Meilleur score : {self.__game.best_score}")
        if self.__game.nb_tries:
            infos_game.append(f"Nombre de coups joués : {self.__game.nb_tries}")
        print(f"{" | " .join(infos_game)}\n")
        self.__show_player_grid()

    def __input(self, text) -> str:
        self.__show_screen()
        return input(text)

    def __get_new_game(self, level: int) -> Game:

        def get_grid(values):
            length = int(sqrt(len(values)))
            letters = list(string.ascii_uppercase[:length])
            values = [values[i:i + length] for i in range(0, len(values), length)]
            return [dict(zip(letters, line)) for line in values]

        solution_values = []
        nb_values = self.__config["niveau"][level - 1] ** 2
        while len(solution_values) < nb_values / 2:
            value = choice(self.__config["recto"])
            if value not in solution_values:
                solution_values.append(value)
        solution_values *= 2
        shuffle(solution_values)
        player_values = [self.__config["verso"] for _ in solution_values]

        return Game(solution_grid=get_grid(solution_values),
                    player_grid=get_grid(player_values),
                    level=level,
                    best_score=self.__get_saved_best_score(level))

    @staticmethod
    def __get_saved_game() -> bool | Game:
        infos = INFOS_TABLE.get(Query().nb_tries > 0)
        if not infos:
            return False

        return Game(solution_grid=SOLUTION_GRID_TABLE.all(),
                    player_grid=PLAYER_GRID_TABLE.all(),
                    level=infos["level"],
                    nb_tries=infos["nb_tries"],
                    best_score=infos["best_score"])

    @staticmethod
    def __get_saved_best_score(level: int):
        infos = INFOS_TABLE.get(Query().level == level)
        return infos["best_score"] if infos else 0

    @staticmethod
    def __get_config() -> dict:
        with open(CURRENT_DIR / "config.yml", 'r', encoding='utf8') as file:
            try:
                # Chargement du fichiers
                return yaml.safe_load(file)
            except yaml.YAMLError as ex:
                print("YAML FILE HAS SYNTAX ERROR :")
                print(ex)

    @staticmethod
    def __clear_screen():
        system('cls') if name == 'nt' else system('clear')


if __name__ == '__main__':
    PairsGame()