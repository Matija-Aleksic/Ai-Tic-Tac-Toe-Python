import json
import socket
import threading
import tkinter as tk
from tkinter import messagebox

from GameEngine import GameEngine

HOST = "127.0.0.1"
PORT = 5000



def send_json(conn, data: dict):
    text = json.dumps(data) + "\n"
    conn.sendall(text.encode("utf-8"))


def recv_line(conn):
    buffer = b""
    while True:
        chunk = conn.recv(1)
        if not chunk:
            return None
        if chunk == b"\n":
            break
        buffer += chunk
    return buffer.decode("utf-8")


def try_connect_once(host, port, timeout=0.5):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.settimeout(None)
        return s
    except OSError:
        s.close()
        return None


def run_server(host=HOST, port=PORT):
    engine = GameEngine()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen(2)
        print(f"[SERVER] Čekam igrače na {host}:{port}...")

        conn_x, addr_x = s.accept()
        print(f"[SERVER] Spojio se X: {addr_x}")
        send_json(conn_x, {"type": "role", "mark": "X"})

        conn_o, addr_o = s.accept()
        print(f"[SERVER] Spojio se O: {addr_o}")
        send_json(conn_o, {"type": "role", "mark": "O"})

        players = {"X": conn_x, "O": conn_o}

        def broadcast_state(extra=None):
            state = {
                "type": "state",
                "board": engine.board,
                "current_player": engine.current_player,
            }
            if extra:
                state.update(extra)
            send_json(conn_x, state)
            send_json(conn_o, state)

        broadcast_state()

        while True:
            current = engine.current_player
            conn = players[current]

            send_json(conn, {"type": "your_turn"})

            line = recv_line(conn)
            if line is None:
                print("[SERVER] Igrač se odspojio. Kraj servera.")
                break

            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                print("[SERVER] Neispravan JSON.")
                continue

            if msg.get("type") != "move":
                print("[SERVER] Očekivan 'move'.")
                continue

            row = msg.get("row")
            col = msg.get("col")
            if row is None or col is None:
                continue

            result = engine.play_move(int(row), int(col))

            if not result["valid"]:
                send_json(conn, {"type": "error", "message": "Polje je već zauzeto."})
                continue

            extra = {"winner": result["winner"], "draw": result["draw"]}
            broadcast_state(extra)

            if result["winner"] or result["draw"]:
                print("[SERVER] Igra gotova, gasim server.")
                break

        conn_x.close()
        conn_o.close()
        print("[SERVER] Server završio.")


class TicTacToeNetworkGUI:
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.listener_thread = None

        self.root = tk.Tk()
        self.root.title("Tic-Tac-Toe LAN")

        self.board = [["" for _ in range(3)] for _ in range(3)]
        self.buttons = [[None for _ in range(3)] for _ in range(3)]

        self.my_mark = None
        self.current_player = None
        self.is_my_turn = False

        self.status_label = tk.Label(
            self.root, text="Spajanje...", font=("Arial", 14)
        )
        self.status_label.grid(row=0, column=0, columnspan=3, pady=(10, 10))

        self._create_board()

        self.exit_btn = tk.Button(
            self.root,
            text="Izađi",
            font=("Arial", 12),
            command=self.on_close
        )
        self.exit_btn.grid(row=4, column=0, columnspan=3, pady=(10, 10))

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.disable_board()

        self.listener_thread = threading.Thread(target=self.listen_loop, daemon=True)
        self.listener_thread.start()

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

    def listen_loop(self):
        try:
            while True:
                line = recv_line(self.sock)
                if line is None:
                    self.root.after(0, self.handle_server_disconnect)
                    break

                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue

                self.root.after(0, self.handle_message, msg)
        except OSError:
            pass

    def handle_server_disconnect(self):
        messagebox.showinfo("Veza prekinuta", "Veza sa serverom je prekinuta.")
        self.disable_board()
        self.status_label.config(text="Veza prekinuta.")

    def handle_message(self, msg: dict):
        mtype = msg.get("type")

        if mtype == "role":
            self.my_mark = msg.get("mark")
            self.root.title(f"Tic-Tac-Toe LAN – Igrač {self.my_mark}")
            self.status_label.config(
                text=f"Ti si igrač {self.my_mark}. Čekam početak igre..."
            )

        elif mtype == "state":
            self.board = msg.get("board", self.board)
            self.current_player = msg.get("current_player", self.current_player)
            winner = msg.get("winner")
            draw = msg.get("draw")

            self.update_board_view()

            if winner:
                self.status_label.config(text=f"Pobijedio je {winner}")
                messagebox.showinfo("Kraj igre", f"Pobijedio je {winner}")
                self.disable_board()
            elif draw:
                self.status_label.config(text="Neriješeno")
                messagebox.showinfo("Kraj igre", "Neriješeno!")
                self.disable_board()
            else:
                self.status_label.config(
                    text=f"Igrač na potezu: {self.current_player}"
                )

        elif mtype == "your_turn":
            if self.current_player == self.my_mark:
                self.is_my_turn = True
                self.enable_board()
                self.status_label.config(
                    text=f"Tvoj potez ({self.my_mark})"
                )
            else:
                self.is_my_turn = False
                self.disable_board()

        elif mtype == "error":
            err_msg = msg.get("message", "Nepoznata greška.")
            messagebox.showwarning("Greška", err_msg)

    def update_board_view(self):
        for r in range(3):
            for c in range(3):
                value = self.board[r][c]
                self.buttons[r][c].config(text=value)

    def disable_board(self):
        for row in self.buttons:
            for btn in row:
                btn.config(state=tk.DISABLED)

    def enable_board(self):
        for row in self.buttons:
            for btn in row:
                btn.config(state=tk.NORMAL)

    def on_cell_click(self, row: int, col: int):
        if not self.is_my_turn:
            return

        if self.board[row][col] != "":
            return

        move_msg = {"type": "move", "row": row, "col": col}
        try:
            text = json.dumps(move_msg) + "\n"
            self.sock.sendall(text.encode("utf-8"))
        except OSError:
            messagebox.showerror("Greška", "Veza sa serverom je prekinuta.")
            self.disable_board()
            return

        self.is_my_turn = False
        self.disable_board()

    def on_close(self):
        try:
            if self.sock:
                self.sock.close()
        except OSError:
            pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    sock = try_connect_once(HOST, PORT)
    if sock:
        print("[APP] Pronađen server, spajam se kao klijent.")
        app = TicTacToeNetworkGUI(sock)
        app.run()
        return

    print("[APP] Nema servera, pokrećem server u pozadini...")
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    sock = None
    while sock is None:
        sock = try_connect_once(HOST, PORT)

    print("[APP] Spojen na vlastiti server kao prvi klijent.")
    app = TicTacToeNetworkGUI(sock)
    app.run()


if __name__ == "__main__":
    main()
