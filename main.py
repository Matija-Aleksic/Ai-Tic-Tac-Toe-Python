from GUI import TicTacToeGUI
from GameEngine import GameEngine

if __name__ == "__main__":
    engine = GameEngine()
    gui = TicTacToeGUI(engine)
    gui.run()