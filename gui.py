import tkinter as tk
import os
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
from core import FarmLabyrinth, RobotFarmer, DirectionType, FarmCellType

class FarmGUI:
    CELL_SIZE = 40
    
    def __init__(self, root, labyrinth: FarmLabyrinth, robot: RobotFarmer):
        self.running = False
        self.root = root
        self.lab = labyrinth
        self.robot = robot

        root.title("РобоФерма")

        self.assets_raw = {}
        for cell_type in FarmCellType:
            path = os.path.join("assets", f"{cell_type.name}.png")
            if os.path.exists(path):
                self.assets_raw[cell_type] = Image.open(path)

        robot_path = os.path.join("assets", "Robot.png")
        if os.path.exists(robot_path):
            self.robot_raw = Image.open(robot_path)
        else:
            self.robot_raw = None

        self.menu_bar = tk.Menu(root)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Экспорт", command=self.export_level)
        self.file_menu.add_command(label="Импорт", command=self.import_level)
        self.menu_bar.add_cascade(label="Файл", menu=self.file_menu)

        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="Команды робота", command=self.show_help)
        self.help_menu.add_command(label="Руководство по использованию", command=self.show_desc)
        self.menu_bar.add_cascade(label="Справка", menu=self.help_menu)

        self.robot_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.robot_menu.add_command(label = "Переместить робота", command=self.enable_move_robot_mode)
        self.menu_bar.add_cascade(label="Робот",menu=self.robot_menu)

        self.move_robot_label = tk.Label(root, text="", fg="blue")
        self.move_robot_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=10)
        self.move_robot_mode = False

        root.config(menu=self.menu_bar)

        self.frame = tk.Frame(root)
        self.frame.grid(row=0, column=0, sticky="nsew")
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        self.command_box = tk.Text(self.frame, width=25, height=10)
        self.command_box.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")

        self.command_box.bind("<Control-c>", self.copy_event)
        self.command_box.bind("<Control-C>", self.copy_event)

        self.command_box.bind("<Control-v>", self.paste_event)
        self.command_box.bind("<Control-V>", self.paste_event)

        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=0)

        self.button_frame = tk.Frame(self.frame)
        self.button_frame.grid(row=1, column=0, pady=5, sticky="ew")

        copy_button = tk.Button(self.button_frame, text="Скопировать", command=lambda: self.command_box.event_generate("<<Copy>>"))
        copy_button.pack(side="left", expand=True, fill="x", padx=2)

        run_button = tk.Button(self.button_frame, text="Выполнить", command=self.execute_commands)
        run_button.pack(side="left", expand=True, fill="x", padx=2)

        paste_button = tk.Button(self.button_frame, text="Вставить", command=lambda: self.command_box.event_generate("<<Paste>>"))
        paste_button.pack(side="left", expand=True, fill="x", padx=2)

        self.canvas = tk.Canvas(
            self.frame,
            width=self.lab.width * self.CELL_SIZE,
            height=self.lab.height * self.CELL_SIZE,
            bg="white"
        )
        self.canvas.grid(row=0, column=1, rowspan=20, sticky="nsew")
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Configure>", self.on_resize)

        self.draw_grid()

    def enable_move_robot_mode(self):
        self.move_robot_mode = True
        self.move_robot_label.config(text="Нажмите на клетку, куда хотите переместить робота")


    def copy_event(self, event=None):
        try:
            widget = event.widget if event is not None else self.command_box
            widget.event_generate("<<Copy>>")
        except Exception:
            pass
        return "break"

    def paste_event(self, event=None):
        try:
            widget = event.widget if event is not None else self.command_box
            widget.event_generate("<<Paste>>")
        except Exception:
            pass
        return "break"
    
    def show_help(self):
            help_window = tk.Toplevel(self.root)
            help_window.title("Справка по командам робота")
            help_window.geometry("500x200")
            help_window.resizable(False, False)

            label = tk.Label(help_window, text="Список доступных команд для робота:", font=("Arial", 12, "bold"))
            label.pack(pady=10)

            help_text = tk.Text(help_window, wrap="word")
            help_text.pack(expand=True, fill="both", padx=10, pady=5)

            commands_info = (
                "Вправо — перемещение робота вправо\n"
                "Влево — перемещение робота влево\n"
                "Вверх — перемещение робота на следующую строку вверх\n"
                "Вниз — перемещение робота на следующую строку вниз\n"
                "ВлевоВверх — перемещение по диагонали вверх влево\n"
                "ВправоВниз — перемещение по диагонали вниз вправо\n"
                "Грядка — создание грядки из почвы в текущей клетке\n"
                "Посадка — выращивание растения в грядке в текущей клетке\n"
            )

            help_text.insert("1.0", commands_info)
            help_text.config(state="disabled")
    
    def show_desc(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("Руководство по использованию")
        help_window.geometry("700x400")
        help_window.resizable(False, False)

        help_text = tk.Text(help_window, wrap="word", font=("Arial", 11))
        help_text.pack(expand=True, fill="both", padx=10, pady=10)

        commands_info = (
            "Руководство по РобоФерме:\n\n"
            "Цель игры:\n"
            "1) Засадить всю почву растениями.\n"
            "2) Добраться до финиша.\n\n"
            "Правила:\n"
            "- Камень и вода блокируют робота.\n"
            "- Только почву можно превратить в грядку.\n"
            "- Только грядку можно превратить в грядку с растениями.\n"
            "- Попытка использовать действия не в том месте приведет к ошибке.\n\n"
            "Управление:\n"
            "- Используйте поле слева для ввода команд.\n"
            "- Список команд доступен 'Справка' → 'Справка по командам робота'\n"
            "- Чтобы изменить клетки уровня, кликайте по ним левой кнопкой мыши.\n\n"
            "Сохранение уровня:\n"
            "1) Меню 'Файл' → 'Экспорт'\n"
            "2) Скопируйте код с помощью Ctrl+C (английская раскладка) или кнопки 'Скопировать'.\n\n"
            "Загрузка уровня:\n"
            "1) Меню 'Файл' → 'Импорт'\n"
            "2) Вставьте код с помощью Ctrl+V (английская раскладка) или кнопки 'Вставить'.\n\n"
            "Советы по копированию и вставке:\n"
            "- Выделите текст, затем используйте кнопку 'Скопировать' или Ctrl+C.\n"
            "- Чтобы вставить текст, используйте кнопку 'Вставить' или Ctrl+V."
        )

        help_text.insert("1.0", commands_info)
        help_text.config(state="disabled")
    
    def on_resize(self, event):
        w = event.width
        h = event.height
        self.CELL_SIZE = max(10, min(w // self.lab.width, h // self.lab.height))
        self.draw_grid()

    def export_level(self):
        code = self.robot.encode_state()
        export_window = tk.Toplevel(self.root)
        export_window.title("Экспорт уровня")
        export_window.geometry("600x150")
        export_window.resizable(False, False)

        label = tk.Label(export_window, text="Код уровня (скопируйте):")
        label.pack(pady=5)

        text_box = tk.Text(export_window, height=5, wrap="word")
        text_box.pack(expand=True, fill="both", padx=10, pady=5)
        text_box.insert("1.0", code)
        text_box.config(state="normal")

        text_box.focus()
        text_box.tag_add("sel", "1.0", "end")

        text_box.bind("<Control-c>", self.copy_event)
        text_box.bind("<Control-C>", self.copy_event)

        copy_button = tk.Button(export_window, text="Скопировать", command=self.copy_event)
        copy_button.pack(pady=5)

    def import_level(self):
        import_window = tk.Toplevel(self.root)
        import_window.title("Импорт уровня")
        import_window.geometry("600x200")
        import_window.resizable(False, False)

        label = tk.Label(import_window, text="Вставьте код уровня:")
        label.pack(pady=5)

        text_box = tk.Text(import_window, height=8, wrap="word")
        text_box.pack(expand=True, fill="both", padx=10, pady=5)
        text_box.focus()

        def load_code():
            code = text_box.get("1.0", "end").strip()
            if code:
                try:
                    self.robot.decode_state(code)
                    self.draw_grid()
                    import_window.destroy()
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Невозможно загрузить код:\n{e}")

        load_button = tk.Button(import_window, text="Загрузить", command=load_code)
        load_button.pack(pady=5)

        paste_button = tk.Button(import_window, text="Вставить", command=self.paste_event)
        paste_button.pack(pady=5)

        text_box.bind("<Control-v>", self.paste_event)
        text_box.bind("<Control-V>", self.paste_event)

    def draw_grid(self):
        self.canvas.delete("all")
        self._img_refs = []

        for x in range(self.lab.width):
            for y in range(self.lab.height):
                cell = self.lab.cells[y][x]
                gui_x = x * self.CELL_SIZE
                gui_y = y * self.CELL_SIZE 

                raw_img = self.assets_raw.get(cell.cell_type)
                if raw_img:
                    resized = raw_img.resize((self.CELL_SIZE, self.CELL_SIZE), Image.NEAREST)
                    tk_img = ImageTk.PhotoImage(resized)
                    self.canvas.create_image(gui_x, gui_y, anchor="nw", image=tk_img)
                    self._img_refs.append(tk_img)
                else:
                    color = {
                        0: "#7C8024",  # Garden
                        1: "#C2B280",  # Soil
                        2: "#DAA520",  # Harvest
                        3: "#90EE90",  # Greenhouse
                        4: "#1E90FF",  # Water
                        5: "#CD6F26",  # Barrier
                        6: "#000000",  # Finish
                    }.get(cell.cell_type.value, "white")
                    self.canvas.create_rectangle(
                        gui_x, gui_y,
                        gui_x + self.CELL_SIZE, gui_y + self.CELL_SIZE,
                        fill=color, outline="black"
                    )

                if cell.has_robot and self.robot_raw:
                    size = int(self.CELL_SIZE * 0.8)
                    offset = (self.CELL_SIZE - size) // 2
                    robot_img = self.robot_raw.resize((size, size), Image.NEAREST)
                    tk_robot = ImageTk.PhotoImage(robot_img)
                    self.canvas.create_image(gui_x + offset, gui_y + offset, anchor="nw", image=tk_robot)
                    self._img_refs.append(tk_robot)

    def on_canvas_click(self, event):
        if self.running:
            return
        x = event.x // self.CELL_SIZE
        y = event.y // self.CELL_SIZE

        cell = self.lab.get_cell(x, self.lab._to_internal_y(y))
        if not cell:
            return

        if self.move_robot_mode:
            self.robot.place(x, self.lab._to_internal_y(y))
            self.move_robot_mode = False
            self.move_robot_label.config(text="")
        else:
            cell.cell_type = FarmCellType((cell.cell_type.value + 1) % 7)
        self.draw_grid()

    def execute_commands(self):
        commands = self.command_box.get("1.0", tk.END).strip().split("\n")
        self.temp_robot_cell = self.robot.current_cell
        self.command_box.config(state="disabled")
        for child in self.button_frame.winfo_children():
            if isinstance(child, tk.Button):
                child.config(state="disabled")
        self.running = True


        self._execute_step(commands, 0)

    def _execute_step(self, commands, index):
        if len(commands) == 1 and commands[0] == "":
            self.command_box.config(state="normal")
            for child in self.button_frame.winfo_children():
                if isinstance(child, tk.Button):
                    child.config(state="normal")
            self.running = False
            messagebox.showinfo("Что-то пошло не так", "Ты не ввёл никакую команду!")
            return
        if index == 0:
            self._initial_state_code = self.robot.encode_state()
        if index >= len(commands):
            if self.robot.current_cell.cell_type == FarmCellType.Finish:
                for cell in self.lab.get_iterator():
                    if cell.cell_type in (FarmCellType.Soil, FarmCellType.Garden):
                        messagebox.showinfo(
                            "Что-то пошло не так!",
                            "Уровень не был пройден, ещё остались грядки или почва, попробуй ещё раз!"
                        )
                        break
                else:
                    messagebox.showinfo("Поздравляем!", "Уровень успешно пройден!")
            else:
                messagebox.showinfo(
                    "Что-то пошло не так!",
                    "Уровень не был пройден, ты не добрался до финиша, попробуй ещё раз!"
                )

            self.robot.decode_state(self._initial_state_code)

            self.command_box.config(state="normal")
            for child in self.button_frame.winfo_children():
                if isinstance(child, tk.Button):
                    child.config(state="normal")
            self.running = False
            self.draw_grid()
            return

        cmd = commands[index].strip()
        result = 1
        msg = ""
        if cmd in ("Вправо", "Влево", "Вниз", "Вверх", "ВлевоВверх", "ВправоВниз"):
            msg = "робот разбился"
        if cmd in ("Грядка", "Посадка"):
            msg = "робот начал работать не в том месте"
        if cmd == "Вправо":
            result = self.robot.move_right()
        elif cmd == "Влево":
            result = self.robot.move_left()
        elif cmd == "Вверх":
            result = self.robot.move_next_row()
        elif cmd == "Вниз":
            result = self.robot.move_previous_row()
        elif cmd == "ВлевоВверх":
            result = self.robot.move_up()
        elif cmd == "ВправоВниз":
            result = self.robot.move_down()
        elif cmd == "Посадка":
            result = self.robot.action_garden()
        elif cmd == "Грядка":
            result = self.robot.action_soil()
        else:
            messagebox.showerror("Ошибка", f"Неизвестная команда: {cmd}")
            self.robot.place(self.temp_robot_cell.x, self.temp_robot_cell.y)
            self.command_box.config(state="normal")
            for child in self.button_frame.winfo_children():
                if isinstance(child, tk.Button):
                    child.config(state="normal")
            self.running = False
            self.draw_grid()
            return
        if result is None:
            messagebox.showinfo(
                    "Что-то пошло не так!",
                    f"Уровень не был пройден, {msg}, попробуй ещё раз!"
                )
            self.robot.decode_state(self._initial_state_code)

            self.command_box.config(state="normal")
            for child in self.button_frame.winfo_children():
                if isinstance(child, tk.Button):
                    child.config(state="normal")
            self.running = False
            self.draw_grid()
            return
        self.draw_grid()
        self.root.after(300, lambda: self._execute_step(commands, index + 1))
