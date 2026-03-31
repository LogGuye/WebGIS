from properties.models import Property
props = Property.objects.filter(listing_status=Property.ListingStatus.ACTIVE).order_by('pk')
with open('tmp_props.txt', 'w', encoding='utf-8') as out:
    for p in props:
        out.write(f"{p.pk}|{p.title}|{p.primary_image_url}\n")
