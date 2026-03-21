from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def price_vn(value):
    if value in (None, ""):
        return "Liên hệ"
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return value

    abs_amount = abs(amount)
    if abs_amount >= Decimal("1000000000"):
        scaled = amount / Decimal("1000000000")
        text = f"{scaled.quantize(Decimal('0.1'))}".rstrip("0").rstrip(".")
        return f"{text} tỷ"
    if abs_amount >= Decimal("1000000"):
        scaled = amount / Decimal("1000000")
        text = f"{scaled.quantize(Decimal('0.1'))}".rstrip("0").rstrip(".")
        return f"{text} triệu"
    if abs_amount >= Decimal("1000"):
        return f"{int(amount):,}".replace(",", ".") + " đ"
    return f"{int(amount)} đ"


@register.filter
def vnd_int(value):
    if value in (None, ""):
        return "-"
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return value
    return f"{int(amount):,}".replace(",", ".") + " đ"
