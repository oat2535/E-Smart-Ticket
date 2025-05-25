# your_app/templatetags/custom_filters.py
from django import template

register = template.Library()

#ข้อความยาวเกิน 50 ตัวอักษรจะถูกขึ้นบรรทัดใหม่
# @register.filter
# def wrap_50(value):
#     if not isinstance(value, str):
#         return value
#     return '<br>'.join([value[i:i+50] for i in range(0, len(value), 50)])

#ตัดข้อความที่ยาวเกิน 50 ตัวอักษร
@register.filter
def wrap_50(value):
    if not isinstance(value, str):
        return value
    if len(value) > 50:
        return value[:50] + '...'
    return value

#ตัดข้อความหลังโรงพยาบาลสัตว์ ให้ขึ้นบรรทัดใหม่
@register.filter
def linebreak_after(value, text):
    if text in value:
        return value.replace(text, f"{text}<br>")
    return value