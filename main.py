import csv, os, urllib.parse, urllib.request
import flet as ft

def fetch_products_from_sheets():
    sheet_url = "https://docs.google.com/spreadsheets/d/1OWDkHSYrdtAiDGddzoAwv3smt78D0Y12Gc7vPs7QDys/gviz/tq?tqx=out:csv"
    paper_products, medical_products = [], []
    try:
        req = urllib.request.Request(sheet_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            lines = [line.decode("utf-8") for line in response.readlines()]
            reader = csv.reader(lines)
            next(reader, None)
            for row in reader:
                if len(row) >= 3 and row[0].strip():
                    try: paper_products.append({"name": row[0].strip(), "price": float(row[1].strip()), "unit": row[2].strip(), "category": "paper"})
                    except: pass
                if len(row) >= 6 and row[3].strip():
                    try: medical_products.append({"name": row[3].strip(), "price": float(row[4].strip()), "unit": row[5].strip(), "category": "medical"})
                    except: pass
    except Exception as e: print(f"تنبيه: {e}")
    return paper_products, medical_products

def main(page: ft.Page):
    page.title = "بوابة مشتريات - مصر الجديدة"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.rtl = True
    page.padding = 0
    page.bgcolor = "#f8fafc"
    page.scroll = ft.ScrollMode.ALWAYS
    page.theme = ft.Theme(scrollbar_theme=ft.ScrollbarTheme(thumb_visibility=True, track_visibility=True, thickness=12, radius=6, thumb_color="#1e3a8a", track_color="#e2e8f0"))

    paper_products, medical_products = fetch_products_from_sheets()
    cart, saved_client_info = {}, {"pharmacy": "", "phone": ""}
    current_section = {"name": "home", "qp": "", "qm": "", "show_invoice": False}

    cart_items_container = ft.Column(spacing=5)
    top_bar_total_text = ft.Text("الإجمالي: 0 ج.م", size=13, weight=ft.FontWeight.BOLD, color="#b91c1c")
    top_bar_count_text = ft.Text("(0 أصناف)", size=11, color="#475569")
    total_price_text = ft.Text("إجمالي الطلب: 0 ج.م", size=14, weight=ft.FontWeight.BOLD, color="#b91c1c")
    nav_home_btn = ft.ElevatedButton("الرئيسية", on_click=lambda e: show_home(), style=ft.ButtonStyle(bgcolor="#64748b", color="#ffffff", padding=8))
    new_order_btn = ft.ElevatedButton("طلب جديد", icon=ft.Icons.REFRESH, style=ft.ButtonStyle(bgcolor="#ef4444", color="#ffffff", padding=5), visible=False)

    paper_list_view = ft.Column(spacing=6)
    medical_list_view = ft.Column(spacing=6)

    invoice_dropdown_list = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO)
    invoice_dropdown_container = ft.Container(content=ft.Column(controls=[ft.Text("فاتورتك الحالية:", size=14, weight=ft.FontWeight.BOLD, color="#1e3a8a"), ft.Divider(height=1), invoice_dropdown_list], spacing=6), padding=10, bgcolor="#ffffff", border_radius=10, border=ft.Border.all(2, "#1e3a8a"), width=400, visible=False)

    def toggle_invoice_dropdown(e=None):
        if not cart:
            page.snack_bar = ft.SnackBar(ft.Text("السلة فارغة!"), open=True); page.update(); return
        current_section["show_invoice"] = not current_section["show_invoice"]
        build_invoice_dropdown()
        invoice_dropdown_container.visible = current_section["show_invoice"]
        page.update()

    def build_invoice_dropdown():
        invoice_dropdown_list.controls.clear()
        total_sum = 0
        for name, details in cart.items():
            item_total = details["price"] * details["qty"]; total_sum += item_total
            invoice_dropdown_list.controls.append(ft.Container(content=ft.Row(controls=[ft.Text(f"• {name} ({details['qty']} {details['unit']})", size=12, weight=ft.FontWeight.BOLD, expand=True), ft.Text(f"{item_total} ج.م", size=12, weight=ft.FontWeight.BOLD, color="#b91c1c")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=6, bgcolor="#f8fafc", border_radius=6, border=ft.Border.all(1, "#e2e8f0")))
        invoice_dropdown_list.controls.append(ft.Divider(height=1))
        invoice_dropdown_list.controls.append(ft.Row(controls=[ft.Text("الإجمالي:", weight=ft.FontWeight.BOLD, size=13), ft.Text(f"{total_sum} ج.م", weight=ft.FontWeight.BOLD, color="#b91c1c", size=14)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
        invoice_dropdown_list.controls.append(ft.Row(controls=[ft.ElevatedButton("إخفاء", on_click=toggle_invoice_dropdown, style=ft.ButtonStyle(bgcolor="#64748b", color="#ffffff")), ft.ElevatedButton("تأكيد وإرسال", icon=ft.Icons.SEND, on_click=lambda e: show_checkout_page(), style=ft.ButtonStyle(bgcolor="#9f1239", color="#ffffff"), expand=True)], spacing=8))

    def clear_cart(e):
        cart.clear(); current_section["show_invoice"]=False; invoice_dropdown_container.visible=False; update_cart_ui()

    new_order_btn.on_click = clear_cart

    def change_qty(name, delta):
        if name in cart:
            cart[name]["qty"] += delta
            if cart[name]["qty"] <= 0: del cart[name]
        update_cart_ui()

    def remove_item(name):
        if name in cart: del cart[name]; update_cart_ui()

    def show_checkout_page():
        if not cart: return
        current_section["name"]="checkout"
        invoice_dropdown_container.visible=False

        pharmacy_name_input = ft.TextField(label="اسم الصيدلية *", value=saved_client_info["pharmacy"], border_color="#1e3a8a", autofocus=True)
        phone_number_input = ft.TextField(label="رقم الهاتف *", value=saved_client_info["phone"], border_color="#1e3a8a", keyboard_type=ft.KeyboardType.PHONE)

        invoice_items_list = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO, height=200)
        total_sum=0
        for name, details in cart.items():
            item_total = details["price"]*details["qty"]; total_sum+=item_total
            invoice_items_list.controls.append(ft.Row(controls=[ft.Text(f"• {name}", size=12, weight=ft.FontWeight.BOLD, expand=True), ft.Text(f"{details['qty']} {details['unit']}", size=12), ft.Text(f"{item_total} ج.م", size=12, weight=ft.FontWeight.BOLD, color="#b91c1c")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))

        total_text = ft.Text(f"الإجمالي: {total_sum} ج.م", size=15, weight=ft.FontWeight.BOLD, color="#b91c1c")
        send_btn = ft.ElevatedButton("إرسال عبر الواتساب", icon=ft.Icons.SEND, style=ft.ButtonStyle(bgcolor="#25D366", color="#ffffff", padding=12), height=45, width=400)

        def update_link(e=None):
            saved_client_info["pharmacy"]=pharmacy_name_input.value.strip()
            saved_client_info["phone"]=phone_number_input.value.strip()
            if not saved_client_info["pharmacy"] or not saved_client_info["phone"]:
                send_btn.bgcolor="#9ca3af"
                send_btn.text="اكتب اسم الصيدلية والهاتف أولاً"
                send_btn.url=None
            else:
                send_btn.bgcolor="#25D366"
                send_btn.text="إرسال عبر الواتساب"
                msg = [f"*طلب جديد - مصر الجديدة*", f"الصيدلية: {saved_client_info['pharmacy']}", f"الهاتف: {saved_client_info['phone']}", "", "الأصناف:"]
                t_sum=0
                for name, details in cart.items():
                    item_total=details["price"]*details["qty"]; t_sum+=item_total; msg.append(f"• {name} - {details['qty']} {details['unit']} = {item_total} ج.م")
                msg.append(f"\nالإجمالي: {t_sum} ج.م")
                send_btn.url = f"https://wa.me/201095969276?text={urllib.parse.quote(chr(10).join(msg))}"
            page.update()

        pharmacy_name_input.on_change=update_link
        phone_number_input.on_change=update_link
        update_link()

        header_section_local = ft.Container(content=ft.Row(controls=[ft.Image(src="/logo.png", height=50, fit="contain")], alignment=ft.MainAxisAlignment.CENTER), padding=4, bgcolor="#ffffff", border_radius=8, width=400)

        main_content.controls=[
            header_section_local,
            ft.Container(content=ft.Row(controls=[ft.ElevatedButton("رجوع", on_click=lambda e: show_home(), style=ft.ButtonStyle(bgcolor="#64748b", color="#ffffff")), ft.Text("تأكيد الطلب", size=16, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), width=400),
            ft.Container(content=ft.Column(controls=[ft.Text("بيانات الصيدلية:", weight=ft.FontWeight.BOLD, color="#1e3a8a"), pharmacy_name_input, phone_number_input], spacing=8), padding=12, bgcolor="#ffffff", border_radius=10, border=ft.Border.all(1, "#cbd5e1"), width=400),
            ft.Container(content=ft.Column(controls=[ft.Text("معاينة الفاتورة:", weight=ft.FontWeight.BOLD, color="#1e3a8a"), ft.Divider(height=1), invoice_items_list, ft.Divider(height=1), total_text], spacing=6), padding=12, bgcolor="#f8fafc", border=ft.Border.all(1, "#cbd5e1"), border_radius=10, width=400),
            send_btn
        ]
        page.update()

    def add_to_cart(product, qty=1):
        name = product["name"]
        if name in cart: cart[name]["qty"] += qty
        else: cart[name] = {"price": product["price"], "unit": product["unit"], "qty": qty, "category": product.get("category", "")}
        if cart[name]["qty"] <= 0: del cart[name]
        update_cart_ui()

    def set_cart_qty(product, qty):
        try: qty = int(qty)
        except: qty = 0
        name = product["name"]
        if qty <= 0:
            if name in cart: del cart[name]
        else:
            if name in cart: cart[name]["qty"] = qty
            else: cart[name] = {"price": product["price"], "unit": product["unit"], "qty": qty, "category": product.get("category", "")}
        update_cart_ui()

    def build_product_card(product, color_code):
        current_qty = cart[product["name"]]["qty"] if product["name"] in cart else 0
        is_added = current_qty > 0
        qty_field = ft.TextField(value=str(current_qty), width=55, height=32, text_size=13, content_padding=4, text_align=ft.TextAlign.CENTER, keyboard_type=ft.KeyboardType.NUMBER, border_radius=6, border_color="#16a34a" if is_added else "#cbd5e1")
        def on_qty_change(e): set_cart_qty(product, e.control.value)
        qty_field.on_change = on_qty_change
        def on_add_click(e): add_to_cart(product, 1)
        def on_delete_click(e):
            if product["name"] in cart: del cart[product["name"]]; update_cart_ui()
        add_btn_bg = "#16a34a" if is_added else color_code
        add_btn_text = f"+ ({current_qty})" if is_added else "+ إضافة"
        return ft.Container(content=ft.Column(controls=[ft.Text(product["name"], size=13, weight=ft.FontWeight.BOLD, color="#1e293b"), ft.Row(controls=[ft.Text(f"{product['price']} ج.م / {product['unit']}", size=11, color="#b91c1c", weight=ft.FontWeight.BOLD), ft.Row(controls=[ft.Text("العدد:", size=10, color="#475569"), qty_field, ft.ElevatedButton(add_btn_text, on_click=on_add_click, style=ft.ButtonStyle(bgcolor=add_btn_bg, color="#ffffff", padding=5), height=30), ft.ElevatedButton("حذف", on_click=on_delete_click, style=ft.ButtonStyle(bgcolor="#ef4444", color="#ffffff", padding=5), height=30, visible=is_added)], spacing=3)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)], spacing=5), padding=8, bgcolor="#f0fdf4" if is_added else "#ffffff", border_radius=8, border=ft.Border.all(2 if is_added else 1, "#16a34a" if is_added else "#e2e8f0"))

    def build_cart_widget():
        return ft.Container(content=ft.Column(controls=[ft.Row(controls=[ft.Text("سلة المشتريات", size=14, weight=ft.FontWeight.BOLD), total_price_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.Row(controls=[ft.ElevatedButton("تأكيد وإرسال", icon=ft.Icons.SEND, on_click=lambda e: show_checkout_page(), style=ft.ButtonStyle(bgcolor="#9f1239", color="#ffffff", padding=8), expand=True), new_order_btn], spacing=8), ft.Divider(height=1), cart_items_container]), padding=10, bgcolor="#ffffff", border_radius=10, border=ft.Border.all(1, "#cbd5e1"))

    def filter_paper_logic(query):
        current_section["qp"]=query
        filtered=[p for p in paper_products if query in p["name"].lower()] if query else paper_products
        paper_list_view.controls=[build_product_card(p, "#1e3a8a") for p in filtered] if filtered else [ft.Text("لا توجد نتائج.", color="#64748b")]

    def filter_medical_logic(query):
        current_section["qm"]=query
        filtered=[p for p in medical_products if query in p["name"].lower()] if query else medical_products
        medical_list_view.controls=[build_product_card(p, "#9f1239") for p in filtered] if filtered else [ft.Text("لا توجد نتائج.", color="#64748b")]

    def update_cart_ui():
        cart_items_container.controls.clear()
        if not cart:
            cart_items_container.controls.append(ft.Text("السلة فارغة حالياً.", color="#64748b", size=13, text_align=ft.TextAlign.CENTER))
            total_price_text.value="إجمالي الطلب: 0 ج.م"; top_bar_total_text.value="الإجمالي: 0 ج.م"; top_bar_count_text.value="(0 أصناف)"; new_order_btn.visible=False
            invoice_dropdown_container.visible = False; current_section["show_invoice"]=False
        else:
            total_sum=0
            for name, details in cart.items():
                item_total=details["price"]*details["qty"]; total_sum+=item_total
                cart_items_container.controls.append(ft.Container(content=ft.Column(controls=[ft.Row(controls=[ft.Text(f"• {name}", size=13, weight=ft.FontWeight.BOLD, expand=True), ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="#ef4444", icon_size=20, on_click=lambda e, n=name: remove_item(n))], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.Row(controls=[ft.Text(f"{details['price']} ج.م", size=12, color="#64748b"), ft.Row(controls=[ft.IconButton(icon=ft.Icons.REMOVE_CIRCLE_OUTLINE, icon_color="#b91c1c", icon_size=18, on_click=lambda e, n=name: change_qty(n, -1)), ft.Text(f"{details['qty']} {details['unit']}", size=13, weight=ft.FontWeight.BOLD), ft.IconButton(icon=ft.Icons.ADD_CIRCLE_OUTLINE, icon_color="#15803d", icon_size=18, on_click=lambda e, n=name: change_qty(n, 1))], spacing=0), ft.Text(f"= {item_total} ج.م", size=13, weight=ft.FontWeight.BOLD, color="#b91c1c")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)], spacing=2), padding=8, bgcolor="#f1f5f9", border_radius=8))
            total_price_text.value=f"إجمالي الطلب: {total_sum} ج.م"; top_bar_total_text.value=f"الإجمالي: {total_sum} ج.م"; top_bar_count_text.value=f"({len(cart)} أصناف)"; new_order_btn.visible=True
            if current_section["show_invoice"]: build_invoice_dropdown()
        if current_section["name"]=="paper": filter_paper_logic(current_section["qp"])
        elif current_section["name"]=="medical": filter_medical_logic(current_section["qm"])
        page.update()

    header_section = ft.Container(content=ft.Row(controls=[ft.Image(src="/logo.png", height=60, fit="contain")], alignment=ft.MainAxisAlignment.CENTER), padding=4, bgcolor="#ffffff", border_radius=8, width=400)
    main_content = ft.Column(spacing=10, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.ALWAYS)

    def build_sticky_top_bar():
        total_box = ft.Container(content=ft.Column(controls=[ft.Row(controls=[ft.Icon(ft.Icons.SHOPPING_BAG, color="#b91c1c", size=20), ft.Column(controls=[top_bar_total_text, top_bar_count_text], spacing=0, alignment=ft.CrossAxisAlignment.CENTER)], spacing=6, alignment=ft.MainAxisAlignment.CENTER), ft.ElevatedButton("اضغط لعرض الفاتورة", icon=ft.Icons.LIST, on_click=toggle_invoice_dropdown, style=ft.ButtonStyle(bgcolor="#1e3a8a", color="#ffffff", padding=8), height=32)], spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER), bgcolor="#eef2ff", padding=10, border_radius=10, border=ft.Border.all(1, "#1e3a8a"), width=220)
        return ft.Container(content=ft.Column(controls=[ft.Row(controls=[nav_home_btn, total_box], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER), invoice_dropdown_container], spacing=8), bgcolor="#ffffff", padding=8, border_radius=10, width=400)

    def show_home(e=None):
        current_section["name"]="home"; current_section["show_invoice"]=False; invoice_dropdown_container.visible=False
        home_cards = ft.Column(controls=[ft.Container(content=ft.Column(controls=[ft.Image(src="/paper.png", height=110, fit="cover", border_radius=8), ft.Text("قسم الورقيات والعناية", size=15, weight=ft.FontWeight.BOLD, color="#1e3a8a"), ft.ElevatedButton("دخول القسم", on_click=show_paper, style=ft.ButtonStyle(bgcolor="#1e3a8a", color="#ffffff"))], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6), padding=10, bgcolor="#ffffff", border_radius=12, border=ft.Border.all(1, "#e2e8f0"), width=400), ft.Container(content=ft.Column(controls=[ft.Image(src="/medical.png", height=110, fit="cover", border_radius=8), ft.Text("قسم المستلزمات والأجهزة الطبية", size=15, weight=ft.FontWeight.BOLD, color="#9f1239"), ft.ElevatedButton("دخول القسم", on_click=show_medical, style=ft.ButtonStyle(bgcolor="#9f1239", color="#ffffff"))], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6), padding=10, bgcolor="#ffffff", border_radius=12, border=ft.Border.all(1, "#e2e8f0"), width=400)], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        main_content.controls=[header_section, ft.Text("مرحباً بكم! اختار القسم للبدء:", size=14, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, color="#1e293b"), home_cards, ft.Container(content=build_cart_widget(), width=400)]
        page.update()

    def show_paper(e=None):
        current_section["name"]="paper"
        def on_search_change(ev): filter_paper_logic(ev.control.value.strip().lower()); page.update()
        search_field = ft.TextField(hint_text="ابحث ورقيات...", on_change=on_search_change, border_radius=8, border_color="#cbd5e1", content_padding=8, height=40, text_size=13, width=400)
        filter_paper_logic(current_section["qp"])
        main_content.controls=[header_section, build_sticky_top_bar(), ft.Container(content=ft.Text("قسم الورقيات", size=16, weight=ft.FontWeight.BOLD, color="#1e3a8a"), width=400), search_field, ft.Container(content=paper_list_view, width=400)]
        page.update()

    def show_medical(e=None):
        current_section["name"]="medical"
        def on_search_change(ev): filter_medical_logic(ev.control.value.strip().lower()); page.update()
        search_field = ft.TextField(hint_text="ابحث مستلزمات...", on_change=on_search_change, border_radius=8, border_color="#cbd5e1", content_padding=8, height=40, text_size=13, width=400)
        filter_medical_logic(current_section["qm"])
        main_content.controls=[header_section, build_sticky_top_bar(), ft.Container(content=ft.Text("قسم المستلزمات", size=16, weight=ft.FontWeight.BOLD, color="#9f1239"), width=400), search_field, ft.Container(content=medical_list_view, width=400)]
        page.update()

    # --- ده كود زرار الباك للموبايل واللابتوب ---
    def handle_back():
        if current_section["name"]!= "home":
            show_home()
            return True
        return False

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Escape":
            if handle_back():
                e.prevent_default = True

    def on_view_pop(e):
        handle_back()

    page.on_keyboard_event = on_keyboard
    try:
        page.on_view_pop = on_view_pop
    except:
        pass

    page.add(ft.Row(controls=[main_content], alignment=ft.MainAxisAlignment.CENTER, expand=True))
    show_home()

port = int(os.environ.get("PORT", 8080))
ft.app(target=main, assets_dir="assets", view=ft.AppView.WEB_BROWSER, port=port)
