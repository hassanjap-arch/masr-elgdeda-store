import csv
import os
import urllib.parse
import urllib.request
import flet as ft


# ==========================================
# 1. جلب البيانات تلقائياً من Google Sheets
# ==========================================
def fetch_products_from_sheets():
    sheet_url = "https://docs.google.com/spreadsheets/d/1OWDkHSYrdtAiDGddzoAwv3smt78D0Y12Gc7vPs7QDys/gviz/tq?tqx=out:csv"

    paper_products = []
    medical_products = []

    try:
        req = urllib.request.Request(
            sheet_url, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            lines = [line.decode("utf-8") for line in response.readlines()]
            reader = csv.reader(lines)

            header = next(reader, None)

            for row in reader:
                if len(row) >= 3 and row[0].strip():
                    try:
                        paper_products.append(
                            {
                                "name": row[0].strip(),
                                "price": float(row[1].strip()),
                                "unit": row[2].strip(),
                                "category": "paper",
                            }
                        )
                    except (ValueError, IndexError):
                        pass

                if len(row) >= 6 and row[3].strip():
                    try:
                        medical_products.append(
                            {
                                "name": row[3].strip(),
                                "price": float(row[4].strip()),
                                "unit": row[5].strip(),
                                "category": "medical",
                            }
                        )
                    except (ValueError, IndexError):
                        pass
    except Exception as e:
        print(f"تنبيه: تعذر جلب البيانات من شيت جوجل: {e}")

    return paper_products, medical_products


def main(page: ft.Page):
    page.title = "بوابة مشتريات - شركة مصر الجديدة"
    page.window_icon = "assets/icon.png"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.rtl = True
    page.padding = 8
    page.bgcolor = "#f8fafc"
    page.scroll = None

    page.theme = ft.Theme(
        scrollbar_theme=ft.ScrollbarTheme(
            thumb_color="#1e293b",
            track_color="#cbd5e1",
            track_visibility=True,
            thumb_visibility=True,
            thickness=8,
            radius=4,
        )
    )

    paper_products, medical_products = fetch_products_from_sheets()

    cart = {}
    saved_client_info = {"pharmacy": "", "phone": ""}

    cart_items_container = ft.Column(spacing=5)
    cart_empty_text = ft.Text(
        "السلة فارغة حالياً. قم بطلب الأصناف من الأقسام بالأعلى.",
        color="#64748b",
        size=13,
        text_align=ft.TextAlign.CENTER,
    )

    top_bar_total_text = ft.Text(
        "الإجمالي: 0 ج.م",
        size=13,
        weight=ft.FontWeight.BOLD,
        color="#b91c1c",
    )
    top_bar_count_text = ft.Text("(0 أصناف)", size=11, color="#475569")

    total_price_text = ft.Text(
        "إجمالي الطلب: 0 ج.م",
        size=14,
        weight=ft.FontWeight.BOLD,
        color="#b91c1c",
    )

    # أزرار التنقل
    nav_paper_btn = ft.ElevatedButton(
        "📋 الورقيات ➔",
        style=ft.ButtonStyle(bgcolor="#1e3a8a", color="#ffffff", padding=8),
    )
    nav_medical_btn = ft.ElevatedButton(
        "🩺 المستلزمات ➔",
        style=ft.ButtonStyle(bgcolor="#9f1239", color="#ffffff", padding=8),
    )
    nav_home_btn = ft.ElevatedButton(
        "🏠 الرئيسية",
        style=ft.ButtonStyle(bgcolor="#64748b", color="#ffffff", padding=8),
    )

    def change_qty(name, delta):
        if name in cart:
            cart[name]["qty"] += delta
            if cart[name]["qty"] <= 0:
                del cart[name]
        update_cart_ui()

    def remove_item(name):
        if name in cart:
            del cart[name]
        update_cart_ui()

    def clear_cart(e):
        cart.clear()
        update_cart_ui()
        page.snack_bar = ft.SnackBar(
            ft.Text("تم تفريغ السلة بنجاح، يمكنك بدء طلب جديد."), open=True
        )
        page.update()

    new_order_btn = ft.ElevatedButton(
        "طلب جديد",
        icon=ft.Icons.REFRESH,
        on_click=clear_cart,
        style=ft.ButtonStyle(bgcolor="#ef4444", color="#ffffff", padding=5),
        visible=False,
    )

    def update_nav_badges():
        paper_count = sum(
            1 for item in cart.values() if item.get("category") == "paper"
        )
        medical_count = sum(
            1 for item in cart.values() if item.get("category") == "medical"
        )

        nav_paper_btn.text = (
            f"📋 الورقيات ({paper_count})"
            if paper_count > 0
            else "📋 الورقيات ➔"
        )
        nav_medical_btn.text = (
            f"🩺 المستلزمات ({medical_count})"
            if medical_count > 0
            else "🩺 المستلزمات ➔"
        )

    def update_cart_ui():
        cart_items_container.controls.clear()

        if not cart:
            cart_items_container.controls.append(cart_empty_text)
            total_price_text.value = "إجمالي الطلب: 0 ج.م"
            top_bar_total_text.value = "الإجمالي: 0 ج.م"
            top_bar_count_text.value = "(0 أصناف)"
            new_order_btn.visible = False
        else:
            total_sum = 0
            total_items_count = len(cart)
            for name, details in cart.items():
                item_total = details["price"] * details["qty"]
                total_sum += item_total

                item_row = ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        f"• {name}",
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                        color="#0f172a",
                                        expand=True,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE_OUTLINE,
                                        icon_color="#ef4444",
                                        icon_size=20,
                                        on_click=lambda e, n=name: remove_item(n),
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        f"السعر: {details['price']} ج.م",
                                        size=12,
                                        color="#64748b",
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.IconButton(
                                                icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
                                                icon_color="#b91c1c",
                                                icon_size=20,
                                                on_click=lambda e, n=name: change_qty(
                                                    n, -1
                                                ),
                                            ),
                                            ft.Text(
                                                f"{details['qty']} {details['unit']}",
                                                size=13,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                            ft.IconButton(
                                                icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                                                icon_color="#15803d",
                                                icon_size=20,
                                                on_click=lambda e, n=name: change_qty(
                                                    n, 1
                                                ),
                                            ),
                                        ],
                                        spacing=0,
                                    ),
                                    ft.Text(
                                        f"= {item_total} ج.م",
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                        color="#b91c1c",
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                        ],
                        spacing=2,
                    ),
                    padding=8,
                    bgcolor="#f1f5f9",
                    border_radius=8,
                )
                cart_items_container.controls.append(item_row)

            total_price_text.value = f"إجمالي الطلب: {total_sum} ج.م"
            top_bar_total_text.value = f"الإجمالي: {total_sum} ج.م"
            top_bar_count_text.value = f"({total_items_count} أصناف)"
            new_order_btn.visible = True

        update_nav_badges()
        page.update()

    def open_checkout_dialog(e):
        if not cart:
            page.snack_bar = ft.SnackBar(
                ft.Text("السلة فارغة! قم بطلب بعض الأصناف أولاً."), open=True
            )
            page.update()
            return

        target_whatsapp = "201095969276"

        pharmacy_name_input = ft.TextField(
            label="اسم الصيدلية",
            value=saved_client_info["pharmacy"],
            border_color="#1e3a8a",
            autofocus=True,
        )
        phone_number_input = ft.TextField(
            label="رقم الهاتف للتواصل",
            value=saved_client_info["phone"],
            border_color="#1e3a8a",
            keyboard_type=ft.KeyboardType.PHONE,
        )

        invoice_items_list = ft.ListView(
            spacing=4,
            height=220,
            expand=False,
        )

        total_sum = 0
        for name, details in cart.items():
            item_total = details["price"] * details["qty"]
            total_sum += item_total
            invoice_items_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text(
                                f"• {name}",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                expand=True,
                            ),
                            ft.Text(
                                f"{details['qty']} {details['unit']}", size=12
                            ),
                            ft.Text(
                                f"{item_total} ج.م",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color="#b91c1c",
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=2,
                )
            )

        invoice_preview_box = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "📋 معاينة الفاتورة قبل الإرسال:",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color="#1e3a8a",
                    ),
                    ft.Divider(height=1),
                    invoice_items_list,
                    ft.Divider(height=1),
                    ft.Row(
                        controls=[
                            ft.Text(
                                "الإجمالي الكلي:",
                                weight=ft.FontWeight.BOLD,
                                size=13,
                            ),
                            ft.Text(
                                f"{total_sum} ج.م",
                                weight=ft.FontWeight.BOLD,
                                size=14,
                                color="#b91c1c",
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=5,
            ),
            padding=8,
            bgcolor="#f8fafc",
            border=ft.Border.all(1, "#cbd5e1"),
            border_radius=8,
        )

        send_btn = ft.ElevatedButton(
            "إرسال الطلب عبر الواتساب",
            url=f"https://wa.me/{target_whatsapp}",
            style=ft.ButtonStyle(bgcolor="#9f1239", color="#ffffff"),
        )

        def generate_whatsapp_link(ev=None):
            pharmacy_name = pharmacy_name_input.value.strip()
            client_phone = phone_number_input.value.strip()

            saved_client_info["pharmacy"] = pharmacy_name
            saved_client_info["phone"] = client_phone

            message_lines = [
                "*طلب توريد جديد - شركة مصر الجديدة*\n",
                f"🏥 *الصيدلية:* {pharmacy_name if pharmacy_name else 'غير محدد'}",
                f"📞 *هاتف التواصل:* {client_phone if client_phone else 'غير محدد'}\n",
                "----------------------------",
                "*الأصناف المطلوبة:*",
            ]

            t_sum = 0
            for name, details in cart.items():
                item_total = details["price"] * details["qty"]
                t_sum += item_total
                message_lines.append(
                    f"• {name}\n   الكمية: {details['qty']} {details['unit']} | الإجمالي: {item_total} ج.م"
                )

            message_lines.append("----------------------------")
            message_lines.append(f"*إجمالي فاتورة الطلب:* {t_sum} ج.م")

            full_message = "\n".join(message_lines)
            encoded_message = urllib.parse.quote(full_message)

            send_btn.url = (
                f"https://wa.me/{target_whatsapp}?text={encoded_message}"
            )

        pharmacy_name_input.on_change = generate_whatsapp_link
        phone_number_input.on_change = generate_whatsapp_link

        generate_whatsapp_link(None)

        def close_dialog(ev):
            if hasattr(dialog, "open"):
                dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            title=ft.Text(
                "مراجعة وإرسال الطلب", weight=ft.FontWeight.BOLD, size=16
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        pharmacy_name_input,
                        phone_number_input,
                        invoice_preview_box,
                    ],
                    tight=True,
                    spacing=8,
                ),
                width=350,
            ),
            actions=[
                ft.TextButton("إلغاء", on_click=close_dialog),
                send_btn,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        if hasattr(page, "open"):
            page.open(dialog)
        else:
            page.overlay.append(dialog)
            dialog.open = True
            page.update()

    def add_to_cart(product):
        name = product["name"]
        if name in cart:
            cart[name]["qty"] += 1
        else:
            cart[name] = {
                "price": product["price"],
                "unit": product["unit"],
                "qty": 1,
                "category": product.get("category", ""),
            }
        update_cart_ui()

    def build_product_card(product, color_code):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        product["name"],
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color="#1e293b",
                    ),
                    ft.Row(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        f"{product['price']} ج.م",
                                        size=13,
                                        color="#b91c1c",
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Text(
                                        f"/ {product['unit']}",
                                        size=12,
                                        color="#64748b",
                                    ),
                                ],
                                spacing=4,
                            ),
                            ft.ElevatedButton(
                                "+ إضافة",
                                on_click=lambda e, p=product: add_to_cart(p),
                                style=ft.ButtonStyle(
                                    bgcolor=color_code,
                                    color="#ffffff",
                                    padding=6,
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=6,
            ),
            padding=10,
            bgcolor="#ffffff",
            border_radius=8,
            border=ft.Border.all(1, "#e2e8f0"),
        )

    def build_cart_widget():
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        "🛒 سلة المشتريات",
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color="#0f172a",
                                    ),
                                    total_price_text,
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Row(
                                controls=[
                                    ft.ElevatedButton(
                                        "تأكيد وإرسال عبر الواتساب",
                                        icon=ft.Icons.SEND,
                                        on_click=open_checkout_dialog,
                                        style=ft.ButtonStyle(
                                            bgcolor="#9f1239",
                                            color="#ffffff",
                                            padding=8,
                                        ),
                                        expand=True,
                                    ),
                                    new_order_btn,
                                ],
                                spacing=8,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Divider(height=1),
                    cart_items_container,
                ]
            ),
            padding=10,
            bgcolor="#ffffff",
            border_radius=10,
            border=ft.Border.all(1, "#cbd5e1"),
        )

    header_section = ft.Container(
        content=ft.Row(
            controls=[
                ft.Image(
                    src="/logo.png",
                    height=65,
                    fit="contain",
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        padding=4,
        bgcolor="#ffffff",
        border_radius=8,
    )

    main_content = ft.Column(
        spacing=8,
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )

    def build_sticky_top_bar(nav_buttons):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(controls=nav_buttons, spacing=5, expand=True),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.Icons.SHOPPING_BAG_OUTLINED,
                                    color="#b91c1c",
                                    size=18,
                                ),
                                ft.Column(
                                    controls=[
                                        top_bar_total_text,
                                        top_bar_count_text,
                                    ],
                                    spacing=0,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                            ],
                            spacing=4,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        bgcolor="#f1f5f9",
                        padding=6,
                        border_radius=6,
                        border=ft.Border.all(1, "#cbd5e1"),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor="#ffffff",
            padding=6,
            border_radius=8,
            shadow=ft.BoxShadow(
                blur_radius=4, color="#10000000", offset=ft.Offset(0, 2)
            ),
        )

    # ==========================================
    # عرض الأقسام والصفحات
    # ==========================================
    def show_home(e=None):
        nav_paper_btn.on_click = show_paper
        nav_medical_btn.on_click = show_medical

        main_content.controls = [
            ft.ListView(
                controls=[
                    header_section,
                    ft.Text(
                        "مرحباً بكم! اختار القسم للبدء في الطلب:",
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color="#1e293b",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Column(
                        controls=[
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Image(
                                            src="/paper.png",
                                            height=140,
                                            fit="cover",
                                            border_radius=8,
                                        ),
                                        ft.Text(
                                            "📋 قسم الورقيات والعناية",
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                            color="#1e3a8a",
                                        ),
                                        ft.ElevatedButton(
                                            "دخول القسم ➔",
                                            on_click=show_paper,
                                            style=ft.ButtonStyle(
                                                bgcolor="#1e3a8a",
                                                color="#ffffff",
                                            ),
                                        ),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=8,
                                ),
                                padding=12,
                                bgcolor="#ffffff",
                                border_radius=12,
                                border=ft.Border.all(1, "#e2e8f0"),
                            ),
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Image(
                                            src="/medical.png",
                                            height=140,
                                            fit="cover",
                                            border_radius=8,
                                        ),
                                        ft.Text(
                                            "🩺 قسم المستلزمات والأجهزة الطبية",
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                            color="#9f1239",
                                        ),
                                        ft.ElevatedButton(
                                            "دخول القسم ➔",
                                            on_click=show_medical,
                                            style=ft.ButtonStyle(
                                                bgcolor="#9f1239",
                                                color="#ffffff",
                                            ),
                                        ),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=8,
                                ),
                                padding=12,
                                bgcolor="#ffffff",
                                border_radius=12,
                                border=ft.Border.all(1, "#e2e8f0"),
                            ),
                        ],
                        spacing=12,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                    ft.Container(height=10),
                    build_cart_widget(),
                ],
                spacing=12,
                expand=True,
            )
        ]
        page.update()
        update_cart_ui()

    def show_paper(e=None):
        nav_home_btn.on_click = show_home
        nav_medical_btn.on_click = show_medical
        nav_btns = [nav_home_btn, nav_medical_btn]

        products_list_view = ft.ListView(spacing=8, expand=True)

        def filter_paper(ev):
            query = ev.control.value.strip().lower() if ev else ""
            filtered = [
                p for p in paper_products if query in p["name"].lower()
            ]
            products_list_view.controls = (
                [build_product_card(p, "#1e3a8a") for p in filtered]
                if filtered
                else [ft.Text("لا توجد نتائج مطابقة للبحث.", color="#64748b")]
            )
            if ev:
                products_list_view.update()

        search_field = ft.TextField(
            hint_text="🔍 ابحث عن صنف ورقيات...",
            on_change=filter_paper,
            border_radius=8,
            border_color="#cbd5e1",
            content_padding=10,
            autofocus=False,
        )

        filter_paper(None)

        main_content.controls = [
            header_section,
            build_sticky_top_bar(nav_btns),
            ft.Text(
                "📋 قسم الورقيات",
                size=17,
                weight=ft.FontWeight.BOLD,
                color="#1e3a8a",
            ),
            search_field,
            products_list_view,
        ]
        page.update()
        update_cart_ui()

    def show_medical(e=None):
        nav_home_btn.on_click = show_home
        nav_paper_btn.on_click = show_paper
        nav_btns = [nav_home_btn, nav_paper_btn]

        products_list_view = ft.ListView(spacing=8, expand=True)

        def filter_medical(ev):
            query = ev.control.value.strip().lower() if ev else ""
            filtered = [
                p for p in medical_products if query in p["name"].lower()
            ]
            products_list_view.controls = (
                [build_product_card(p, "#9f1239") for p in filtered]
                if filtered
                else [ft.Text("لا توجد نتائج مطابقة للبحث.", color="#64748b")]
            )
            if ev:
                products_list_view.update()

        search_field = ft.TextField(
            hint_text="🔍 ابحث عن صنف مستلزمات...",
            on_change=filter_medical,
            border_radius=8,
            border_color="#cbd5e1",
            content_padding=10,
            autofocus=False,
        )

        filter_medical(None)

        main_content.controls = [
            header_section,
            build_sticky_top_bar(nav_btns),
            ft.Text(
                "🩺 قسم المستلزمات الطبية",
                size=17,
                weight=ft.FontWeight.BOLD,
                color="#9f1239",
            ),
            search_field,
            products_list_view,
        ]
        page.update()
        update_cart_ui()

    page.add(main_content)
    show_home()


# ==========================================
# تشغيل التطبيق وتحديد المنفذ تلقائياً للسيرفر
# ==========================================
port = int(os.environ.get("PORT", 8080))

ft.app(
    target=main,
    assets_dir="assets",
    view=ft.AppView.WEB_BROWSER,
    port=port,
    host="0.0.0.0",
)
