import flet as ft
import sqlite3
import os
from datetime import datetime

def get_db_path():
    # المسار الدائم الخاص بالتطبيق على نظام أندرويد لضمان عدم مسح البيانات
    app_data = os.getenv("FLET_APP_STORAGE_DATA_DIR")
    if not app_data:
        app_data = os.path.expanduser("~")
    
    os.makedirs(app_data, exist_ok=True)
    return os.path.join(app_data, "debts_permanent.db")

def init_db(db_path):
    conn = sqlite3.connect(db_path)
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
    db_path = get_db_path()
    init_db(db_path)

    page.title = "دفتر الديون"
    page.theme_mode = ft.ThemeMode.DARK
    page.rtl = True
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 15

    editing_id = {"value": None}

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
    total_debts_card = ft.Text("إجمالي الديون المتبقية: 0.00 دج", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.RED_400)

    def calculate_remaining(e=None):
        try:
            t = float(str(total_field.value or "0").replace(",", "."))
            p = float(str(paid_field.value or "0").replace(",", "."))
            rem = t - p
            remaining_text.value = f"الباقي: {rem:,.2f} دج"
        except Exception:
            remaining_text.value = "الباقي: 0.00 دج"
        page.update()

    total_field.on_change = calculate_remaining
    paid_field.on_change = calculate_remaining

    list_container = ft.Column(spacing=10)

    def load_data():
        list_container.controls.clear()
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT id, date, creditor, total_amount, paid_amount, remaining FROM debts ORDER BY id DESC")
        rows = c.fetchall()

        sum_remaining = 0.0
        for r in rows:
            rec_id, r_date, r_cred, r_tot, r_paid, r_rem = r
            sum_remaining += float(r_rem or 0)

            def make_delete(current_id):
                return lambda e: delete_debt(current_id)

            def make_edit(item_id, d, cred, tot, pd):
                return lambda e: start_edit(item_id, d, cred, tot, pd)

            card = ft.Card(
                elevation=2,
                content=ft.Container(
                    padding=10,
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"{r_cred}", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_200),
                            ft.Text(f"{r_date}", size=12, color=ft.colors.GREY_400),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([
                            ft.Text(f"الكلي: {r_tot:,.0f} دج", size=13),
                            ft.Text(f"المدفوع: {r_paid:,.0f} دج", size=13, color=ft.colors.GREEN_300),
                            ft.Text(f"الباقي: {r_rem:,.0f} دج", size=13, weight=ft.FontWeight.BOLD, color=ft.colors.RED_300),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([
                            ft.TextButton("تعديل", icon=ft.icons.EDIT, on_click=make_edit(rec_id, r_date, r_cred, r_tot, r_paid)),
                            ft.TextButton("حذف", icon=ft.icons.DELETE, icon_color=ft.colors.RED_400, on_click=make_delete(rec_id)),
                        ], alignment=ft.MainAxisAlignment.END)
                    ])
                )
            )
            list_container.controls.append(card)

        total_debts_card.value = f"إجمالي الديون المتبقية: {sum_remaining:,.2f} دج"
        conn.close()
        page.update()

    def start_edit(item_id, d, cred, tot, pd):
        editing_id["value"] = item_id
        date_field.value = str(d)
        creditor_field.value = str(cred)
        total_field.value = str(tot)
        paid_field.value = str(pd)
        calculate_remaining()
        submit_btn.text = "تحديث الدين"
        submit_btn.icon = ft.icons.CHECK
        cancel_btn.visible = True
        page.update()

    def cancel_edit(e):
        reset_form()

    def reset_form():
        editing_id["value"] = None
        creditor_field.value = ""
        total_field.value = ""
        paid_field.value = ""
        date_field.value = datetime.now().strftime("%Y-%m-%d")
        remaining_text.value = "الباقي: 0.00 دج"
        submit_btn.text = "إضافة الدين"
        submit_btn.icon = ft.icons.ADD
        cancel_btn.visible = False
        page.update()

    def delete_debt(rec_id):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("DELETE FROM debts WHERE id = ?", (rec_id,))
        conn.commit()
        conn.close()
        if editing_id["value"] == rec_id:
            reset_form()
        load_data()

    def save_debt(e):
        if not creditor_field.value or not total_field.value:
            page.snack_bar = ft.SnackBar(ft.Text("يرجى ملء اسم الدائن والمبلغ الكلي"), open=True)
            page.update()
            return

        try:
            t = float(str(total_field.value).replace(",", "."))
            p = float(str(paid_field.value or "0").replace(",", "."))
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("يرجى إدخال أرقام صحيحة للمبالغ"), open=True)
            page.update()
            return

        rem = t - p
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        if editing_id["value"] is None:
            c.execute("""INSERT INTO debts (date, creditor, total_amount, paid_amount, remaining)
                         VALUES (?, ?, ?, ?, ?)""",
                      (date_field.value, creditor_field.value.strip(), t, p, rem))
        else:
            c.execute("""UPDATE debts SET date=?, creditor=?, total_amount=?, paid_amount=?, remaining=?
                         WHERE id=?""",
                      (date_field.value, creditor_field.value.strip(), t, p, rem, editing_id["value"]))

        conn.commit()
        conn.close()
        reset_form()
        load_data()

    submit_btn = ft.ElevatedButton("إضافة الدين", icon=ft.icons.ADD, on_click=save_debt, expand=True)
    cancel_btn = ft.OutlinedButton("إلغاء", icon=ft.icons.CLOSE, on_click=cancel_edit, visible=False)

    header = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.icons.ACCOUNT_BALANCE_WALLET, color=ft.colors.BLUE_400),
                ft.Text("دفتر الديون", size=22, weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Text("بشير جودي", size=12, color=ft.colors.GREY_400, text_align=ft.TextAlign.CENTER)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.padding.only(bottom=10)
    )

    page.add(
        header,
        ft.Card(
            content=ft.Container(
                padding=12,
                content=ft.Column([
                    date_field,
                    creditor_field,
                    total_field,
                    paid_field,
                    ft.Container(content=remaining_text, alignment=ft.alignment.center),
                    ft.Row([submit_btn, cancel_btn], spacing=10)
                ], spacing=10)
            )
        ),
        ft.Container(content=total_debts_card, alignment=ft.alignment.center, padding=10),
        ft.Text("قائمة الديون المسجلة:", size=16, weight=ft.FontWeight.BOLD),
        list_container
    )

    load_data()

ft.app(target=main)
