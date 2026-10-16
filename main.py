import flet as ft
import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("debts.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS debts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    creditor TEXT,
                    total_amount REAL,
                    paid_amount REAL,
                    remaining REAL
                )""")
    conn.commit()
    conn.close()

def main(page: ft.Page):
    init_db()
    page.title = "إدارة الديون"
    page.theme_mode = ft.ThemeMode.DARK
    page.rtl = True
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 10

    # حقول الإدخال بتنسيق عمودي مناسب للهاتف
    date_field = ft.TextField(
        label="التاريخ", 
        value=datetime.now().strftime("%Y-%m-%d"), 
        dense=True,
        text_size=14
    )
    creditor_field = ft.TextField(
        label="اسم الدائن", 
        dense=True,
        text_size=14
    )
    total_field = ft.TextField(
        label="المبلغ الكلي (دج)", 
        keyboard_type=ft.KeyboardType.NUMBER, 
        dense=True,
        text_size=14
    )
    paid_field = ft.TextField(
        label="المبلغ المدفوع (دج)", 
        keyboard_type=ft.KeyboardType.NUMBER, 
        dense=True,
        text_size=14
    )

    remaining_text = ft.Text("الباقي: 0.00 دج", size=15, weight=ft.FontWeight.BOLD, color=ft.colors.ORANGE_400)
    total_debts_card = ft.Text("إجمالي الديون المتبقية: 0.00 دج", size=15, weight=ft.FontWeight.BOLD, color=ft.colors.RED_400)

    def calculate_remaining(e):
        try:
            total = float(total_field.value or 0)
            paid = float(paid_field.value or 0)
            remaining_text.value = f"الباقي: {total - paid:,.2f} دج"
        except ValueError:
            remaining_text.value = "الباقي: خطأ في الحساب"
        page.update()

    total_field.on_change = calculate_remaining
    paid_field.on_change = calculate_remaining

    # جدول يدعم السحب الأفقي عند صغر الشاشة
    table = ft.DataTable(
        column_spacing=12,
        heading_row_height=38,
        data_row_min_height=36,
        columns=[
            ft.DataColumn(ft.Text("الدائن", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("الكلي", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("المدفوع", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("المتبقي", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("حذف")),
        ],
        rows=[]
    )

    table_container = ft.Row([table], scroll=ft.ScrollMode.ALWAYS)

    def load_data():
        table.rows.clear()
        conn = sqlite3.connect("debts.db")
        c = conn.cursor()
        c.execute("SELECT id, date, creditor, total_amount, paid_amount, remaining FROM debts ORDER BY id DESC")
        rows = c.fetchall()
        
        sum_remaining = 0.0
        for r in rows:
            record_id, r_date, r_creditor, r_total, r_paid, r_rem = r
            sum_remaining += r_rem

            def delete_record(e, rec_id=record_id):
                del_conn = sqlite3.connect("debts.db")
                del_c = del_conn.cursor()
                del_c.execute("DELETE FROM debts WHERE id = ?", (rec_id,))
                del_conn.commit()
                del_conn.close()
                load_data()

            table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(r_creditor), size=13)),
                    ft.DataCell(ft.Text(f"{r_total:,.0f}", size=13)),
                    ft.DataCell(ft.Text(f"{r_paid:,.0f}", size=13)),
                    ft.DataCell(ft.Text(f"{r_rem:,.0f}", color=ft.colors.RED_300, weight=ft.FontWeight.BOLD, size=13)),
                    ft.DataCell(
                        ft.IconButton(
                            icon=ft.icons.DELETE_OUTLINE, 
                            icon_color=ft.colors.RED_400, 
                            icon_size=18,
                            on_click=delete_record
                        )
                    ),
                ])
            )
        total_debts_card.value = f"إجمالي الديون المتبقية: {sum_remaining:,.2f} دج"
        conn.close()
        page.update()

    def add_debt(e):
        if not creditor_field.value or not total_field.value:
            return
        total = float(total_field.value or 0)
        paid = float(paid_field.value or 0)
        rem = total - paid

        conn = sqlite3.connect("debts.db")
        c = conn.cursor()
        c.execute("INSERT INTO debts (date, creditor, total_amount, paid_amount, remaining) VALUES (?, ?, ?, ?, ?)",
                  (date_field.value, creditor_field.value, total, paid, rem))
        conn.commit()
        conn.close()

        creditor_field.value = ""
        total_field.value = ""
        paid_field.value = ""
        remaining_text.value = "الباقي: 0.00 دج"
        load_data()

    add_btn = ft.ElevatedButton("إضافة الدين", icon=ft.icons.ADD, on_click=add_debt, width=400)

    header = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.icons.ACCOUNT_BALANCE_WALLET, color=ft.colors.BLUE_400),
                ft.Text("دفتر الديون", size=20, weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Text("بشير جودي", size=12, color=ft.colors.GREY_400, text_align=ft.TextAlign.CENTER)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=10
    )

    page.add(
        ft.Column([
            header,
            ft.Card(content=ft.Container(content=ft.Column([date_field, creditor_field, total_field, paid_field, remaining_text, add_btn]), padding=12)),
            ft.Container(content=total_debts_card, alignment=ft.alignment.center, padding=5),
            ft.Text("سجل الديون:", size=15, weight=ft.FontWeight.BOLD),
            table_container
        ])
    )

    load_data()

ft.app(target=main)
