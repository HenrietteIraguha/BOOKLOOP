from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render

from distribution.models import Distribution
from donations.models import DonationSubmission
from inventory.models import Book, InventoryLot

PILOT_DONATIONS = 10
PILOT_BOOKS = 50
AVAILABLE = [InventoryLot.Status.ACCEPTED, InventoryLot.Status.IN_STORAGE]


def _qty(queryset):
    return queryset.aggregate(n=Sum("quantity"))["n"] or 0


def _percent(part, whole):
    return round(100 * part / whole) if whole else 0


def _grouped(lots, field):
    """Available copies grouped by a Book field, with readable labels and bar widths."""
    labels = dict(Book._meta.get_field(field).choices or [])
    rows = (lots.values(f"book__{field}")
                .annotate(n=Sum("quantity"))
                .order_by("-n"))
    top = rows[0]["n"] if rows else 0
    return [{"label": labels.get(r[f"book__{field}"], r[f"book__{field}"] or "Not set"),
             "n": r["n"], "width": _percent(r["n"], top)} for r in rows if r["n"]]



@login_required
@permission_required("inventory.view_inventorylot", raise_exception=True)
def report(request):
    lots = InventoryLot.objects.all()
    distributed = _qty(Distribution.objects.all())

    rejected = _qty(lots.filter(status=InventoryLot.Status.REJECTED))
    pending = _qty(lots.filter(status=InventoryLot.Status.PENDING_ASSESSMENT))
    available = _qty(lots.filter(status__in=AVAILABLE))
    still_held = _qty(lots)  # a lot's quantity goes down when books are given out
    collected = still_held + distributed
    accepted = collected - rejected - pending

    donations = DonationSubmission.objects.all()
    donation_count = donations.exclude(status=DonationSubmission.Status.REJECTED).count()

    dists = Distribution.objects.select_related("recipient", "lot__book")
    dist_total = dists.count()
    dist_recorded = dists.filter(recipient__isnull=False,
                                 distribution_date__isnull=False).count()

    status_labels = dict(DonationSubmission.Status.choices)
    by_status = [{"label": status_labels.get(r["status"], r["status"]), "n": r["n"]}
                 for r in donations.order_by().values("status").annotate(n=Count("id"))]

    by_month = (donations.annotate(month=TruncMonth("submitted_at"))
                         .order_by("month").values("month").annotate(n=Count("id")))

    type_labels = dict(dists.model._meta.get_field("recipient").related_model
                       ._meta.get_field("recipient_type").choices)

    by_recipient_type = [{"label": type_labels.get(r["recipient__recipient_type"], "Other"), "n": r["n"]}
                         for r in dists.order_by().values("recipient__recipient_type")
                                                  .annotate(n=Sum("quantity"))]

    available_lots = lots.filter(status__in=AVAILABLE)
    context = {
        "pilot": {
            "donations": donation_count, "donation_target": PILOT_DONATIONS,
            "donation_pct": min(_percent(donation_count, PILOT_DONATIONS), 100),
            "books": collected, "book_target": PILOT_BOOKS,
            "book_pct": min(_percent(collected, PILOT_BOOKS), 100),
            "assessed_pct": _percent(accepted + rejected, collected),
            "recorded_pct": _percent(dist_recorded, dist_total),
            "dist_total": dist_total,
        },
        "inv": {"collected": collected, "accepted": accepted, "rejected": rejected,
                "pending": pending, "available": available, "distributed": distributed},
        "by_level": _grouped(available_lots, "education_level"),
        "by_type": _grouped(available_lots, "book_type"),
        "by_status": by_status,
        "by_month": by_month,
        "by_recipient_type": by_recipient_type,
        "recent": dists.order_by("-distribution_date", "-id")[:10],
    }
    return render(request, "reports/report.html", context)
