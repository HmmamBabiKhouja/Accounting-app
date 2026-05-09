import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import ttfonts
from reportlab.pdfbase import pdfmetrics

# ---------- تحميل خط عربي ----------
pdfmetrics.registerFont(ttfonts.TTFont('Arabic', 'Cairo-Regular.ttf'))

# ---------- Database ----------
conn = sqlite3.connect("arabic_accounting.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    amount REAL,
    description TEXT,
    date TEXT
)
""")

conn.commit()

invoice_counter = 1

# ---------- Functions ----------
def add_client():
    name = client_entry.get()
    if name == "":
        return
    try:
        cursor.execute("INSERT INTO clients (name) VALUES (?)", (name,))
        conn.commit()
        update_clients()
        client_entry.delete(0, tk.END)
    except:
        messagebox.showerror("خطأ", "العميل موجود بالفعل")

def update_clients():
    cursor.execute("SELECT name FROM clients")
    clients = [row[0] for row in cursor.fetchall()]
    client_combo["values"] = clients

def get_client_id(name):
    cursor.execute("SELECT id FROM clients WHERE name=?", (name,))
    return cursor.fetchone()[0]

def add_transaction():
    try:
        client = client_combo.get()
        amount = float(amount_entry.get())
        desc = desc_entry.get()
        date = datetime.now().strftime("%Y-%m-%d")

        if client == "":
            messagebox.showwarning("تنبيه", "اختر العميل")
            return

        client_id = get_client_id(client)

        cursor.execute("""
        INSERT INTO transactions (client_id, amount, description, date)
        VALUES (?, ?, ?, ?)
        """, (client_id, amount, desc, date))

        conn.commit()
        update_table()

    except:
        messagebox.showerror("خطأ", "بيانات غير صحيحة")

def update_table():
    for row in tree.get_children():
        tree.delete(row)

    cursor.execute("""
    SELECT t.id, c.name, t.amount, t.description, t.date
    FROM transactions t
    JOIN clients c ON t.client_id = c.id
    """)

    for row in cursor.fetchall():
        tree.insert("", "end", values=row)

# ---------- فاتورة عربية ----------
def generate_invoice():
    global invoice_counter

    selected = tree.selection()
    if not selected:
        messagebox.showwarning("تنبيه", "اختر عملية")
        return

    item = tree.item(selected[0])["values"]
    _, client, amount, desc, date = item

    vat_rate = 0.14
    vat = amount * vat_rate
    total = amount + vat

    file_name = f"فاتورة_{invoice_counter}.pdf"
    invoice_counter += 1

    doc = SimpleDocTemplate(file_name)
    styles = getSampleStyleSheet()

    arabic_style = ParagraphStyle(
        name='ArabicStyle',
        fontName='Arabic',
        fontSize=12,
        alignment=2  # محاذاة لليمين
    )

    title_style = ParagraphStyle(
        name='TitleArabic',
        fontName='Arabic',
        fontSize=16,
        alignment=2
    )

    content = []

    # الشركة
    content.append(Paragraph("شركة محمود خوجة للمحاسبة القانونية", title_style))
    content.append(Spacer(1, 10))

    # بيانات
    content.append(Paragraph(f"رقم الفاتورة: {invoice_counter}", arabic_style))
    content.append(Paragraph(f"التاريخ: {date}", arabic_style))
    content.append(Paragraph(f"العميل: {client}", arabic_style))
    content.append(Spacer(1, 10))

    # جدول
    data = [
        ["الخدمة", "المبلغ"],
        [desc, f"{amount:.2f}"],
        ["ضريبة (14%)", f"{vat:.2f}"],
        ["الإجمالي", f"{total:.2f}"]
    ]

    table = Table(data)
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
    ]))

    content.append(table)
    content.append(Spacer(1, 15))

    content.append(Paragraph("شكرًا لتعاملكم معنا", arabic_style))

    doc.build(content)

    messagebox.showinfo("تم", f"تم إنشاء الفاتورة: {file_name}")

# ---------- UI ----------
root = tk.Tk()
root.title("نظام المحاسبة - شركة محمود خوجة")
root.geometry("800x600")

# عميل
tk.Label(root, text="اسم العميل").pack()
client_entry = tk.Entry(root)
client_entry.pack()

tk.Button(root, text="إضافة عميل", command=add_client).pack()

# العمليات
frame = tk.Frame(root)
frame.pack(pady=10)

tk.Label(frame, text="العميل").grid(row=0, column=0)
client_combo = ttk.Combobox(frame)
client_combo.grid(row=0, column=1)

tk.Label(frame, text="المبلغ").grid(row=1, column=0)
amount_entry = tk.Entry(frame)
amount_entry.grid(row=1, column=1)

tk.Label(frame, text="الوصف").grid(row=2, column=0)
desc_entry = tk.Entry(frame)
desc_entry.grid(row=2, column=1)

tk.Button(frame, text="إضافة عملية", command=add_transaction).grid(row=3, columnspan=2)

# جدول
columns = ("ID", "العميل", "المبلغ", "الوصف", "التاريخ")
tree = ttk.Treeview(root, columns=columns, show="headings")

for col in columns:
    tree.heading(col, text=col)

tree.pack(fill="both", expand=True)

# فاتورة
tk.Button(root, text="إنشاء فاتورة PDF", command=generate_invoice).pack(pady=10)

# init
update_clients()
update_table()

root.mainloop()