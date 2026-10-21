import flet as ft
from datetime import datetime
import json
import os

# تحديد مسار التخزين الدائم لنظام أندرويد
def get_storage_file():
    # 1. المسار الرسمي لتخزين تطبيقات أندرويد الداخلية
    android_path = "/data/data/dz.djoudi.debtsapp/files"
    if os.path.exists("/data/data/dz.djoudi.debtsapp"):
        try:
            os.makedirs(android_path, exist_ok=True)
            return os.path.join(android_path, "debts_store.json")
        except Exception:
            pass

    # 2. مسار احتياطي موثوق عبر FLET_APP_STORAGE_DATA_DIR إن وجد
    env_dir = os.environ.get("FLET_APP_STORAGE_DATA_DIR")
    if env_dir:
        try:
            os.makedirs(env_dir, exist_ok=True)
            return os.path.join(env_dir, "debts_store.json")
        except Exception:
            pass

    # 3. مسار المستندات المحلي
    home_dir = os.path.expanduser("~")
    return os.path.join(home_dir, "debts_store.json")

DATA_FILE = get_storage_file()

def read_debts():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def write_debts(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def main(page: ft.Page):
    page.title = "دفتر الديون"
    page.theme_mode = ft.ThemeMode.DARK
    page.rtl = True
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 15

    debts_data = read_debts()
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
        sum_remaining = 0.0

        for r in debts_data:
            rec_id = r.get("id")
            r_date = r.get("date", "")
            r_cred = r.get("creditor", "")
            r_tot = float(r.get("total_amount", 0))
            r_paid = float(r.get("paid_amount", 0))
            r_rem = float(r.get("remaining", 0))

            sum_remaining += r_rem

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
        nonlocal debts_data
        debts_data = [item for item in debts_data if item.get("id") != rec_id]
        write_debts(debts_data)
        if editing_id["value"] == rec_id:
            reset_form()
        load_data()

    def save_debt(e):
        nonlocal debts_data
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

        if editing_id["value"] is None:
            new_id = int(datetime.now().timestamp() * 1000)
            new_item = {
                "id": new_id,
                "date": date_field.value,
                "creditor": creditor_field.value.strip(),
                "total_amount": t,
                "paid_amount": p,
                "remaining": rem
            }
            debts_data.insert(0, new_item)
        else:
            for item in debts_data:
                if item.get("id") == editing_id["value"]:
                    item["date"] = date_field.value
                    item["creditor"] = creditor_field.value.strip()
                    item["total_amount"] = t
                    item["paid_amount"] = p
                    item["remaining"] = rem
                    break

        write_debts(debts_data)
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
