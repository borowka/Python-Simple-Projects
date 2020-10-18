import random
import sqlite3


def print_normal():
    print("""
    1. Create an account
    2. Log into account
    0. Exit""")


def print_logged():
    print("""
    1. Balance
    2. Add income
    3. Do transfer
    4. Close account
    5. Log out
    0. Exit""")


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)

    return conn


def get_account_number(conn):
    sql = """ SELECT account_number FROM metadata; """
    cur = conn.cursor()
    cur.execute(sql)
    account_number = cur.fetchall()
    return max(account_number)[0]


def increment_account_number(conn, number):
    sql = """ INSERT INTO metadata (account_number) VALUES (?); """
    number += 1
    cur = conn.cursor()
    cur.execute(sql, [number])
    conn.commit()


def create_account(conn):
    account_number = get_account_number(conn)
    card_number = "400000" + str(account_number+1)
    checksum = generate_checksum(card_number)
    card_number = card_number + str(checksum)
    card_pin = random.randint(1000, 9999)
    sql = """ INSERT INTO card (number,pin,balance) VALUES(?,?,?); """
    cur = conn.cursor()
    cur.execute(sql, [card_number, card_pin, 0])
    conn.commit()
    increment_account_number(conn, account_number)
    return card_number, card_pin


def get_balance(conn, card_number):
    sql = """ SELECT id,number,pin,balance FROM card WHERE number = ?; """
    cur = conn.cursor()
    cur.execute(sql, [card_number])
    balance = cur.fetchone()[3]
    return balance


def add_balance(conn, balance, card_number):
    actual_balance = get_balance(conn, card_number)
    sql = """ UPDATE card SET balance = ? WHERE number = ?; """
    cur = conn.cursor()
    new_balance = actual_balance + balance
    cur.execute(sql, [new_balance, card_number])
    conn.commit()


def check_login(conn, number, pin):
    sql = ''' SELECT * FROM card where number=(?) and pin=(?)'''
    cur = conn.cursor()
    cur.execute(sql, [number, pin])
    rows = cur.fetchall()
    if len(rows) > 0:
        user = rows[0]
        if number == user[1] and pin == user[2]:
            return True
        else:
            return False
    else:
        return False


def generate_checksum(card_number):
    card_numbers = list(str(card_number))
    for num, x in enumerate(card_numbers):
        if num % 2 == 0:
            card_numbers[num] = str(2 * int(x))
    for num, x in enumerate(card_numbers):
        if int(x) > 9:
            card_numbers[num] = str(int(x) - 9)
    sums = 0
    for x in card_numbers:
        sums += int(x)
    if sums % 10 == 0:
        return 0
    else:
        return 10 - (sums % 10)


def create_table(conn):
    sql = ''' CREATE TABLE IF NOT EXISTS card (id INTEGER PRIMARY KEY, number TEXT UNIQUE, pin TEXT UNIQUE, balance INTEGER DEFAULT 0);'''
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    sql = ''' CREATE TABLE IF NOT EXISTS metadata (account_number INTEGER) '''
    cur.execute(sql)
    conn.commit()
    number = 216000004
    sql = ''' INSERT INTO metadata (account_number) VALUES (?) '''
    cur.execute(sql, [number])
    conn.commit()


def check_card_number(card_number):
    card_numbers = list(str(card_number))
    num = str(card_number)[0:-1]
    checksum = generate_checksum(num)
    if checksum == int(card_numbers[-1]):
        return True
    return False


def transfer_money(conn, money_to_transfer, input_card, logged_number):
    sql = """ UPDATE card SET balance = ? WHERE number = ?; """
    cur = conn.cursor()
    balance_1 = get_balance(conn, logged_number)
    update_balance_1 = balance_1 - money_to_transfer
    cur.execute(sql, [update_balance_1, logged_number])
    conn.commit()
    balance_2 = get_balance(conn, input_card)
    update_balance_2 = balance_2 + money_to_transfer
    cur.execute(sql, [update_balance_2, input_card])
    conn.commit()


def check_if_exists(conn, number):
    sql = """ SELECT EXISTS (SELECT id,number,pin,balance FROM card WHERE number = ?); """
    cur = conn.cursor()
    cur.execute(sql, [number])
    res = cur.fetchone()
    return res[0]


def delete_account(conn, logged_number):
    sql = """ DELETE FROM card WHERE number = ?; """
    cur = conn.cursor()
    cur.execute(sql, [logged_number])
    conn.commit()


def main():
    is_logged = False
    is_running = True
    logged_number = 0
    conn = create_connection('card.s3db')
    create_table(conn)

    while is_running:
        if is_logged is True:
            print_logged()
        else:
            print_normal()
        operation = int(input())

        if operation == 1 and is_logged is False:
            card_number, card_pin = create_account(conn)
            print("Your card has been created")
            print("Your card number:")
            print(card_number)
            print("Your card PIN:")
            print(card_pin)

        elif operation == 2 and is_logged is False:
            print("Enter your card number")
            input_card = input()
            print("Enter your PIN:")
            input_pin = input()
            result = check_login(conn, input_card, input_pin)
            if result:
                print("You have successfully logged in!")
                is_logged = True
                logged_number = input_card
            else:
                print("Wrong card number or PIN!")
        elif operation == 1 and is_logged is True:
            balance = get_balance(conn, logged_number)
            print("Balance: {}".format(balance))
        elif operation == 2 and is_logged is True:
            print("Enter income:")
            income = int(input())
            add_balance(conn, income, logged_number)
            print("Income was added!")
        elif operation == 3 and is_logged is True:
            print("Transfer")
            print("Enter card number:")
            input_card = int(input())
            valid = check_card_number(input_card)
            if valid:
                if input_card != int(logged_number):
                    exist = check_if_exists(conn, input_card)
                    if exist == 1:
                        print("Enter how much money you want to transfer:")
                        money_to_transfer = int(input())
                        balance = get_balance(conn, logged_number)
                        if money_to_transfer <= balance:
                            transfer_money(conn, money_to_transfer, input_card, logged_number)
                        else:
                            print("Not enough money!")
                    else:
                        print("Such a card does not exist.")
                else:
                    print("You can't transfer money to the same account!")
            else:
                print("Probably you made a mistake in the card number. Please try again!")
        elif operation ==4 and is_logged is True:
            delete_account(conn, logged_number)
            print("The account has been closed!")
            is_logged = False
            logged_number = 0
        elif operation == 5 and is_logged is True:
            print("You have successfully logged out!")
            is_logged = False
        elif operation == 0:
            is_running = False
            print("Bye!")


if __name__ == '__main__':
    main()
