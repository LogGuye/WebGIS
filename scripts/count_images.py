import os
import sys
sys.path.append(r'C:\Users\Admin\Desktop\GIS\WebGIS')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realestate.settings')
import django
django.setup()
from properties.models import PropertyImage
print(PropertyImage.objects.count())
