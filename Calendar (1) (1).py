import calendar
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from tkinter import font
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect("Calendar.db")
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        fio TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT CHECK(role IN ('teacher', 'student')) NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY,
            dateevent date not null,
            title TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY,
            event_id INTEGER NOT NULL,
            student_name TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE 
    )''')

    listuser = [
        ('Лукина Екатерина', hash_password('1234'), 'student'),
        ('Юлия Васильевна', hash_password('123456789'), 'teacher'),
        ('123', hash_password('123'), 'teacher'),
        ('1234', hash_password('1234'), 'student')
    ]

    for user in listuser:
        c.execute('SELECT * FROM users WHERE fio = ? AND password = ?', (user[1], user[2]))
        if c.fetchone() is None:
            c.execute('INSERT INTO users (fio, password, role) VALUES (?, ?, ?)',user)

    conn.commit()
    conn.close()

current_user = None

def register_user(fio, password, role):
    conn = sqlite3.connect("Calendar.db")
    c = conn.cursor()
    hashed_password = hash_password(password)
    c.execute("INSERT INTO users (fio, password, role) VALUES (?, ?, ?)",
              (fio, hashed_password, role ))
    conn.commit()
    conn.close()
    return "Пользователь успешно зарегистрирован."


def register():
    win = tk.Toplevel()  # Открываем новое окно
    win.title("Регистрация")
    win.geometry("400x300")
    def submit():
        fio = entry_fio.get().strip()
        password = entry_password.get().strip()

        if not fio or not password or not role_var.get():
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены и роль выбрана")
            return

        # Попытка регистрации пользователя
        result = register_user(fio, password, role_var.get())
        if "успешно зарегистрирован" in result:
            messagebox.showinfo("Успех", result)
            win.destroy()
        else:
            messagebox.showerror("Ошибка", result)

    tk.Label(win, text="ФИО:", width=50, height=2).pack()
    entry_fio = tk.Entry(win)
    entry_fio.pack()

    tk.Label(win, text="Пароль:", width=50, height=2).pack()
    entry_password = tk.Entry(win, show="*")
    entry_password.pack()

    role_var = tk.StringVar(value="student")  # Установка значения по умолчанию на "Ученик"
    tk.Radiobutton(win, text="Ученик", variable=role_var, value="student", width=50, height=2).pack()

    tk.Button(win, text="Зарегистрироваться", command=submit, width=50, height=2).pack()

def login_user(fio, password):
    conn = sqlite3.connect("Calendar.db")
    c = conn.cursor()
    hashed_password = hash_password(password)
    c.execute("SELECT id, role FROM users WHERE fio = ? AND password = ?", (fio, hashed_password))
    user = c.fetchone()
    conn.close()
    return user

def login(entry_login, entry_password):
    fio = entry_login.get()
    password = entry_password.get()
    user = login_user(fio, password)
    global current_user
    if user:
        global current_user
        current_user = user
        role = current_user[1]
        if role == "student":
            load_interface()
        elif role == "teacher":
            display_teacher()
        else:
            messagebox.showerror("Ошибка", "Неизвестная роль пользователя.")
    else:
        messagebox.showerror("Ошибка", "Неправильные ФИО или пароль")

def get_event():
    conn = sqlite3.connect("Calendar.db")
    c = conn.cursor()
    c.execute("SELECT DISTINCT title FROM events")
    events = [row[0] for row in c.fetchall()]
    conn.close()
    return events

def get_events():
    conn = sqlite3.connect("Calendar.db")
    c = conn.cursor()
    c.execute("SELECT id, dateevent, title FROM events")
    events = c.fetchall()
    conn.close()
    return events

def load_interface():
    for widget in root.winfo_children():
        widget.destroy()

    year = tk.IntVar(value=2025)
    month = tk.IntVar(value=5)

    year_label = ttk.Label(root, text="Год:")
    year_label.grid(row=0, column=0, padx=5, pady=5)
    year_entry = ttk.Entry(root, textvariable=year, width=6)
    year_entry.grid(row=0, column=1, padx=5, pady=5)

    month_label = ttk.Label(root, text="Месяц:")
    month_label.grid(row=0, column=2, padx=5, pady=5)
    month_entry = ttk.Entry(root, textvariable=month, width=3)
    month_entry.grid(row=0, column=3, padx=5, pady=5)

    show_button = ttk.Button(root, text="Показать", command=lambda: show_calendar(year.get(), month.get()))
    show_button.grid(row=0, column=4, padx=5, pady=5)

    tk.Label(root, text="Введите ваше ФИО:").grid(row=2, column=0, padx=5, pady=5)
    entry_name = tk.Entry(root)
    entry_name.grid(row=2, column=1, padx=5, pady=5)

    # Комбобокс для выбора мероприятия
    tk.Label(root, text="Выберите мероприятие:").grid(row=3, column=0, padx=5, pady=20)
    events = get_events()
    event_dates = [dateevent for _, dateevent, _ in events]
    event_combobox = ttk.Combobox(root, values=event_dates, state='readonly')
    event_combobox.grid(row=3, column=1, padx=5, pady=5)

    global calendar_text
    calendar_font = font.Font(family="Courier New", size=25)  # моноширинный шрифт для ровного отображения

    calendar_text = tk.Text(root, wrap="word", font=calendar_font)
    calendar_text.grid(row=1, column=0, columnspan=5, padx=5, pady=5, sticky='nsew')

    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(0, weight=1)

    def display_events():
        # Очищаем текстовое поле или список перед добавлением новых данных
        calendar_text.delete(1.0, tk.END)  # Очистка текстового виджета

        conn = sqlite3.connect("Calendar.db")
        c = conn.cursor()
        c.execute("SELECT event_id, student_name FROM registrations")
        events = c.fetchall()  # Получаем все события

        if not events:
            calendar_text.insert(tk.END, "Нет записей.\n")
        else:
            # Форматируем вывод
            for event in events:
                event_id, name = event
                calendar_text.insert(tk.END, f"{event_id} - {name}\n")

    display_button = tk.Button(root, text="Показать записи", command=display_events)
    display_button.grid(row=1, column=5, padx=5, pady=5)

    def display_events():
        # Очищаем текстовое поле или список перед добавлением новых данных
        calendar_text.delete(1.0, tk.END)  # Очистка текстового виджета

        conn = sqlite3.connect("Calendar.db")
        c = conn.cursor()
        c.execute("SELECT dateevent, title FROM events")
        events = c.fetchall()  # Получаем все события

        if not events:
            calendar_text.insert(tk.END, "Нет доступных мероприятий.\n")
        else:
            # Форматируем вывод
            for event in events:
                date, title = event
                calendar_text.insert(tk.END, f"{date} - {title}\n")

    display_button = tk.Button(root, text="Показать мероприятия", command=display_events)
    display_button.grid(row=0, column=5, padx=5, pady=5)

    # Функция для сохранения регистрации студента на мероприятие
    def register_student(event_id, student_name):
        conn = sqlite3.connect("Calendar.db")
        c = conn.cursor()
        c.execute('INSERT INTO registrations (event_id, student_name) VALUES (?, ?)', (event_id, student_name))
        conn.commit()
        conn.close()
        messagebox.showinfo("Успех", f"Студент '{student_name}' успешно зарегистрирован на мероприятие!")

    # Функция для регистрации студента на мероприятие
    def select_event_and_register():
        event_id = event_combobox.get()
        student_name = entry_name.get().strip()

        if not student_name:
            messagebox.showwarning("Ошибка", "Пожалуйста, введите ваше ФИО.")
            return

        if not event_id:
            messagebox.showwarning("Ошибка", "Пожалуйста, выберите мероприятие.")
            return

        register_student(event_id, student_name)

    tk.Button(root, text="Зарегистрироваться", command=select_event_and_register).grid(row=4, column=1, padx=5, pady=10)

def display_teacher():
    for widget in root.winfo_children():
        widget.destroy()

    year = tk.IntVar(value=2025)
    month = tk.IntVar(value=5)

    year_label = ttk.Label(root, text="Год:")
    year_label.grid(row=0, column=1, padx=5, pady=5)
    year_entry = ttk.Entry(root, textvariable=year, width=6)
    year_entry.grid(row=0, column=2, padx=5, pady=5)

    month_label = ttk.Label(root, text="Месяц:")
    month_label.grid(row=0, column=3, padx=5, pady=5)
    month_entry = ttk.Entry(root, textvariable=month, width=3)
    month_entry.grid(row=0, column=4, padx=5, pady=5)

    show_button = ttk.Button(root, text="Показать", command=lambda: show_calendar(year.get(), month.get()))
    show_button.grid(row=0, column=5, padx=5, pady=5)

    l = ttk.Label(root, text="Добавить новое мероприятие:")
    l.grid(row=2, column=0, padx=5, pady=5)

    entry_new_events = tk.Entry(root)
    entry_new_events.grid(row=2, column=1, padx=5, pady=5)

    tk.Label(text="Дата мероприятия (дд-мм-гггг)").grid(row=3, column=0, padx=5, pady=5)
    entry_date = tk.Entry()
    entry_date.grid(row=3, column=1, padx=5, pady=5)

    global calendar_text
    calendar_font = font.Font(family="Courier New", size=25)  # моноширинный шрифт для ровного отображения

    calendar_text = tk.Text(root, wrap="word", font=calendar_font)
    calendar_text.grid(row=1, column=0, columnspan=5, padx=5, pady=5, sticky='nsew')

    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(0, weight=1)

    def display_events():
        # Очищаем текстовое поле или список перед добавлением новых данных
        calendar_text.delete(1.0, tk.END)  # Очистка текстового виджета

        conn = sqlite3.connect("Calendar.db")
        c = conn.cursor()
        c.execute("SELECT event_id, student_name FROM registrations")
        events = c.fetchall()  # Получаем все события

        if not events:
            calendar_text.insert(tk.END, "Нет записей.\n")
        else:
            # Форматируем вывод
            for event in events:
                event_id, name = event
                calendar_text.insert(tk.END, f"{event_id} - {name}\n")

    display_button = tk.Button(root, text="Показать записи", command=display_events)
    display_button.grid(row=1, column=5, padx=5, pady=5)

    def display_events():
        # Очищаем текстовое поле или список перед добавлением новых данных
        calendar_text.delete(1.0, tk.END)  # Очистка текстового виджета

        conn = sqlite3.connect("Calendar.db")
        c = conn.cursor()
        c.execute("SELECT dateevent, title FROM events")
        events = c.fetchall()  # Получаем все события

        if not events:
            calendar_text.insert(tk.END, "Нет доступных мероприятий.\n")
        else:
            # Форматируем вывод
            for event in events:
                date, title = event
                calendar_text.insert(tk.END, f"{date} - {title}\n")

    display_button = tk.Button(root, text="Показать мероприятия", command=display_events)
    display_button.grid(row=0, column=5, padx=5, pady=5)

    def delete_event():
        selected_date = event_combobox.get()

        conn = sqlite3.connect("Calendar.db")
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()

        # Получаем ID события по дате
        c.execute('SELECT id FROM events WHERE dateevent = ?', (selected_date,))
        result = c.fetchone()

        if result:
            event_id = result[0]
            # Удаляем связанные регистрации
            c.execute('DELETE FROM registrations WHERE event_id = ?', (event_id,))
            # Удаляем событие
            c.execute('DELETE FROM events WHERE id = ?', (event_id,))
            conn.commit()
            messagebox.showinfo("Ок", f"Мероприятие '{selected_date}' и связанные регистрации удалены.")
        else:
            messagebox.showerror("Ошибка", f"Мероприятие '{selected_date}' не найдено.")

        conn.close()

    tk.Label(text="Удалить мероприятие").grid(row=3, column=5, padx=5, pady=5)
    events = get_events()
    event_dates = [dateevent for _, dateevent, _ in events]
    event_combobox = ttk.Combobox(root, values=event_dates, state='readonly')
    event_combobox.grid(row=3, column=6, padx=5, pady=5)
    delete = ttk.Button(root, text="Удалить меропритие", command=lambda: delete_event())
    delete.grid(row=4, column=6, padx=5, pady=5)

    def add_new_event():
        new_ev = entry_new_events.get().strip()
        data = entry_date.get()
        if not new_ev:
            messagebox.showwarning("Пусто", "Введите название мероприятия")
            return
        events = get_event()
        if new_ev in events:
            messagebox.showinfo("Инфо", "Такое мероприятие уже существует")
        else:
            # Добавляем предмет в базу данных
            conn = sqlite3.connect("Calendar.db")
            c = conn.cursor()
            c.execute("INSERT INTO events (dateevent, title) VALUES (?, ?)", (new_ev, data))
            conn.commit()
            conn.close()
            messagebox.showinfo("Ок", f"Мероприятие '{new_ev}' добавлено")

    tk.Button(text="Добавить мероприятие", command=add_new_event).grid(row=4, column=1, padx=5, pady=5)

def show_calendar(year, month):
    try:
        year = int(year)
        month = int(month)
    except ValueError:
        calendar_text.delete("1.0", tk.END)
        calendar_text.insert(tk.END, "Некорректный год или месяц")
        return

    cal = calendar.month(year, month)
    calendar_text.delete("1.0", tk.END)
    calendar_text.insert(tk.END, cal)

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    root.title("Календарь")
    root.geometry("1000x600")

    tk.Label(root, text="Введите ФИО для входа:").pack(pady=10)
    entry_login = tk.Entry(root, width=40)
    entry_login.pack(pady=5)

    tk.Label(root, text="Введите пароль:").pack(pady=10)
    entry_password = tk.Entry(root, width=40, show='*')
    entry_password.pack(pady=5)

    login_button = ttk.Button(root, text="Войти", command=lambda: login(entry_login, entry_password))
    login_button.pack(pady=5)
    register_but = ttk.Button(root, text="Регистрация", command=register)
    register_but.pack(pady=5)

    root.mainloop()
