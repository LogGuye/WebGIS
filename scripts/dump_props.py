import os
import sys
sys.path.append(r'C:\Users\Admin\Desktop\GIS\WebGIS')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realestate.settings')
import django
django.setup()
from properties.models import Property
props = Property.objects.filter(listing_status=Property.ListingStatus.ACTIVE).order_by('pk')
with open('scripts/prop_dump.txt', 'w', encoding='utf-8') as out:
    for p in props:
        url = p.primary_image_url
        if hasattr(url, 'url'):
            url = url.url
        out.write(f"{p.pk}|{p.title}|{url}\n")
