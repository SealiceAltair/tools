"""ほしみのダイスロール - 小型Windowsデスクトップアプリ。"""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from dice_logic import parse_command, roll_cc


APP_NAME = "ほしみのダイスロール"
VERSION = "1.1.1"
COLORS = {
    "bg": "#202124",
    "panel": "#292a2d",
    "field": "#34363a",
    "border": "#46484d",
    "text": "#f1f3f4",
    "muted": "#9aa0a6",
    "accent": "#4da3ff",
    "success": "#48a9ff",
    "failure": "#ff7770",
    "button": "#3c4043",
    "button_active": "#4b5054",
}


def data_file_path() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    return base / "HoshimiDiceRoll" / "state.json"


class HoshimiDiceApp:
    COLLAPSED_HEIGHT = 315
    EXPANDED_HEIGHT = 570

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.state_path = data_file_path()
        self.names: list[str] = []
        self.history: list[dict[str, str]] = []
        self.history_open = False
        self.current_copy_text = ""
        self.placeholder_active = False

        self._load_state()
        self._configure_window()
        self._configure_styles()
        self._build_ui()
        self._refresh_names()
        self._refresh_history()
        self._set_placeholder()

    def _configure_window(self) -> None:
        self.root.title(APP_NAME)
        self.root.geometry(f"500x{self.COLLAPSED_HEIGHT}")
        self.root.minsize(460, 300)
        self.root.resizable(True, False)
        self.root.configure(bg=COLORS["bg"])
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Dark.TCombobox",
            fieldbackground=COLORS["field"],
            background=COLORS["field"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["text"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            padding=4,
        )
        style.map(
            "Dark.TCombobox",
            fieldbackground=[("readonly", COLORS["field"])],
            foreground=[("readonly", COLORS["text"])],
            selectbackground=[("readonly", COLORS["field"])],
            selectforeground=[("readonly", COLORS["text"])],
        )

    def _button(self, parent: tk.Widget, text: str, command, **kwargs) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=kwargs.pop("bg", COLORS["button"]),
            fg=kwargs.pop("fg", COLORS["text"]),
            activebackground=COLORS["button_active"],
            activeforeground=COLORS["text"],
            relief="flat",
            bd=0,
            padx=kwargs.pop("padx", 9),
            pady=kwargs.pop("pady", 5),
            cursor="hand2",
            **kwargs,
        )

    def _build_ui(self) -> None:
        outer = tk.Frame(self.root, bg=COLORS["bg"], padx=10, pady=8)
        outer.pack(fill="both", expand=True)

        top = tk.Frame(outer, bg=COLORS["bg"])
        top.pack(fill="x")

        self.name_var = tk.StringVar()
        self.name_combo = ttk.Combobox(
            top,
            textvariable=self.name_var,
            state="readonly",
            style="Dark.TCombobox",
            width=23,
        )
        self.name_combo.pack(side="left", fill="x", expand=True)
        self._button(top, "名前…", self._open_names, padx=8).pack(side="left", padx=(6, 0))

        self.bonus_labels = {
            "通常": 0,
            "ボーナス1": 1,
            "ボーナス2": 2,
            "ペナルティ1": -1,
            "ペナルティ2": -2,
        }
        self.bonus_var = tk.StringVar(value="通常")
        self.bonus_combo = ttk.Combobox(
            top,
            textvariable=self.bonus_var,
            values=list(self.bonus_labels),
            state="readonly",
            style="Dark.TCombobox",
            width=12,
        )
        self.bonus_combo.pack(side="left", padx=(6, 0))

        tk.Label(
            outer,
            text="Codexの最終行を貼り付け",
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            anchor="w",
            font=("Yu Gothic UI", 9),
        ).pack(fill="x", pady=(7, 2))

        input_row = tk.Frame(outer, bg=COLORS["bg"])
        input_row.pack(fill="x")
        self.command_text = tk.Text(
            input_row,
            height=2,
            wrap="word",
            undo=True,
            bg=COLORS["field"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            selectbackground="#456a91",
            relief="flat",
            bd=0,
            padx=7,
            pady=5,
            font=("Yu Gothic UI", 10),
        )
        self.command_text.bind("<FocusIn>", self._clear_placeholder)
        self.command_text.bind("<FocusOut>", self._restore_placeholder)
        self.command_text.bind("<Control-v>", self._replace_with_clipboard)
        self.command_text.bind("<Control-V>", self._replace_with_clipboard)
        self.command_text.bind("<Control-Return>", lambda _event: self._roll())
        roll_button = self._button(
            input_row,
            "振る",
            self._roll,
            bg="#1667a8",
            padx=15,
            pady=12,
            font=("Yu Gothic UI", 10, "bold"),
        )
        roll_button.pack(side="right", fill="y", padx=(6, 0))
        self.command_text.pack(side="left", fill="x", expand=True)

        result_frame = tk.Frame(
            outer,
            bg=COLORS["panel"],
            highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        result_frame.pack(fill="both", expand=True, pady=(7, 6))
        self.result_text = tk.Text(
            result_frame,
            height=6,
            wrap="word",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            relief="flat",
            bd=0,
            padx=9,
            pady=7,
            font=("Yu Gothic UI", 9),
            cursor="arrow",
        )
        self.result_text.pack(fill="both", expand=True)
        self.result_text.tag_configure("name", foreground=COLORS["muted"], font=("Yu Gothic UI", 9, "bold"))
        self.result_text.tag_configure("command", foreground=COLORS["text"], font=("Yu Gothic UI", 9, "bold"))
        self.result_text.tag_configure("success", foreground=COLORS["success"], font=("Yu Gothic UI", 9, "bold"))
        self.result_text.tag_configure("failure", foreground=COLORS["failure"], font=("Yu Gothic UI", 9, "bold"))
        self.result_text.insert("1.0", "D100の結果をここに表示します。", "name")
        self.result_text.configure(state="disabled")

        action_row = tk.Frame(outer, bg=COLORS["bg"])
        action_row.pack(fill="x")
        self.copy_button = self._button(action_row, "結果をコピー", self._copy_result, state="disabled")
        self.copy_button.pack(side="left")
        self.history_button = self._button(action_row, "履歴を開く ▾", self._toggle_history)
        self.history_button.pack(side="right")

        self.status_var = tk.StringVar(value="Ctrl＋Enterでも振れます")
        tk.Label(
            action_row,
            textvariable=self.status_var,
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            anchor="w",
            font=("Yu Gothic UI", 8),
        ).pack(side="left", padx=8)

        self.history_frame = tk.Frame(outer, bg=COLORS["bg"])
        history_toolbar = tk.Frame(self.history_frame, bg=COLORS["bg"])
        history_toolbar.pack(fill="x", pady=(7, 3))
        tk.Label(
            history_toolbar,
            text="履歴（新しい順）",
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            font=("Yu Gothic UI", 9),
        ).pack(side="left")
        self._button(history_toolbar, "履歴を消す", self._clear_history, padx=7, pady=3).pack(side="right")

        history_box = tk.Frame(self.history_frame, bg=COLORS["panel"])
        history_box.pack(fill="both", expand=True)
        scroll = tk.Scrollbar(history_box)
        scroll.pack(side="right", fill="y")
        self.history_text = tk.Text(
            history_box,
            wrap="word",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            relief="flat",
            bd=0,
            padx=8,
            pady=6,
            font=("Yu Gothic UI", 8),
            yscrollcommand=scroll.set,
            cursor="arrow",
        )
        self.history_text.pack(fill="both", expand=True)
        scroll.configure(command=self.history_text.yview)
        self.history_text.configure(state="disabled")

    def _set_placeholder(self) -> None:
        if self.command_text.get("1.0", "end-1c").strip():
            return
        self.placeholder_active = True
        self.command_text.configure(fg=COLORS["muted"])
        self.command_text.insert("1.0", "CC<=45 【判定名・行動内容】")

    def _clear_placeholder(self, _event=None) -> None:
        if self.placeholder_active:
            self.command_text.delete("1.0", "end")
            self.command_text.configure(fg=COLORS["text"])
            self.placeholder_active = False

    def _restore_placeholder(self, _event=None) -> None:
        if not self.command_text.get("1.0", "end-1c").strip():
            self._set_placeholder()

    def _replace_with_clipboard(self, _event=None) -> str:
        """コマンド貼り付けは追記せず、入力欄全体を置き換える。"""
        try:
            pasted = self.root.clipboard_get()
        except tk.TclError:
            return "break"
        self._clear_placeholder()
        self.command_text.delete("1.0", "end")
        self.command_text.insert("1.0", pasted)
        return "break"

    def _load_state(self) -> None:
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            self.names = [str(name) for name in data.get("names", []) if str(name).strip()]
            self.history = [item for item in data.get("history", []) if isinstance(item, dict)][-500:]
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self.names = ["マイン・A・レッドフォックス"]
            self.history = []

    def _save_state(self) -> None:
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self.state_path.with_suffix(".tmp")
            payload = {"version": 1, "names": self.names, "history": self.history[-500:]}
            temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            temp_path.replace(self.state_path)
        except OSError as exc:
            self.status_var.set(f"保存できませんでした: {exc}")

    def _refresh_names(self, select: str | None = None) -> None:
        values = self.names if self.names else ["名前を登録してください"]
        self.name_combo.configure(values=values)
        if select in self.names:
            self.name_var.set(select)
        elif self.name_var.get() not in self.names:
            self.name_var.set(values[0])

    def _open_names(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("振る人の登録")
        dialog.geometry("350x285")
        dialog.minsize(320, 250)
        dialog.configure(bg=COLORS["bg"])
        dialog.transient(self.root)
        dialog.grab_set()

        frame = tk.Frame(dialog, bg=COLORS["bg"], padx=10, pady=10)
        frame.pack(fill="both", expand=True)
        name_list = tk.Listbox(
            frame,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            selectbackground="#456a91",
            relief="flat",
            bd=0,
            font=("Yu Gothic UI", 10),
        )
        name_list.pack(fill="both", expand=True)
        for name in self.names:
            name_list.insert("end", name)

        entry = tk.Entry(
            frame,
            bg=COLORS["field"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            bd=0,
            font=("Yu Gothic UI", 10),
        )
        entry.pack(fill="x", pady=(7, 5), ipady=5)

        buttons = tk.Frame(frame, bg=COLORS["bg"])
        buttons.pack(fill="x")

        def add_name() -> None:
            name = entry.get().strip()
            if not name:
                return
            if name not in self.names:
                self.names.append(name)
                name_list.insert("end", name)
                self._refresh_names(select=name)
                self._save_state()
            entry.delete(0, "end")

        def delete_name() -> None:
            selection = name_list.curselection()
            if not selection:
                return
            index = selection[0]
            name = name_list.get(index)
            if not messagebox.askyesno("確認", f"『{name}』を一覧から削除しますか？", parent=dialog):
                return
            self.names.remove(name)
            name_list.delete(index)
            self._refresh_names()
            self._save_state()

        self._button(buttons, "追加", add_name, bg="#1667a8").pack(side="left")
        self._button(buttons, "削除", delete_name).pack(side="left", padx=5)
        self._button(buttons, "閉じる", dialog.destroy).pack(side="right")
        entry.bind("<Return>", lambda _event: add_name())
        entry.focus_set()

    def _roll(self) -> None:
        if not self.names:
            messagebox.showinfo("名前の登録", "先に『名前…』から振る人を登録してください。")
            return

        raw = "" if self.placeholder_active else self.command_text.get("1.0", "end-1c")
        try:
            parsed = parse_command(raw)
            bonus = parsed.command_bonus
            if bonus is None:
                bonus = self.bonus_labels[self.bonus_var.get()]
            else:
                matching_label = next(label for label, value in self.bonus_labels.items() if value == bonus)
                self.bonus_var.set(matching_label)
            result = roll_cc(parsed.success_value, parsed.label, bonus)
        except (ValueError, KeyError) as exc:
            messagebox.showerror("入力を確認してください", str(exc))
            self.status_var.set("入力形式を確認してください")
            return

        roller = self.name_var.get()
        now = datetime.now()
        date_text = now.strftime("%Y/%m/%d")
        copy_text = f"{roller} - {date_text}\n\n{result.command}\n{result.result_line}"
        record = {
            "time": now.isoformat(timespec="seconds"),
            "date": date_text,
            "roller": roller,
            "command": result.command,
            "result": result.result_line,
            "level": result.level,
            "copy": copy_text,
        }
        self.history.append(record)
        self.history = self.history[-500:]
        self.current_copy_text = copy_text
        self._save_state()
        self._show_result(record)
        self._refresh_history()
        self.copy_button.configure(state="normal")
        self.status_var.set("結果を保存しました")
        self.command_text.focus_set()
        self.command_text.tag_add("sel", "1.0", "end-1c")

    def _show_result(self, record: dict[str, str]) -> None:
        level = record["level"]
        level_tag = "failure" if level in {"失敗", "ファンブル", "自動失敗"} else "success"

        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", f"{record['roller']} - {record['date']}\n", "name")
        self.result_text.insert("end", f"{record['command']}\n", "command")
        self.result_text.insert("end", record["result"], level_tag)
        self.result_text.configure(state="disabled")

    def _copy_result(self) -> None:
        if not self.current_copy_text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.current_copy_text)
        self.root.update()
        self.status_var.set("結果をコピーしました")

    def _toggle_history(self) -> None:
        self.root.update_idletasks()
        width = max(self.root.winfo_width(), 460)
        if self.history_open:
            self.history_frame.pack_forget()
            self.history_button.configure(text="履歴を開く ▾")
            self.root.geometry(f"{width}x{self.COLLAPSED_HEIGHT}")
        else:
            self.history_frame.pack(fill="both", expand=True)
            self.history_button.configure(text="履歴を閉じる ▴")
            self.root.geometry(f"{width}x{self.EXPANDED_HEIGHT}")
        self.history_open = not self.history_open

    def _refresh_history(self) -> None:
        if not hasattr(self, "history_text"):
            return
        self.history_text.configure(state="normal")
        self.history_text.delete("1.0", "end")
        if not self.history:
            self.history_text.insert("end", "履歴はまだありません。")
        else:
            for record in reversed(self.history):
                time_text = record.get("time", "").replace("T", " ")
                self.history_text.insert("end", f"{record.get('roller', '')}  {time_text}\n")
                self.history_text.insert("end", f"{record.get('command', '')}\n")
                self.history_text.insert("end", f"{record.get('result', '')}\n\n")
        self.history_text.configure(state="disabled")

    def _clear_history(self) -> None:
        if not self.history:
            return
        if not messagebox.askyesno("履歴を消す", "保存されたダイス履歴をすべて消しますか？"):
            return
        self.history.clear()
        self._save_state()
        self._refresh_history()
        self.status_var.set("履歴を消しました")

    def _on_close(self) -> None:
        self._save_state()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    HoshimiDiceApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
