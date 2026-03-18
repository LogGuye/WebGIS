import random

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from accounts.models import Agent
from leads.models import Lead
from properties.models import Amenity, Property


class Command(BaseCommand):
    help = "Seed demo data for Real Estate project"

    def handle(self, *args, **options):
        if Property.objects.exists():
            self.stdout.write(self.style.WARNING("Data already exists, skipping seed."))
            return

        self.stdout.write("Creating agents...")
        agents = []
        base_points = [
            (21.0285, 105.8542),
            (21.0035, 105.8200),
            (21.0405, 105.7800),
            (21.0150, 105.8500),
            (21.0500, 105.8000),
        ]
        for idx, (lat, lng) in enumerate(base_points, start=1):
            agent = Agent.objects.create(
                name=f"Agent {idx}",
                phone=f"0900{idx:04d}",
                email=f"agent{idx}@demo.com",
                location=Point(lng, lat, srid=4326),
            )
            agents.append(agent)

        self.stdout.write("Creating amenities...")
        amenity_types = [c[0] for c in Amenity.AmenityType.choices]
        amenities = []
        for i in range(20):
            lat = 21.01 + random.uniform(-0.03, 0.03)
            lng = 105.83 + random.uniform(-0.03, 0.03)
            amenity = Amenity.objects.create(
                name=f"Amenity {i+1}",
                amenity_type=random.choice(amenity_types),
                location=Point(lng, lat, srid=4326),
            )
            amenities.append(amenity)

        self.stdout.write("Creating properties...")
        prop_types = [c[0] for c in Property.PropertyType.choices]
        for i in range(10):
            lat = 21.02 + random.uniform(-0.03, 0.03)
            lng = 105.84 + random.uniform(-0.03, 0.03)
            prop = Property.objects.create(
                title=f"Property {i+1}",
                description="Mẫu mô tả bất động sản tại Hà Nội.",
                property_type=random.choice(prop_types),
                price=random.randint(2_000_000_000, 10_000_000_000),
                area=random.randint(50, 200),
                address=f"Số {i+10} Đường Demo, Hà Nội",
                location=Point(lng, lat, srid=4326),
                agent=random.choice(agents),
            )
            # attach random amenities
            prop.amenities.set(random.sample(amenities, k=min(3, len(amenities))))

        self.stdout.write("Creating leads...")
        for i in range(10):
            lat = 21.02 + random.uniform(-0.02, 0.02)
            lng = 105.84 + random.uniform(-0.02, 0.02)
            lead = Lead.objects.create(
                name=f"Lead {i+1}",
                phone=f"0911{i:04d}",
                budget=random.randint(2_000_000_000, 8_000_000_000),
                desired_location=Point(lng, lat, srid=4326),
                assigned_agent=random.choice(agents),
            )
            lead.save()

        self.stdout.write(self.style.SUCCESS("Seed data created successfully."))
