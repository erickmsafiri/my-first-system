import flet as ft
import json
import os
from datetime import datetime
import random
import time
from typing import List, Dict, Optional
import asyncio

# ======================
# CONSTANTS & CONFIGURATION
# ======================
REQUESTS_FILE = "food_requests.json"
DELIVERY_STATUSES = ["Preparing", "Cooking", "On the way", "Delivered"]
ADMIN_PASSWORD = "admin123"

COLORS = {
    "primary": "#6C63FF",
    "secondary": "#4D8BFF",
    "accent": "#FF6584",
    "background": "#F5F5F5",
    "text": "#2D3748",
    "success": "#48BB78",
    "warning": "#ED8936",
    "error": "#F56565",
    "dark_bg": "#1A202C",
    "dark_text": "#E2E8F0",
    "grey": "#E2E8F0",
    "white": "#FFFFFF",
    "transparent": "#00000000"
}

MENU_ITEMS = {
    "Wali Maharage": {
        "price": 2000,
        "description": "Wali na maharage",
        "ingredients": ["mchele", "maharage", "mchuzi"],
        "icon": "RICE_BOWL"
    },
    "Mihogo": {
        "price": 500,
        "description": "Mihogo ya kupika",
        "ingredients": ["mihogo", "maji", "chumvi"],
        "icon": "RESTAURANT"
    },
    "Chapati Maharage": {
        "price": 1500,
        "description": "Chapati na maharage",
        "ingredients": ["unga", "maharage", "mafuta"],
        "icon": "BREAD_SLICE"
    },
    "Chai Maziwa": {
        "price": 500,
        "description": "Chai yenye maziwa",
        "ingredients": ["maji", "chai", "sukari", "maziwa"],
        "icon": "COFFEE"
    },
    "Ugali Dagaa": {
        "price": 1500,
        "description": "Ugali na dagaa",
        "ingredients": ["unga wa mahindi", "dagaa", "mchuzi"],
        "icon": "KITCHEN"
    },
    "Supu": {
        "price": 1000,
        "description": "Supu ya nyama au mboga",
        "ingredients": ["maji", "nyama/mboga", "viungo"],
        "icon": "SOUP_KITCHEN"
    }
}

# ======================
# DATA MODELS
# ======================
class FoodRequest:
    def __init__(self, user_name: str, food_type: str, quantity: int = 1, special_requests: str = "", timestamp: Optional[str] = None):
        self.user_name = user_name
        self.food_type = food_type
        self.quantity = quantity
        self.special_requests = special_requests
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.completed = False
        self.delivery_status = "Preparing"
        self.order_id = f"ORD-{random.randint(1000, 9999)}"
        self.price = MENU_ITEMS.get(self.food_type, {}).get("price", 0) * self.quantity

    def to_dict(self) -> Dict:
        return {
            "user_name": self.user_name,
            "food_type": self.food_type,
            "quantity": self.quantity,
            "special_requests": self.special_requests,
            "timestamp": self.timestamp,
            "completed": self.completed,
            "delivery_status": self.delivery_status,
            "order_id": self.order_id,
            "price": self.price
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'FoodRequest':
        request = cls(
            data["user_name"],
            data["food_type"],
            data.get("quantity", 1),
            data.get("special_requests", "")
        )
        request.timestamp = data["timestamp"]
        request.completed = data["completed"]
        request.delivery_status = data.get("delivery_status", "Preparing")
        request.order_id = data.get("order_id", f"ORD-{random.randint(1000, 9999)}")
        request.price = data.get("price", 0)
        return request

# ======================
# CORE FUNCTIONALITY
# ======================
class DataManager:
    @staticmethod
    def save_requests(requests: List[FoodRequest]):
        with open(REQUESTS_FILE, "w") as f:
            json.dump([req.to_dict() for req in requests], f)

    @staticmethod
    def load_requests() -> List[FoodRequest]:
        if not os.path.exists(REQUESTS_FILE):
            return []
        try:
            with open(REQUESTS_FILE, "r") as f:
                data = json.load(f)
                return [FoodRequest.from_dict(item) for item in data]
        except (json.JSONDecodeError, FileNotFoundError):
            return []

# ======================
# VIEW COMPONENTS
# ======================
class ConfettiAnimation:
    def __init__(self):
        self.stack = ft.Stack()
        self.colors = [COLORS["primary"], COLORS["secondary"], COLORS["accent"], COLORS["success"]]
    
    def create(self, page: ft.Page):
        self.stack.controls.clear()
        for _ in range(50):
            self.stack.controls.append(
                ft.Container(
                    width=10,
                    height=10,
                    bgcolor=random.choice(self.colors),
                    left=random.randint(0, page.width),
                    top=random.randint(0, 100),
                    animate_position=ft.animation.Animation(1000, ft.AnimationCurve.EASE_OUT)
                )
            )
        page.update()
        for c in self.stack.controls:
            c.top = page.height
            c.opacity = 0
        page.update()
    
    def get_widget(self) -> ft.Stack:
        return self.stack

class OrderForm:
    def __init__(self, on_submit):
        self.user_name = ft.TextField(
            label="Your Name",
            width=300,
            border_color=COLORS["primary"],
            focused_border_color=COLORS["secondary"]
        )
        self.food_type = ft.Dropdown(
            label="Food Type",
            width=300,
            options=[ft.dropdown.Option(
                key=item,
                text=f"{item} (TZS {details['price']:,})"
            ) for item, details in MENU_ITEMS.items()],
            border_color=COLORS["primary"],
            focused_border_color=COLORS["secondary"]
        )
        self.quantity = ft.TextField(
            label="Quantity",
            width=300,
            value="1",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=COLORS["primary"],
            focused_border_color=COLORS["secondary"]
        )
        self.special_requests = ft.TextField(
            label="Special Requests",
            width=300,
            multiline=True,
            min_lines=1,
            max_lines=3
        )
        self.submit_btn = ft.ElevatedButton(
            "Submit Order",
            bgcolor=COLORS["primary"],
            color=COLORS["white"],
            width=300,
            height=50,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                elevation=5
            ),
            on_click=on_submit
        )
        self.status_text = ft.Text("", color=COLORS["success"])
    
    def get_view(self) -> ft.Column:
        return ft.Column([
            self.user_name,
            self.food_type,
            self.quantity,
            self.special_requests,
            self.submit_btn,
            self.status_text
        ], spacing=20)

# ======================
# AI ASSISTANT
# ======================
class ErickAI:
    def __init__(self, page: ft.Page, requests: List[FoodRequest]):
        self.page = page
        self.requests = requests
        self.conversation = ft.ListView(expand=True, spacing=10, auto_scroll=True)
        self.user_input = ft.TextField(
            label="Ask Erick AI anything about food...",
            multiline=True,
            min_lines=1,
            max_lines=3,
            on_submit=self.process_input
        )
        self.setup_ui()

    def setup_ui(self):
        self.send_button = ft.IconButton(
            icon="SEND",
            on_click=self.process_input,
            bgcolor=COLORS["primary"],
            icon_color=COLORS["white"]
        )

    def get_view(self) -> ft.Column:
        return ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Icon(name="ROCKET", color=COLORS["primary"], size=30),
                    ft.Text("Erick AI - Food Expert", size=18, weight=ft.FontWeight.BOLD),
                    ft.IconButton(
                        icon="INFO",
                        on_click=self.show_ai_capabilities,
                        icon_color=COLORS["primary"]
                    )
                ], alignment=ft.MainAxisAlignment.CENTER),
                padding=10,
                border=ft.border.all(1, COLORS["primary"])
            ),
            ft.Container(
                content=self.conversation,
                height=400,
                padding=10,
                border=ft.border.all(1, COLORS["grey"]),
                border_radius=5,
                bgcolor=COLORS["background"]
            ),
            ft.Row([self.user_input, self.send_button])
        ])

    def add_message(self, sender: str, message: str, is_ai: bool = False):
        self.conversation.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text(sender, weight=ft.FontWeight.BOLD, 
                           color=COLORS["primary"] if is_ai else COLORS["secondary"]),
                    ft.Text(message)
                ]),
                padding=10,
                bgcolor=f"{COLORS['primary']}10" if is_ai else f"{COLORS['secondary']}10",
                border_radius=10,
                margin=5
            )
        )
        self.page.update()

    async def process_input(self, e):
        user_text = self.user_input.value.strip()
        if not user_text:
            return
            
        self.add_message("You", user_text)
        self.user_input.value = ""
        self.page.update()
        
        await asyncio.sleep(0.5)  # Simulate thinking
        
        response = self.generate_response(user_text.lower())
        self.add_message("Erick AI", response, is_ai=True)

    def generate_response(self, text: str) -> str:
        # Check order status
        if any(w in text for w in ["status", "track", "where is my"]):
            return self.handle_order_status(text)
        
        # Menu inquiry
        elif "menu" in text:
            menu_text = "Menu yetu:\n"
            for item, details in MENU_ITEMS.items():
                menu_text += f"🍽️ {item}: TZS {details['price']:,}\n"
                menu_text += f"   {details['description']}\n"
            return menu_text + "\nUngependa kuagiza nini?"
        
        # Nutrition info
        elif any(w in text for w in ["ingredients", "viungo"]):
            items = [item for item in MENU_ITEMS if item.lower() in text]
            if items:
                response = ""
                for item in items:
                    details = MENU_ITEMS[item]
                    response += f"{item}:\n"
                    response += f"• Viungo: {', '.join(details['ingredients'])}\n"
                    response += f"• Bei: TZS {details['price']:,}\n\n"
                return response
            else:
                return "Samahani, sielewi chakula gani unahusu. Tafadhali niambie jina kamili."
        
        # Food recommendations
        elif any(w in text for w in ["pendekeza", "shauri"]):
            popular = max(MENU_ITEMS.items(), key=lambda x: x[1]['price'])
            return f"Napendekeza {popular[0]} - ni maarufu sana! {popular[1]['description']}"
        
        # Delivery questions
        elif any(w in text for w in ["delivery", "muda", "itachukua muda gani"]):
            return "Uwasilishaji huchukua dakika 30-45. Tunatengeneza chakula chako mara baada ya kuagizwa!"
        
        # Standard responses
        responses = {
            "greeting": [
                "Habari! Mimi ni Erick AI, msaidizi wako wa chakula. Nisaidie nini?",
                "Hujambo! Tuko tayari kukuhudumia."
            ],
            "help": "Naweza:\n- Kuchukua maagizo\n- Kufafanua vyakula\n- Kutoa maelezo ya viungo\n- Kufuatilia agizo lako\n- Kujibu maswali yoyote kuhusu chakula",
            "thanks": [
                "Karibu! Furahia chakula chako!",
                "Nimefurahi kukusaidia! 😊",
                "Ni raha yangu! Nipigie simu kama unahitaji msaada zaidi."
            ],
            "default": "Niko hapa kukusaidia kuhusu vyakula vyote! Unaweza kuuliza kuhusu:\n" +
                      "- Vyakula kwenye menyu\n- Viungo\n- Hali ya agizo\n- Uwasilishaji\n- Mapendekezo"
        }
        
        if any(w in text for w in ["hello", "hi", "hey", "habari", "jambo"]):
            return random.choice(responses["greeting"])
        elif any(w in text for w in ["help", "msaada", "saidia"]):
            return responses["help"]
        elif any(w in text for w in ["thank", "thanks", "asante", "shukrani"]):
            return random.choice(responses["thanks"])
        
        return responses["default"]

    def handle_order_status(self, text: str) -> str:
        for request in self.requests:
            if request.user_name.lower() in text.lower() or request.order_id in text:
                return (f"Agizo {request.order_id}:\n"
                       f"🍽️ {request.food_type} (x{request.quantity})\n"
                       f"💰 Jumla: TZS{request.price:,}\n"
                       f"📦 Hali: {request.delivery_status}\n"
                       f"⏱️ Imeagizwa: {request.timestamp}")
        return "Sikupata agizo lako. Tafadhali hakikisha jina au namba ya agizo."

    def show_ai_capabilities(self, e):
        capabilities = [
            "• Kuchukua maagizo ya chakula",
            "• Kufafanua vyakula kwa undani", 
            "• Kuangalia hali ya agizo",
            "• Kutoa mapendekezo",
            "• Kutoa maelezo ya viungo",
            "• Kujibu maswali kuhusu chakula",
            "• Kutoa maelezo ya vyakula"
        ]
        self.add_message("Erick AI", "Naweza kusaidia kwa:\n" + "\n".join(capabilities), is_ai=True)

# ======================
# MAIN APPLICATION
# ======================
def main(page: ft.Page):
    requests = DataManager.load_requests()
    confetti = ConfettiAnimation()
    
    page.title = "Mama Ntilie Food Delivery"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.fonts = {"Poppins": "https://fonts.googleapis.com/css2?family=Poppins"}
    page.theme = ft.Theme(font_family="Poppins")
    page.bgcolor = COLORS["background"]
    page.padding = 0
    
    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        page.bgcolor = COLORS["dark_bg"] if page.theme_mode == ft.ThemeMode.DARK else COLORS["background"]
        page.update()

    def text_color():
        return COLORS["dark_text"] if page.theme_mode == ft.ThemeMode.DARK else COLORS["text"]

    def get_food_icon(food_type: str) -> str:
        return MENU_ITEMS.get(food_type, {}).get("icon", "RESTAURANT")

    def build_header(title: str) -> ft.Row:
        return ft.Row([
            ft.IconButton(
                icon="DARK_MODE" if page.theme_mode == ft.ThemeMode.LIGHT else "LIGHT_MODE",
                on_click=toggle_theme,
                icon_color=text_color()
            ),
            ft.Text(title, size=24, weight=ft.FontWeight.BOLD, color=text_color()),
            ft.IconButton(
                icon="ARROW_BACK",
                on_click=lambda e: page.go("/"),
                icon_color=text_color()
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    def user_view() -> ft.Container:
        def submit_order(e):
            if not order_form.user_name.value or not order_form.food_type.value:
                order_form.status_text.value = "Tafadhali jaza sehemu zinazohitajika"
                order_form.status_text.color = COLORS["error"]
                page.update()
                return
            try:
                quantity = int(order_form.quantity.value)
                if quantity <= 0:
                    raise ValueError
            except ValueError:
                order_form.status_text.value = "Tafadhali weka idadi sahihi"
                order_form.status_text.color = COLORS["error"]
                page.update()
                return
            new_request = FoodRequest(
                order_form.user_name.value,
                order_form.food_type.value,
                quantity,
                order_form.special_requests.value
            )
            requests.append(new_request)
            DataManager.save_requests(requests)
            order_form.status_text.value = f"Agizo limewasilishwa! Namba ya agizo: {new_request.order_id}\nJumla: TZS {new_request.price:,}"
            order_form.status_text.color = COLORS["success"]
            order_form.user_name.value = ""
            order_form.food_type.value = ""
            order_form.quantity.value = "1"
            order_form.special_requests.value = ""
            order_form.submit_btn.bgcolor = COLORS["success"]
            page.update()
            order_form.submit_btn.bgcolor = COLORS["primary"]
            page.update()

        order_form = OrderForm(on_submit=submit_order)
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Image(
                        src="w.png",  # Using the image from phot.pyw
                        width=100,
                        height=100,
                        fit=ft.ImageFit.CONTAIN
                    ), 
                    ft.Column([
                        ft.Text("JR Food Service", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("Chakula cha nyumbani kwa bei nafuu", size=12, color=COLORS["primary"])
                    ], alignment=ft.MainAxisAlignment.CENTER)
                ], alignment=ft.MainAxisAlignment.CENTER),
                build_header("Weka Agizo Lako"),
                order_form.get_view(),
                ft.Row([
                    ft.ElevatedButton(
                        "Msimamizi",
                        on_click=lambda e: page.go("/admin"),
                        style=ft.ButtonStyle(
                            color=COLORS["primary"],
                            bgcolor=COLORS["transparent"],
                            side=ft.BorderSide(2, COLORS["primary"])
                        )
                    ),
                    ft.ElevatedButton(
                        "Ongea na Erick AI",
                        on_click=lambda e: page.go("/ai"),
                        icon="SMART_TOY",
                        style=ft.ButtonStyle(
                            color=COLORS["secondary"],
                            bgcolor=COLORS["transparent"],
                            side=ft.BorderSide(2, COLORS["secondary"])
                        )
                    )
                ], spacing=20, alignment=ft.MainAxisAlignment.CENTER)
            ], 
            alignment=ft.MainAxisAlignment.CENTER, 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            spacing=20),
            padding=40,
            width=page.width,
            alignment=ft.alignment.center
        )

    def admin_view() -> ft.Container:
        password_field = ft.TextField(
            label="Password ya Msimamizi",
            password=True,
            width=300,
            border_color=COLORS["primary"],
            focused_border_color=COLORS["secondary"]
        )
        login_btn = ft.ElevatedButton(
            "Ingia",
            bgcolor=COLORS["primary"],
            color=COLORS["white"],
            width=300,
            height=50
        )
        status_text = ft.Text("", color=COLORS["error"])
        requests_view = ft.Column(scroll=ft.ScrollMode.AUTO)
        stats_view = ft.Column()

                # Background image from phot.pyw
        bg_image = ft.Image(
            src="raw-pasta-nests-made-durum-wheat-flour-ripe-tomatoes-garlic-basil-leaves-peppercorns-preparing-pasta-italian-food-cooking-concept-nourishing-eating-noodles-white-background.jpg",
            width=page.width,
            height=page.height,
            fit=ft.ImageFit.COVER,
            opacity=0.5,
            repeat=ft.ImageRepeat.NO_REPEAT
        )
        def calculate_stats():
            total_orders = len(requests)
            completed_orders = sum(1 for r in requests if r.completed)
            total_revenue = sum(r.price for r in requests)
            popular_items = {}
            for r in requests:
                if r.food_type in popular_items:
                    popular_items[r.food_type] += r.quantity
                else:
                    popular_items[r.food_type] = r.quantity
            most_popular = max(popular_items.items(), key=lambda x: x[1], default=("Hakuna", 0))
            return {
                "total_orders": total_orders,
                "completed_orders": completed_orders,
                "total_revenue": total_revenue,
                "most_popular": most_popular
            }
        def refresh_requests():
            nonlocal requests
            requests = DataManager.load_requests()
            requests_view.controls.clear()
            stats_view.controls.clear()
            stats = calculate_stats()
            stats_view.controls.append(
                ft.Row([
                    ft.Card(
                        ft.Container(
                            ft.Column([
                                ft.Text("Jumla ya Maagizo", size=14),
                                ft.Text(str(stats["total_orders"]), size=24, weight=ft.FontWeight.BOLD)
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            padding=20,
                            width=150
                        ),
                        elevation=5
                    ),
                    ft.Card(
                        ft.Container(
                            ft.Column([
                                ft.Text("Maagizo Kamili", size=14),
                                ft.Text(str(stats["completed_orders"]), size=24, weight=ft.FontWeight.BOLD)
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            padding=20,
                            width=150
                        ),
                        elevation=5
                    ),
                    ft.Card(
                        ft.Container(
                            ft.Column([
                                ft.Text("Mapato", size=14),
                                ft.Text(f"TZS{stats['total_revenue']:,}", size=24, weight=ft.FontWeight.BOLD)
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            padding=20,
                            width=150
                        ),
                        elevation=5
                    ),
                    ft.Card(
                        ft.Container(
                            ft.Column([
                                ft.Text("Kipendwa Zaidi", size=14),
                                ft.Text(f"{stats['most_popular'][0]} (x{stats['most_popular'][1]})", 
                                      size=16, weight=ft.FontWeight.BOLD)
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            padding=20,
                            width=150
                        ),
                        elevation=5
                    )
                ], spacing=20)
            )
            if not requests:
                requests_view.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(name="EMPTY_DASHBOARD", size=50, color=COLORS["primary"]),
                            ft.Text("Hakuna maagizo bado!", color=text_color())
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=20,
                        alignment=ft.alignment.center
                    )
                )
                return
            for request in requests:
                status_dropdown = ft.Dropdown(
                    options=[ft.dropdown.Option(s) for s in DELIVERY_STATUSES],
                    value=request.delivery_status,
                    width=150,
                    on_change=lambda e, req=request: update_status(req, e.control.value)
                )
                request_card = ft.Card(
                    elevation=10,
                    content=ft.Container(
                        content=ft.Column([
                            ft.ListTile(
                                leading=ft.Icon(name=get_food_icon(request.food_type)),
                                title=ft.Text(f"Agizo {request.order_id}", weight=ft.FontWeight.BOLD, color=text_color()),
                                subtitle=ft.Text(
                                    f"Mteja: {request.user_name}\n"
                                    f"Chakula: {request.food_type} (x{request.quantity})\n"
                                    f"Jumla: TZS {request.price:,}\n"
                                    f"Hali: {request.delivery_status}\n"
                                    f"Maagizo maalum: {request.special_requests or 'Hakuna'}",
                                    color=text_color()
                                )
                            ),
                            ft.Row([
                                ft.ElevatedButton(
                                    "Kamilisha" if not request.completed else "Imekamilika",
                                    on_click=lambda e, req=request: toggle_complete(req),
                                    disabled=request.completed,
                                    bgcolor=COLORS["success"] if request.completed else None,
                                    color=COLORS["white"] if request.completed else None
                                ),
                                ft.IconButton(
                                    icon="DELETE",
                                    on_click=lambda e, req=request: delete_request(req),
                                    icon_color=COLORS["error"]
                                ),
                                status_dropdown
                            ], alignment=ft.MainAxisAlignment.END)
                        ]),
                        width=450,
                        padding=10,
                        bgcolor=f"{COLORS['primary']}20" if page.theme_mode == ft.ThemeMode.LIGHT else f"{COLORS['dark_bg']}80",
                        border_radius=10
                    )
                )
                if request.completed:
                    request_card.content.border = ft.border.all(2, COLORS["success"])
                requests_view.controls.append(request_card)
        def update_status(request, status):
            request.delivery_status = status
            DataManager.save_requests(requests)
            refresh_requests()
            page.update()
        def toggle_complete(request):
            request.completed = not request.completed
            if request.completed:
                request.delivery_status = "Delivered"
                confetti.create(page)
            DataManager.save_requests(requests)
            refresh_requests()
            page.update()
        def delete_request(request):
            requests.remove(request)
            DataManager.save_requests(requests)
            refresh_requests()
            page.update()
        def login(e):
            if password_field.value != ADMIN_PASSWORD:
                status_text.value = "Nywila si sahihi"
                page.update()
                return
            status_text.value = ""
            password_field.visible = False
            login_btn.visible = False
            refresh_requests()
            requests_view.visible = True
            stats_view.visible = True
            page.update()
        login_btn.on_click = login
        requests_view.visible = False
        stats_view.visible = False
        return ft.Container(
            content=ft.Column([
                build_header("Dashibodi ya Msimamizi"),
                password_field,
                login_btn,
                status_text,
                stats_view,
                requests_view,
                ft.ElevatedButton(
                    "Sasisha Maagizo",
                    on_click=lambda e: refresh_requests(),
                    icon="REFRESH",
                    bgcolor=COLORS["secondary"],
                    color=COLORS["white"]
                )
            ], alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
            padding=40,
            width=page.width
        )

    def ai_view() -> ft.Container:
        return ft.Container(
            content=ft.Column([
                build_header("Msaidizi wa Erick AI"),
                ErickAI(page, requests).get_view()
            ], spacing=20),
            padding=40,
            width=page.width,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[COLORS["primary"]+"20", COLORS["secondary"]+"20"]
            )
        )

    def route_change(e):
        page.views.clear()
        if page.route == "/" or page.route == "":
            page.views.append(ft.View("/", [user_view()], padding=0))
        elif page.route == "/admin":
            page.views.append(ft.View("/admin", [admin_view()], padding=0))
        elif page.route == "/ai":
            page.views.append(ft.View("/ai", [ai_view()], padding=0))
        page.update()
    
    page.on_route_change = route_change
    page.go(page.route)

if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER, assets_dir="assets")