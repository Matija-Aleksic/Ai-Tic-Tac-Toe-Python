import tkinter as tk
from tkinter import messagebox
import GameEngine


class TicTacToeGUI:
    def __init__(self, engine: GameEngine):
        self.engine = engine
        self.root = tk.Tk()
        self.root.title("Tic-Tac-Toe")

        self.buttons = [[None for _ in range(3)] for _ in range(3)]

        self.status_label = tk.Label(
            self.root,
            text=f"Igrač na potezu: {self.engine.current_player}",
            font=("Arial", 14)
        )
        self.status_label.grid(row=0, column=0, columnspan=3, pady=(10, 10))

        self._create_board()

        reset_btn = tk.Button(
            self.root,
            text="Reset",
            font=("Arial", 12),
            command=self.reset_game
        )
        reset_btn.grid(row=4, column=0, columnspan=3, pady=(10, 10))

    def _create_board(self):
        for r in range(3):
            for c in range(3):
                btn = tk.Button(
                    self.root,
                    text="",
                    width=6,
                    height=3,
                    font=("Arial", 20),
                    command=lambda row=r, col=c: self.on_cell_click(row, col)
                )
                btn.grid(row=r + 1, column=c, padx=5, pady=5)
                self.buttons[r][c] = btn

    def on_cell_click(self, row: int, col: int):
        result = self.engine.play_move(row, col)

        if not result["valid"]:
            return

        self.update_board_view()

        if result["winner"]:
            messagebox.showinfo("Kraj igre", f"Pobijedio je: {result['winner']}")
            self.disable_board()
        elif result["draw"]:
            messagebox.showinfo("Kraj igre", "Neriješeno!")
            self.disable_board()
        else:
            self.status_label.config(
                text=f"Igrač na potezu: {self.engine.current_player}"
            )

    def update_board_view(self):
        for r in range(3):
            for c in range(3):
                value = self.engine.board[r][c]
                self.buttons[r][c].config(text=value)

    def disable_board(self):
        for row in self.buttons:
            for btn in row:
                btn.config(state=tk.DISABLED)

    def enable_board(self):
        for row in self.buttons:
            for btn in row:
                btn.config(state=tk.NORMAL)

    def reset_game(self):
        self.engine.reset_board()
        self.enable_board()
        self.update_board_view()
        self.status_label.config(
            text=f"Igrač na potezu: {self.engine.current_player}"
        )

    def run(self):
        self.root.mainloop()