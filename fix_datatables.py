import os
import glob
import re

files = glob.glob('c:\\E-Smart-Ticket-main\\equipment\\templates\\*.html')

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Add destroy: true to DataTable initialization
    content = re.sub(r"(\$\('#dataTable'\)\.DataTable\(\{)", r"\1\n            destroy: true,", content)
    
    # Remove duplicate css and js includes for datatables
    content = re.sub(r"<link href=\"{% static 'vendor/datatables/dataTables\.bootstrap4\.min\.css' %}\" rel=\"stylesheet\">\n?", "", content)
    content = re.sub(r"<script src=\"{% static 'vendor/datatables/jquery\.dataTables\.min\.js' %}\"></script>\n?", "", content)
    content = re.sub(r"<script src=\"{% static 'vendor/datatables/dataTables\.bootstrap4\.min\.js' %}\"></script>\n?", "", content)

    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
