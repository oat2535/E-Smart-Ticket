import os
import glob

files = glob.glob('c:\\E-Smart-Ticket-main\\equipment\\templates\\*.html')
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    content = content.replace("{% extends 'base.html' %}", "{% extends 'backend/layout.html' %}")
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
