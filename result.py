import os
import sqlite3
import tempfile
from subprocess import call

from rich.console import Console
from rich.prompt import IntPrompt, Confirm

console = Console()
console.clear()


def create_db():  # Уверяемся в существовании таблиц с инфой
    conn = sqlite3.connect(database='records.db')
    cur = conn.cursor()

    cur.executescript('''
                CREATE TABLE IF NOT EXISTS body(
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        text_in TEXT
                ); --Для тел записей

                CREATE TABLE IF NOT EXISTS header(
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        text_in TEXT
                ); --Для заголовков записей

                CREATE TABLE IF NOT EXISTS h_and_b(
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        h_id INTEGER,
                                        b_id INTEGER,
                                        create_time TEXT
                ); --Для связки всего и вся (и времени)
                ''')
    conn.commit()
    conn.close()


def input_text(message):
    EDITOR = os.environ.get('EDITOR')

    initial_message = str.encode(message)
    with tempfile.NamedTemporaryFile(suffix=".tmp") as tf:
        tf.write(initial_message)
        tf.flush()
        call([EDITOR, tf.name])

        tf.seek(0)
        edited_message = tf.read()
        return edited_message.decode("utf-8")


def create_record(header, body):
    conn = sqlite3.connect('records.db')
    cur = conn.cursor()
    cur.executescript(f'''
                    INSERT INTO header(text_in)
                    VALUES ('{header[54 : -1]}');

                    INSERT INTO body(text_in)
                    VALUES ('{body[21 : -1]}');

                    INSERT INTO h_and_b(
                                h_id,
                                b_id,
                                create_time)
                    VALUES(
                        (SELECT MAX(id) FROM header),
                        (SELECT MAX(id) FROM body),
                        datetime('now', 'localtime'));
                ''')
    conn.commit()
    conn.close()


def read_record():
    conn = sqlite3.connect('records.db')
    cur = conn.cursor()

    cur.execute('''
                SELECT s.id,
                       SUBSTR(h.text_in, 1, 100) AS text_in
                  FROM header h,
                       h_and_b s
                 WHERE h.id = s.h_id
                ''')
    id_array = []
    for id, text_in in cur:
        console.print(f'[blue]{id}[/blue] : [magenta]{text_in}[/magenta]\n')
        id_array.append(str(id))
    cur_id = IntPrompt.ask('Введите id запипси для чтения',
                           choices=id_array,
                           show_choices=False)
    cur.execute(f'''
                SELECT h.text_in, b.text_in
                  FROM header h,
                       body b,
                       h_and_b s
                 WHERE h.id = s.h_id
                   AND b.id = s.b_id
                   AND s.id = {cur_id}
                ''')

    for header, body in cur:
        console.print(f'[blue]{header}[/blue]\n[magenta]{body}[/magenta]\n')

    conn.close()


def delete_record():
    conn = sqlite3.connect('records.db')
    cur = conn.cursor()

    cur.execute('''
                SELECT s.id,
                       SUBSTR(h.text_in, 1, 100) AS text_in
                  FROM header h,
                       h_and_b s
                 WHERE h.id = s.h_id
                ''')
    id_array = []
    console.clear()
    for id, text_in in cur:
        console.print(f'[blue]{id}[/blue] : [magenta]{text_in}[/magenta]\n')
        id_array.append(str(id))
    cur_id = IntPrompt.ask('Введите id запипси для удаления',
                           choices=id_array,
                           show_choices=False)

    cur.executescript(f'''DELETE FROM header
                           WHERE id = {cur_id};

                          DELETE FROM body
                           WHERE id = {cur_id};

                          DELETE FROM h_and_b
                           WHERE id = {cur_id};
                      ''')
    console.clear()
    console.print('[magenta]Запись удалена[/magenta]\n')


def redact_record():
    conn = sqlite3.connect('records.db')
    cur = conn.cursor()

    cur.execute('''
                SELECT s.id,
                       SUBSTR(h.text_in, 1, 100) AS text_in
                  FROM header h,
                       h_and_b s
                 WHERE h.id = s.h_id
                ''')
    id_array = []
    for id, text_in in cur:
        console.print(f'[blue]{id}[/blue] : [magenta]{text_in}[/magenta]\n')
        id_array.append(str(id))
    cur_id = IntPrompt.ask('Введите id запипси для правки',
                           choices=id_array,
                           show_choices=False)
    console.clear()
    cur.execute(f'''
                SELECT h.text_in, b.text_in
                  FROM header h,
                       body b,
                       h_and_b s
                 WHERE h.id = s.h_id
                   AND b.id = s.b_id
                   AND s.id = {cur_id}
                ''')
    header, body = cur.fetchone()
    new_header = input_text(message=header)
    new_body = input_text(message=body)
    cur.executescript(f'''
                UPDATE header
                   SET text_in = '{new_header}'
                 WHERE id = {cur_id};

                UPDATE body
                   SET text_in = '{new_body}'
                 WHERE id = '{cur_id}'
                ''')
    conn.commit()
    console.clear()


def do_all_work():
    name = IntPrompt.ask('[blue]Введите номер команды:[/blue]\n' +
                         '  [magenta][bold]1.[/bold] Чтение записи.\n' +
                         '  [bold]2.[/bold] Создание записи.\n' +
                         '  [bold]3.[/bold] Редактирование записи.\n' +
                         '  [bold]4.[/bold] Удаление записи[/magenta]\n',
                         choices=['1', '2', '3', '4'],
                         show_choices=False
                         )
    console.clear()
    match name:
        case 1:
            console.print('Ты выбрал чтение записи.')
            read_record()
        case 2:
            console.print('Ты выбрал создание записи.')
            header = input_text('# Введите заголовок записи ' +
                                '(эта строка будет удалена)')
            body = input_text('# Введите тело записи')
            create_record(header, body)
        case 3:
            console.print('Ты выбрал редактирование записи.')
            redact_record()
        case 4:
            console.print('Ты выбрал удаление записи.')
            delete_record()


def main():
    create_db()

    while True:
        do_all_work()
        if not Confirm.ask('Продолжаем?'):
            console.clear()
            break
        else:
            console.clear()


if __name__ == '__main__':
    main()
