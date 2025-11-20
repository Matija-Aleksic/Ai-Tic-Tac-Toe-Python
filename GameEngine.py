class GameEngine:

    def __init__(self):
        self.current_player = "X"
        self.board = [["" for _ in range(3)] for _ in range(3)]

    def reset_board(self):
        self.current_player = "X"
        self.board = [["" for _ in range(3)] for _ in range(3)]

    def play_move(self, row: int, col: int):
        if self.board[row][col] != "":
            return {"valid": False, "winner": None, "draw": False}

        self.board[row][col] = self.current_player

        winner = self.check_winner()
        draw = self.is_draw() if winner is None else False

        if winner is None and not draw:
            self.current_player = "O" if self.current_player == "X" else "X"

        return {
            "valid": True,
            "winner": winner,
            "draw": draw
        }

    def check_winner(self):
        b = self.board

        for r in range(3):
            if b[r][0] != "" and b[r][0] == b[r][1] == b[r][2]:
                return b[r][0]

        for c in range(3):
            if b[0][c] != "" and b[0][c] == b[1][c] == b[2][c]:
                return b[0][c]

        if b[0][0] != "" and b[0][0] == b[1][1] == b[2][2]:
            return b[0][0]
        if b[0][2] != "" and b[0][2] == b[1][1] == b[2][0]:
            return b[0][2]

        return None

    def is_draw(self):
        for row in self.board:
            for cell in row:
                if cell == "":
                    return False
        return self.check_winner() is None
