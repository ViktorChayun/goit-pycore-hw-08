import sys
import re
from functools import wraps
from collections import UserDict
from datetime import datetime
from datetime import timedelta
from datetime import date
import pickle

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    pass

class Phone(Field):
    def __init__(self, value):
        if not self._is_valid(value):
            raise ValueError(f"Incorret phone value: '{value}'")
        super().__init__(value)
    
    def _is_valid(self, value)->bool:
        pattern = r"^\d{10}$"
        return re.match(pattern, value) if value else False

    def __repr__(self):
        return f"{self.value}"

class Birthday(Field):
    def __init__(self, value):
        try:
            datetime.strptime(value, "%d.%m.%Y")
            super().__init__(value)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
    
    @property
    def date(self)->date:
        return datetime.strptime(self.value, "%d.%m.%Y").date() if self.value else None
        
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = [] # список з обєктами класу Phone
        self.birthday = None
        
    def add_phone(self, phone):
        p = Phone(phone)
        # перевірка чи такий номер вже існує, щоб не додавати дубль
        if not self.find_phone(phone):
            self.phones.append(p)
    
    def remove_phone(self, phone):
        value = self.find_phone(phone)
        if value:
            self.phones.remove(value)
    
    def edit_phone(self, old_phone:str, new_phone:str):
        # якщо номеру телефону який хочемо змінити не існує або новий номер некоректно заданий - викликаємо помилку
        if not self.find_phone(old_phone):
            raise ValueError(f"Can't edit. Old phone '{old_phone}' is not found.")        
        # якщо телефон дійсно змінився
        if old_phone !=  new_phone:
            self.add_phone(new_phone)
            self.remove_phone(old_phone)
    
    def find_phone(self, phone:str) -> Phone:
        for p in self.phones:
            if p.value == phone:
                return p
        return None
        
    def __str__(self):
        return f"Contact name: {self.name}, birthday: {self.birthday}, phones: {'; '.join(p.value for p in self.phones)}"

    def add_birthday(self, birthday:str):
        self.birthday = Birthday(birthday)
            
class AddressBook(UserDict):
    def add_record(self, record:Record):
        # якщо такого запису по імені людини ще не існує, тоді додаємо
        if not self.find(record.name.value):
            self.data[record.name.value.lower()] = record
    
    def find(self, name)->Record:
        return self.data.get(name.lower())

    def delete(self, name):
        if self.find(name):
            del self.data[name]
            
    def __str__(self):
        return "\n".join(str(rec) for rec in self.data.values())

    @staticmethod
    def _find_next_weekday(start_date, weekday:int):
        days_ahead = weekday - start_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return start_date + timedelta(days=days_ahead)
    
    @staticmethod
    def _adjust_for_weekend(date):
        if date.weekday() >= 5:
            return AddressBook._find_next_weekday(date, 0)
        return date

    def get_upcoming_birthdays(self, days=7):
        today = date.today()
        upcoming_birthdays = []
        
        for record in self.data.values():
            if record.birthday:
                dt = record.birthday.date # атрибут класу Birthday, що повертає значення в datetime
                # дата народження в цьому році
                birthday_this_year = dt.replace(year=today.year)
                
                # ящо ДН вже відбувся вцьому році, дивомось коли буде в наступному році
                if birthday_this_year < today:
                    birthday_this_year = dt.replace(year=today.year+1)

                if 0 <= (birthday_this_year - today).days <= days:
                    birthday_this_year = AddressBook._adjust_for_weekend(birthday_this_year)
                    congratulation_date_str = birthday_this_year.strftime("%d.%m.%Y")
                    upcoming_birthdays.append({"name": str(record.name), "birthday": congratulation_date_str})
        
        return upcoming_birthdays

    #def __getstate__(self):
    #    return self.__dict__
    
    #def __setstate__(self, value):
    #    self.__dict__.update(value)
################################
def input_error(func):
    @wraps(func)
    def inner_func(*args, **kwargs) -> str:
        try:
            return func(*args, **kwargs)
        except KeyError as err:
            return f"Invalid command: {err}"
        except ValueError as err:
            return f"Invalid command: {err}"
        except IndexError as err:
            return f"Invalid command: {err}"
        except Exception as  err:
            return f"Unexpected error: {err}"
    return inner_func

@input_error
def parse_input(user_input:str):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args

#add [ім'я] [номер телефону]
@input_error
def add_contact(args, book: AddressBook)->str:
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    
    if phone:
        record.add_phone(phone)
    return message

#change [ім'я] [старий телефон] [новий телефон]
@input_error
def change_contact(args, book: AddressBook)->str:
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        return f"Contact '{name}' is not found."
    record.edit_phone(old_phone, new_phone)
    return "Phone is changed."

#phone [ім'я]
@input_error
def show_phone(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    return record.phones

#all
@input_error
def show_all(args, book:AddressBook)->str:
    return str(book)

#add-birthday [ім'я] [дата народження]
@input_error
def add_birthday(args, book:AddressBook)->str:
    name, birthday, *_ = args
    record = book.find(name)
    record.add_birthday(birthday)
    return "Birthday is added"

#show-birthday [ім'я]
@input_error
def show_birthday(args, book:AddressBook)->str:
    name, *_ = args
    record = book.find(name)
    return str(record.birthday)

#birthdays
@input_error
def birthdays(args, book:AddressBook):
    # Показати дні народження на найближчі 7 днів з датами, коли їх треба привітати.
    return book.get_upcoming_birthdays()

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено
###################################################
def main():
    filename = "my_address_book.pkl"
    book = load_data(filename)
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        match command:
            case "close" | "exit":
                save_data(book, filename)  # Викликати перед виходом з програми
                print("Good bye!")
                sys.exit(0)
            case "hello":
                print("How can I help you?")
            case "all":
                print(show_all(args, book))
            #add [ім'я] [номер телефону]    
            case "add":
                print(add_contact(args, book))
            #change [ім'я] [новий номер телефону]
            case "change":
                print(change_contact(args, book))
            #phone [ім'я]
            case "phone":
                print(show_phone(args, book))
            case "add-birthday":
                print(add_birthday(args, book))
            case "show-birthday":
                print(show_birthday(args, book))
            case "birthdays":
                print(birthdays(args, book))
            case _:
                print("Invalid command.")
###################################################
if __name__ == "__main__":
    main()