import tkinter
import webbrowser
from tkinter import Canvas, Entry, Button, Tk, StringVar, PhotoImage, OptionMenu, Label, Menu, Toplevel
from tkinter import messagebox
from datetime import date
import os
import csv
import pandas as pd
from bs4 import BeautifulSoup
import requests
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


today = date.today()


def my_popup(e):
    my_menu.tk_popup(e.x_root, e.y_root)


def paste():
    text = window.clipboard_get()
    link_entry.insert(0, text)


def scrappy(url):
    # Date of the tracking
    today_date = today.strftime("%m/%d/%Y")

    response = requests.get(url=url)
    soup = BeautifulSoup(response.text, 'lxml')

    # Price of the product
    price = soup.find(class_="product-new-price").get_text()
    price_without_currency = price.split()
    price_as_float = float(price_without_currency[0])
    if price_as_float < 9:
        price_as_float *= 1000
    else:
        price_as_float /= 100

    # Name of the product
    title = soup.find(class_="page-title").get_text().split("\n")
    title_final = (title[1]).lstrip(" ")

    data_dict = {
        "Product": [title_final],
        "Price": [price_as_float],
        "Date": [today_date],
        "Link": [url],
    }

    data_dict2 = {
        "Product": title_final,
        "Price": price_as_float,
        "Date": today_date,
        "Link": url,
    }
    # Check if the file exist and append data to it, else we create it
    if not os.path.isfile('Emag.csv'):
        df = pd.DataFrame(data_dict)
        df.to_csv("Emag.csv", index=False)
        print("CSV file created.")
    else:
        with open('Emag.csv', "r") as f:
            reader = csv.reader(f)
            for header in reader:
                break
        with open('Emag.csv', "a", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writerow(data_dict2)
            print("Data added to CSV file.")

    return data_dict2


def uniq_items():
    df = pd.read_csv('Emag.csv')
    items = df.Product.unique()
    return items


def high_low_price(item):
    df = pd.read_csv('Emag.csv')
    choice = df[df.Product == item]
    high_id = choice["Price"].idxmax()
    high_price = df.loc[high_id]['Price']
    high_date = df.loc[high_id]['Date']
    lowest_id = choice["Price"].idxmin()
    lowest_price = df.loc[lowest_id]['Price']
    lowest_date = df.loc[lowest_id]['Date']
    final_high_low = [[high_price, high_date], [lowest_price, lowest_date]]
    return final_high_low


def live_price(item):
    df = pd.read_csv('Emag.csv')
    choice = df[df.Product == item]
    link = choice['Link'].iloc[0]
    data = scrappy(link)
    price_now = data['Price']
    date_now = data['Date']
    link = data['Link']
    final_curent = [price_now, date_now, link]
    return final_curent


def get_url():
    url = link_entry.get()
    scrappy(url)


def clear():
    link_entry.delete(0, 'end')


# Check low, high and current price and displays it.
def check():
    choice = variable.get()
    high_low = high_low_price(choice)
    current = live_price(choice)
    link = current[2]
    msg = messagebox.askyesno(title="Price info",
                              message=f"Product name: {choice}\n"
                                      f"Highest price: {high_low[0][0]} on {high_low[0][1]}\n"
                                      f"Current price: {current[0]} today on {current[1]}\n"
                                      f"Lowest price: {high_low[1][0]} on {high_low[1][1]}\n"
                                      f"Do you want to open in browser?")
    if msg:
        webbrowser.open(url=link)


# Go through all products from the data base and update the data.
def update_db():
    df = pd.read_csv('Emag.csv')
    all_links = df.Link.unique()
    for item in all_links:
        scrappy(item)
    messagebox.showinfo(title="Database update", message="The data base was updated successfully.")


def resize_db():
    df = pd.read_csv('Emag.csv')
    clean = df.drop_duplicates(subset=['Product', 'Date'])
    df = pd.DataFrame(clean)
    df.to_csv("Emag.csv", index=False)


def graphic():
    choice = variable.get()
    df = pd.read_csv('Emag.csv')
    df_with_choice = df.loc[df['Product'] == choice]
    final_df = df_with_choice[["Price", "Date"]]
    return final_df


def open_new_window():
    new_window = Toplevel(window)
    new_window.title("Evolution of the price")
    new_window.geometry("900x900")
    resize_db()
    df = graphic()
    df.reset_index(drop=True, inplace=True)
    df.Date = pd.to_datetime(df.Date).dt.strftime('%Y-%b-%d')
    sorted_df = df.sort_values(by='Date')
    figure = plt.Figure(figsize=(9, 9))
    ax = figure.add_subplot(111)
    line = FigureCanvasTkAgg(figure, new_window)
    line.get_tk_widget().pack(side=tkinter.LEFT, fill=tkinter.BOTH)
    sorted_df = sorted_df[['Date', 'Price']].groupby('Date').sum()
    sorted_df.plot(kind='line', legend=True, ax=ax, color='r', marker='o', fontsize=10)
    ax.set_title(f"Price evolution: {variable.get()}")


if not os.path.isfile('Emag.csv'):
    OPTIONS = ["No items"]
else:
    OPTIONS = uniq_items()


# Option to remove a product from the data base and to delete all data related to it.
def delete_choice():
    choice = variable.get()
    data = pd.read_csv('Emag.csv', index_col=0)
    data = data.drop(choice, axis=0)
    msg = messagebox.askyesno(title="Remove product",
                              message=f"You are sure you want to delete all the date about:\n {choice}?")
    if msg:
        df = pd.DataFrame(data)
        df.to_csv("Emag.csv")


# GUI
window = Tk()
window.title("Emag Price Tracker")
window.config(padx=20, pady=20)
variable = StringVar(window)
try:
    variable.set(OPTIONS[0])
except IndexError:
    OPTIONS = ["Data base empty"]
    variable.set(OPTIONS)
window.grid_columnconfigure(1, weight=1)
window.grid_rowconfigure(1, weight=1)

my_menu = Menu(window, tearoff=False)
my_menu.add_command(label='Paste', command=paste)

window.bind("<Button-3>", my_popup)


# Function that constantly updates the optionmenu to display new added products to the data base.
def refresh():
    variable.set('')
    item_list['menu'].delete(0, 'end')

    options = uniq_items()
    for option in options:
        item_list['menu'].add_command(label=option, command=tkinter._setit(variable, option))
    try:
        variable.set(options[0])
    except IndexError:
        options = ["Data base empty"]
        variable.set(options)


# Canvas
canvas = Canvas(height=170, width=400)
logo_img = PhotoImage(file='logo1.png')
canvas.create_image(220, 100, image=logo_img)
canvas.grid(row=0, column=1)

# Label
link_label = Label(text="Link:")
link_label.grid(row=1, column=0)
items_label = Label(text="Items:")
items_label.grid(row=2, column=0)

# Entry
link_entry = Entry(width=45)
link_entry.grid(row=1, column=1, sticky='w, e')
item_list = OptionMenu(window, variable, *OPTIONS)
item_list.grid(row=2, column=1)

# Button
add_button = Button(text="Add link", width=6, command=lambda: [get_url(), clear(), refresh()])
add_button.grid(row=1, column=3)
check_button = Button(text="Check", width=6, command=check)
check_button.grid(row=2, column=3)
delete_button = Button(text="Delete", width=6, command=lambda: [delete_choice(), refresh()])
delete_button.grid(row=3, column=3)
update_button = Button(text='Update Database', width=16, command=update_db)
update_button.grid(row=3, column=1)
graphic_button = Button(text="Graphic", command=open_new_window)
graphic_button.grid(row=3, column=0)

window.mainloop()
