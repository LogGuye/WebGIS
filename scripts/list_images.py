from properties.models import PropertyImage

for img in PropertyImage.objects.select_related('property').all()[:10]:
    print(img.property.title, img.image.name)
