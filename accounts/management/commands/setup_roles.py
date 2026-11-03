from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

# What each role is allowed to do. No role gets "delete": records are kept, not removed.
OPERATOR_PERMISSIONS = [
    # Books and inventory (FR-01 to FR-09)
    "add_book",
    "change_book",
    "view_book",
    "add_inventorylot",
    "change_inventorylot",
    "view_inventorylot",
    "view_statushistory",
    # Donations (FR-13, FR-14)
    "view_donor",
    "view_donationsubmission",
    "change_donationsubmission",
    "view_donationphoto",
    # Recipients and distribution (FR-10, FR-17)
    "add_recipient",
    "change_recipient",
    "view_recipient",
    "add_distribution",
    "view_distribution",
]

ADMINISTRATOR_PERMISSIONS = OPERATOR_PERMISSIONS + [
    "add_user",
    "change_user",  # includes deactivating an account
    "view_user",
    "view_group",
]

ROLES = {
    "Operator": OPERATOR_PERMISSIONS,
    "Administrator": ADMINISTRATOR_PERMISSIONS,
}


class Command(BaseCommand):
    help = "Create the Operator and Administrator roles with their permissions (FR-16, NFR-05)."

    def handle(self, *args, **options):
        for role_name, codenames in ROLES.items():
            group, _ = Group.objects.get_or_create(name=role_name)
            permissions = Permission.objects.filter(codename__in=codenames)
            group.permissions.set(permissions)
            self.stdout.write(self.style.SUCCESS(f"{role_name}: {permissions.count()} permissions"))
