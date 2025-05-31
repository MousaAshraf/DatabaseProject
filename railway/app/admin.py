from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from fastapi import Request
from db.database import engine
from db.models import User, Ticket, Station, Line, Subscription, Payment


# Basic authentication for SQLAdmin (replace with your actual admin auth)
class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        # Validate admin credentials (in production, use proper authentication)
        if username == "admin" and password == "admin123":
            request.session.update({"token": "admin-token"})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        return token == "admin-token"


# Model view


class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.username,
        User.firstname,
        User.lastname,
        User.email,
        User.is_admin,
    ]
    can_create = True
    can_edit = True
    can_delete = False
    name_plural = "Users"
    icon = "fa-solid fa-user"


class TicketAdmin(ModelView, model=Ticket):
    column_list = [
        Ticket.id,
        Ticket.user_id,
        Ticket.start_station_id,
        Ticket.end_station_id,
        Ticket.entry_time,
        Ticket.exit_time,
        Ticket.fare_paid,
        Ticket.created_at,
    ]
    can_export = True
    name_plural = "Tickets"
    icon = "fa-solid fa-ticket"


class StationAdmin(ModelView, model=Station):

    column_list = [Station.id, Station.line, Station.name, Station.zone]
    form_columns = [Station.line, Station.name, Station.station_order, Station.zone]
    name_plural = "Stations"
    icon = "fa-solid fa-train-station"


class LineAdmin(ModelView, model=Line):
    column_list = [Line.id, Line.name, Line.description, Line.is_active]
    name_plural = "Lines"
    icon = "fa-solid fa-train"


class SubscriptionAdmin(ModelView, model=Subscription):
    column_list = "__all__"
    name_plural = "Subscriptions"
    icon = "fa-solid fa-id-card"


class PaymentAdmin(ModelView, model=Payment):
    column_list = "__all__"
    name_plural = "Payments"
    icon = "fa-solid fa-credit-card"


def setup_admin(app):
    # Create admin interface
    authentication_backend = AdminAuth(secret_key="aswa2daacswk21wd-122e23-daw231-321")
    admin = Admin(
        app=app,
        engine=engine,
        authentication_backend=authentication_backend,
        title="Cairo Metro Admin",
        base_url="/admin",
    )

    # Add views
    admin.add_view(UserAdmin)
    admin.add_view(TicketAdmin)
    admin.add_view(StationAdmin)
    admin.add_view(LineAdmin)
    admin.add_view(SubscriptionAdmin)
    admin.add_view(PaymentAdmin)
