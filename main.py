import flet as ft
import sqlite3
import threading
import time
from datetime import datetime

DB_NAME = "debts_data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creditor_name TEXT NOT NULL,
            creditor_type TEXT NOT NULL,
            debt_date TEXT NOT NULL,
            total_amount REAL NOT NULL,
            paid_amount REAL DEFAULT 0,
            remaining_amount REAL NOT NULL,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()

def main(page: ft.Page):
    page.title = "سجل إدارة الديون الشخصية"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.rtl = True
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    init_db()

    # --- شريط الترويسة الاحترافي ---
    app_title_row = ft.Row([
        ft.Icon(ft.icons.ACCOUNT_BALANCE_WALLET_ROUNDED, size=38, color=ft.colors.BLUE_800),
        ft.Column([
            ft.Text("سجل إدارة المديونيات", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
            ft.Text("نظام تتبع الديون والمدفوعات والمتبقيات", size=12, color=ft.colors.GREY_700),
        ], spacing=2)
    ], alignment=ft.MainAxisAlignment.START)

    # عنصر الساعة والاسم (بشير جودي)
    clock_text = ft.Text(size=12, color=ft.colors.BLUE_900, weight=ft.FontWeight.W_500)
    date_text = ft.Text(size=12, color=ft.colors.GREY_700)
    
    user_badge = ft.Container(
        content=ft.Row([
            ft.Icon(ft.icons.PERSON_PIN_ROUNDED, color=ft.colors.BLUE_800, size=28),
            ft.Column([
                ft.Text("بشير جودي", size=15, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
                ft.Row([clock_text, ft.Text("•", color=ft.colors.GREY_400), date_text], spacing=5),
            ], spacing=2)
        ], alignment=ft.MainAxisAlignment.END),
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        border_radius=8,
        bgcolor=ft.colors.BLUE_50,
        border=ft.border.all(1, ft.colors.BLUE_100),
    )

    header_row = ft.Row([app_title_row, user_badge], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    # تشغيل الساعة والوقت المحدث حياً
    def update_clock():
        while True:
            try:
                now = datetime.now()
                clock_text.value = now.strftime("%H:%M:%S")
                date_text.value = now.strftime("%Y-%m-%d")
                page.update()
                time.sleep(1)
            except Exception:
                break

    threading.Thread(target=update_clock, daemon=True).start()

    # --- عناصر الإدخال ---
    name_input = ft.TextField(label="اسم الدائن", expand=True)
    type_dropdown = ft.Dropdown(
        label="الصفة / النوع",
        options=[
            ft.dropdown.Option("شخص"),
            ft.dropdown.Option("سوبيرات"),
            ft.dropdown.Option("محل تجاري"),
            ft.dropdown.Option("شركة"),
            ft.dropdown.Option("أخرى"),
        ],
        value="سوبيرات",
        width=170,
    )
    date_input = ft.TextField(
        label="تاريخ الدين",
        value=datetime.today().strftime("%Y-%m-%d"),
        width=140,
    )

    # المبالغ وخانة الباقي الحية التلقائية
    total_input = ft.TextField(label="المبلغ الكلي (دج)", keyboard_type=ft.KeyboardType.NUMBER, width=150)
    paid_input = ft.TextField(label="المدفوع / تخليص (دج)", value="0", keyboard_type=ft.KeyboardType.NUMBER, width=150)
    
    # خانة الباقي التلقائية المحمية (Read-only)
    remaining_input = ft.TextField(
        label="الدين الباقي (دج)",
        value="0.00",
        read_only=True,
        width=150,
        color=ft.colors.RED_700,
        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
    )

    notes_input = ft.TextField(label="ملاحظات وتفاصيل المعاملة", expand=True)

    # تحديث خانة الدين الباقي تلقائياً عند إدخال المبالغ
    def calc_remaining(e=None):
        try:
            total_val = float(total_input.value.strip()) if total_input.value.strip() else 0.0
            paid_val = float(paid_input.value.strip()) if paid_input.value.strip() else 0.0
            rem = total_val - paid_val
            remaining_input.value = f"{rem:,.2f}"
            remaining_input.color = ft.colors.GREEN_700 if rem <= 0 else ft.colors.RED_700
        except ValueError:
            remaining_input.value = "خطأ رقمي"
            remaining_input.color = ft.colors.ORANGE_800
        page.update()

    total_input.on_change = calc_remaining
    paid_input.on_change = calc_remaining

    records_column = ft.Column(spacing=10)
    summary_text = ft.Text(size=15, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900)

    # جلب السجلات وعرضها
    def load_debts():
        records_column.controls.clear()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id, creditor_name, creditor_type, debt_date, total_amount, paid_amount, remaining_amount, notes FROM debts ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()

        total_debts_sum = 0
        total_remaining_sum = 0

        for row in rows:
            d_id, name, c_type, d_date, total, paid, remaining, notes = row
            total_debts_sum += total
            total_remaining_sum += remaining

            status_color = ft.colors.GREEN_700 if remaining <= 0 else ft.colors.RED_600
            status_text = "خالص" if remaining <= 0 else "متبقي عليك"

            def make_delete_handler(record_id):
                return lambda e: delete_debt(record_id)

            card = ft.Card(
                elevation=2,
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Row([
                            ft.Row([
                                ft.Icon(ft.icons.STORE if c_type in ["سوبيرات", "محل تجاري"] else ft.icons.PERSON, color=ft.colors.BLUE_700),
                                ft.Text(f"{name} ({c_type})", size=17, weight=ft.FontWeight.BOLD),
                            ], spacing=8),
                            ft.Row([
                                ft.Text(f"التاريخ: {d_date}", size=13, color=ft.colors.GREY_700),
                                ft.IconButton(
                                    icon=ft.icons.DELETE_OUTLINE,
                                    icon_color=ft.colors.RED_400,
                                    tooltip="حذف السجل",
                                    on_click=make_delete_handler(d_id)
                                )
                            ])
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=1),
                        ft.Row([
                            ft.Text(f"المبلغ الأصلي: {total:,.2f} دج", weight=ft.FontWeight.W_500),
                            ft.Text(f"المسدد (التخليص): {paid:,.2f} دج", color=ft.colors.BLUE_GREY_700),
                            ft.Container(
                                content=ft.Text(f"الباقي: {remaining:,.2f} دج ({status_text})", weight=ft.FontWeight.BOLD, color=status_color),
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=6,
                                bgcolor=ft.colors.GREEN_50 if remaining <= 0 else ft.colors.RED_50,
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(f"ملاحظة: {notes}", size=12, italic=True, color=ft.colors.GREY_800) if notes else ft.Container(),
                    ], spacing=8)
                )
            )
            records_column.controls.append(card)

        summary_text.value = f"إجمالي الديون المسجلة: {total_debts_sum:,.2f} دج   |   إجمالي الدين المتبقي عليك حالياً: {total_remaining_sum:,.2f} دج"
        page.update()

    def delete_debt(record_id):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM debts WHERE id = ?", (record_id,))
        conn.commit()
        conn.close()
        load_debts()

    def add_debt_clicked(e):
        if not name_input.value.strip() or not total_input.value.strip():
            page.snack_bar = ft.SnackBar(ft.Text("يرجى ملء اسم الدائن والمبلغ الكلي على الأقل!"))
            page.snack_bar.open = True
            page.update()
            return

        try:
            total = float(total_input.value.strip())
            paid = float(paid_input.value.strip() or 0)
            remaining = total - paid

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO debts (creditor_name, creditor_type, debt_date, total_amount, paid_amount, remaining_amount, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name_input.value.strip(), type_dropdown.value, date_input.value.strip(), total, paid, remaining, notes_input.value.strip()))
            conn.commit()
            conn.close()

            name_input.value = ""
            total_input.value = ""
            paid_input.value = "0"
            remaining_input.value = "0.00"
            notes_input.value = ""

            page.snack_bar = ft.SnackBar(ft.Text("تمت إضافة المعاملة بنجاح!"), bgcolor=ft.colors.GREEN_700)
            page.snack_bar.open = True
            load_debts()
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("تأكد من إدخال الأرقام بطريقة صحيحة!"), bgcolor=ft.colors.RED_700)
            page.snack_bar.open = True
            page.update()

    page.add(
        header_row,
        ft.Divider(),
        ft.Container(
            content=summary_text,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor=ft.colors.BLUE_50,
            border_radius=8,
            border=ft.border.all(1, ft.colors.BLUE_200)
        ),
        ft.Card(
            elevation=3,
            content=ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("إضافة دين جديد / معاملة تسديد", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
                    ft.Row([name_input, type_dropdown, date_input]),
                    ft.Row([total_input, paid_input, remaining_input, notes_input]),
                    ft.Row([
                        ft.ElevatedButton(
                            "حفظ وتسجيل المعاملة",
                            icon=ft.icons.SAVE_ROUNDED,
                            on_click=add_debt_clicked,
                            bgcolor=ft.colors.BLUE_800,
                            color=ft.colors.WHITE,
                            style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=20, vertical=12))
                        )
                    ], alignment=ft.MainAxisAlignment.END)
                ], spacing=15)
            )
        ),
        ft.Divider(),
        ft.Text("قائمة سجلات المديونية الحالية:", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
        records_column,
    )

    load_debts()

if __name__ == "__main__":
    ft.app(target=main)