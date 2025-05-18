category = Category.objects.first()
print(category.department_id)  # ควรคืนค่าเป็น instance ของ Department
print(category.department_id.department_name)  # ควรคืนค่าเป็นชื่อของ Department