import curses
import curses.textpad
from sqlalchemy import MetaData, Table, Column, Integer, String, create_engine, Boolean, select, update, delete, insert

###!!! Нужно добавить под задачи
###!!! Исправить отричовку если все задачи не влезают в размеры консоли
###!!! Добавить более интуинтивный дисплей с подсказками внизу консоли
###!!! Отредачить код под PEP8

class ToDoPad():
    def __init__(self, stdscr) -> None:
        # define
        self.enter = 10
        self.up_key = 450
        self.down_key = 456
        self.db = DB()
        #
        self.task_dict = {item[1]: item[2] for item in self.db.select_task()}
        self.task_list = list(self.task_dict)
        curses.noecho()
        curses.cbreak()
        self.stdscr = stdscr
        self.cursor = 0
        self.actulit_db = True #  если в базе данных что то менялось то будет False и нужно будет занова доставтьданные из бд задачи
        self.write_gui()
            
    def add_task(self):
        win = curses.newwin(1, 80, self.cursor, 0)
        box = curses.textpad.Textbox(win)
        self.stdscr.addstr(self.max_y - 1, 0, "CTRL + G to exit")
        self.stdscr.refresh()
        box.edit()
        box.gather().replace("\n", "")
        self.db.add_task(box.gather().replace("\n", ""))
        self.actulit_db = False
        self.write_gui()
    
    def remove_task(self):
        self.db.remove_task(self.task_list[self.write_zone + self.cursor])
        self.actulit_db = False
        self.cursor = self.write_zone
        self.write_gui()
        
    def edit_task(self):
        win = curses.newwin(1, 70, self.cursor, 9 + len(str(self.write_zone + self.cursor)))
        win.addstr(self.task_list[self.write_zone + self.cursor])
        box = curses.textpad.Textbox(win)
        self.stdscr.addstr(self.max_y - 1, 0, "CTRL + G to exit edit mode")
        self.stdscr.refresh()
        box.edit()
        self.db.edit_task(self.task_list[self.write_zone + self.cursor], box.gather().replace("\n", ""))
        self.actulit_db = False
        self.write_gui()
    
    def curet_zone(self):
        self.stdscr.clear()
        if self.cursor > self.max_y:
            self.write_zone += self.max_y
            self.cursor = 0
        elif self.cursor < self.write_zone and self.write_zone != 0:
            self.write_zone -= self.max_y
            self.cursor = self.max_y
        
            
    def write_gui(self):
        self.stdscr.clear()
        self.write_zone = 0
        self.max_y, self.max_x = self.stdscr.getmaxyx() ###!!! исправит отрисовку задач которые не влазиют в окно
        """Отрисовывает графическое окружение"""
        if self.actulit_db == False:
            """Получение актуальных данных из бд"""
            self.task_dict = {item[1]: item[2] for item in self.db.select_task()}
            self.task_list = list(self.task_dict)
            self.actulit_db = True
        if self.task_dict != {}:
            self.curet_zone()
            for index, value in enumerate(self.task_list[self.write_zone:self.max_y + self.write_zone]):  
                self.stdscr.addstr(index, 0, f"[{'✓' if self.task_dict[value] else ' '}]> {index + 1} <  {value}" if self.cursor == index else f"[{'✓' if self.task_dict[value] else ' '}]  {index + 1}    {value}") 
        else: ## исправить исключение если список пуст
            self.stdscr.addstr(0, 0, "Push \"a\" to add task, push \"r\" to remove task, \"e\" to edit task or \"q\" to exit")
        self.stdscr.refresh()
    
    def run(self):
        while True:
            """Оброботчик кнопок"""
            key = self.stdscr.getch()
            if key == ord("q"):
                break
            if "a" == chr(key):
                self.add_task()
                
            if "r" == chr(key):
                if self.task_list != []:
                    self.remove_task()
                
            if "e" == chr(key):
                if self.task_list != []:
                    self.edit_task()
                
            if 259 == key:
                if 0 != self.cursor:
                    self.cursor -= 1
                    self.write_gui()
            if 258 == key:
                if self.cursor != len(self.task_list):
                    self.cursor += 1
                    self.write_gui()
            if 10 == key:
                if self.task_list != []:
                    if self.task_dict[self.task_list[self.cursor]]:
                        self.task_dict[self.task_list[self.cursor]] = False
                        self.db.change_status(self.task_list[self.cursor], False)
                    else:
                        self.task_dict[self.task_list[self.cursor]] = True
                        self.db.change_status(self.task_list[self.cursor], True)
                    self.write_gui()

    
        
class DB():
    def __init__(self) -> None:
        self.engine = create_engine("sqlite:///data.sql")
        self.metadata = MetaData()
        self.to_do_list = Table("to_do_list", self.metadata, Column("id", Integer(), primary_key=True), Column("task", String(256), nullable=False), Column("status", Boolean, default=False))
        self.metadata.create_all(self.engine)
    
    def select_task(self):
        """Эта функция возрашает все записи в базе данных"""
        cursor = self.engine.connect()
        query = select(self.to_do_list)
        response = cursor.execute(query).fetchall()
        cursor.close()
        return response
    
    def change_status(self, task: str, status: bool):
        """Меняет состояние задания"""
        cursor = self.engine.connect()
        query = update(self.to_do_list).where(self.to_do_list.columns.task == task).values(status=status)
        cursor.execute(query)
        cursor.commit()
        cursor.close()
        
    def edit_task(self, task, edit_task):
        cursor = self.engine.connect()
        query = update(self.to_do_list).where(self.to_do_list.columns.task == task).values(task=edit_task)
        cursor.execute(query)
        cursor.commit()
        cursor.close()
        
    def add_task(self, task):
        cursor = self.engine.connect()
        query = insert(self.to_do_list).values(task=task)
        cursor.execute(query)
        cursor.commit()
        cursor.close()
        
    def remove_task(self, task):
        cursor = self.engine.connect()
        query = delete(self.to_do_list).where(self.to_do_list.columns.task == task)
        cursor.execute(query)
        cursor.commit()
        cursor.close()
def main(stdscr):
    win = ToDoPad(stdscr)
    win.run()
curses.wrapper(main)