from properties.models import Property
props = Property.objects.filter(listing_status=Property.ListingStatus.ACTIVE).order_by('pk')
for p in props:
    print(p.pk, p.title, p.primary_image_url)
