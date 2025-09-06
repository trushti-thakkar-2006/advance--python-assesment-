import sqlite3
import re
from tkinter import *
from tkinter import messagebox, simpledialog
import csv

# =======================
# DATABASE SETUP
# =======================
conn = sqlite3.connect('repairmate.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    model TEXT,
    serial TEXT UNIQUE,
    FOREIGN KEY(customer_id) REFERENCES customers(id)
);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS repairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER,
    technician TEXT,
    issue TEXT,
    status TEXT,
    cost REAL,
    FOREIGN KEY(device_id) REFERENCES devices(id)
);
''')

conn.commit()

# =======================
# CLASSES
# =======================

class Customer:
    def __init__(self, name, email):
        self.name = name
        self.email = email

    def save(self):
        try:
            cursor.execute('INSERT INTO customers(name, email) VALUES (?, ?)', (self.name, self.email))
            conn.commit()
            print("Customer saved!")
        except sqlite3.IntegrityError as e:
            print(f"Error: {e}")


class Device:
    def __init__(self, customer_id, model, serial):
        self.customer_id = customer_id
        self.model = model
        self.serial = serial

    def save(self):
        try:
            cursor.execute('INSERT INTO devices(customer_id, model, serial) VALUES (?, ?, ?)', (self.customer_id, self.model, self.serial))
            conn.commit()
            print("Device saved!")
        except sqlite3.IntegrityError as e:
            print(f"Error: {e}")

class Repair:
    def __init__(self, device_id, technician, issue, status="Pending", cost=0.0):
        self.device_id = device_id
        self.technician = technician
        self.issue = issue
        self.status = status
        self.cost = cost

    def save(self):
        cursor.execute('INSERT INTO repairs(device_id, technician, issue, status, cost) VALUES (?, ?, ?, ?, ?)',
                       (self.device_id, self.technician, self.issue, self.status, self.cost))
        conn.commit()
        print("Repair job saved!")


# =======================
# GUI IMPLEMENTATION
# =======================

class RepairMateApp:
    def __init__(self, master):
        self.master = master
        self.master.title("RepairMate - TechRepair Hub")
        self.role = None
        self.login_screen()

    def login_screen(self):
        self.clear_widgets()
        Label(self.master, text="Login as:").pack(pady=10)
        Button(self.master, text="Admin", command=self.admin_interface).pack(pady=5)
        Button(self.master, text="Technician", command=self.tech_interface).pack(pady=5)

    def admin_interface(self):
        self.role = "Admin"
        self.main_interface()

    def tech_interface(self):
        self.role = "Technician"
        self.main_interface()

    def main_interface(self):
        self.clear_widgets()

        Label(self.master, text=f"Logged in as: {self.role}").pack(pady=5)

        Button(self.master, text="Add Customer", command=self.add_customer).pack(pady=5)
        Button(self.master, text="Add Device", command=self.add_device).pack(pady=5)
        Button(self.master, text="Add Repair Order", command=self.add_repair).pack(pady=5)
        Button(self.master, text="View Repairs (Search)", command=self.search_repairs).pack(pady=5)
        Button(self.master, text="Generate Invoice", command=self.generate_invoice).pack(pady=5)
        Button(self.master, text="Logout", command=self.login_screen).pack(pady=10)

    def clear_widgets(self):
        for widget in self.master.winfo_children():
            widget.destroy()

    def add_customer(self):
        try:
            name = simpledialog.askstring("Input", "Enter customer name:")
            email = simpledialog.askstring("Input", "Enter customer email:")
            if not name or not email:
                raise ValueError("Name and Email required")
            customer = Customer(name, email)
            customer.save()
            messagebox.showinfo("Success", "Customer saved.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def add_device(self):
        try:
            email = simpledialog.askstring("Input", "Enter customer email for device linking:")
            if not email:
                raise ValueError("Email required")
            cursor.execute('SELECT id FROM customers WHERE email=?', (email,))
            customer = cursor.fetchone()
            if not customer:
                raise ValueError("Customer not found")
            customer_id = customer[0]
            model = simpledialog.askstring("Input", "Enter device model:")
            serial = simpledialog.askstring("Input", "Enter device serial number:")
            if not model or not serial:
                raise ValueError("Model and Serial required")
            device = Device(customer_id, model, serial)
            device.save()
            messagebox.showinfo("Success", "Device saved.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def add_repair(self):
        try:
            if self.role not in ['Admin', 'Technician']:
                raise PermissionError("Access denied")
            serial = simpledialog.askstring("Input", "Enter device serial number:")
            cursor.execute('SELECT id FROM devices WHERE serial=?', (serial,))
            device = cursor.fetchone()
            if not device:
                raise ValueError("Device not found")
            device_id = device[0]
            technician = simpledialog.askstring("Input", "Enter technician name:")
            issue = simpledialog.askstring("Input", "Enter repair issue:")
            if not technician or not issue:
                raise ValueError("Technician and issue required")
            repair = Repair(device_id, technician, issue)
            repair.save()
            messagebox.showinfo("Success", "Repair order saved.")
        except PermissionError as pe:
            messagebox.showerror("Permission Error", str(pe))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def search_repairs(self):
        try:
            pattern = simpledialog.askstring("Search", "Enter status or device model pattern:")
            if not pattern:
                raise ValueError("Pattern required")

            # Search device models and repair statuses
            cursor.execute('''
            SELECT r.id, d.model, r.issue, r.status, r.technician
            FROM repairs r JOIN devices d ON r.device_id = d.id
            ''')
            results = cursor.fetchall()

            matched = []
            for rec in results:
                combined = f"{rec[1]} {rec[3]}"
                if re.search(pattern, combined, re.IGNORECASE):
                    matched.append(rec)

            if matched:
                result_text = "\n".join([f"ID:{r[0]}, Model:{r[1]}, Issue:{r[2]}, Status:{r[3]}, Technician:{r[4]}" for r in matched])
                messagebox.showinfo("Search Results", result_text)
            else:
                messagebox.showinfo("Search Results", "No matches found.")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def generate_invoice(self):
        try:
            serial = simpledialog.askstring("Input", "Enter device serial number for invoice:")
            cursor.execute('''
            SELECT r.id, r.cost, r.status
            FROM repairs r JOIN devices d ON r.device_id = d.id WHERE d.serial = ?
            ''', (serial,))
            repair_jobs = cursor.fetchall()
            if not repair_jobs:
                raise ValueError("No repair jobs found")

            total_cost = 0.0
            for _, cost, status in repair_jobs:
                if cost is None:
                    cost = 0.0
                total_cost += cost
            tax = total_cost * 0.07  # 7% tax
            grand_total = total_cost + tax

            # Save invoice to CSV
            filename = f"invoice_{serial}.csv"
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['RepairID', 'Cost', 'Status'])
                for repair in repair_jobs:
                    writer.writerow(repair)
                writer.writerow([])
                writer.writerow(['Total', total_cost])
                writer.writerow(['Tax (7%)', tax])
                writer.writerow(['Grand Total', grand_total])

            messagebox.showinfo("Invoice Generated", f"Invoice saved as {filename}")

        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = Tk()
    app = RepairMateApp(root)
    root.geometry('300x400')
    root.mainloop()

