from decimal import Decimal
from pathlib import Path
import random

from django.core.files import File
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point

from accounts.models import Agent
from leads.models import Lead
from properties.models import Amenity, Property, PropertyImage


class Command(BaseCommand):
    help = "Seed realistic HCMC demo data for GeoEstate"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing seedable data before insert")
        parser.add_argument("--properties", type=int, default=30)
        parser.add_argument("--agents", type=int, default=6)
        parser.add_argument("--amenities", type=int, default=40)
        parser.add_argument("--leads", type=int, default=10)

    def handle(self, *args, **options):
        reset = options["reset"]
        property_count = options["properties"]
        agent_count = options["agents"]
        amenity_count = options["amenities"]
        lead_count = options["leads"]
        seed_dir = Path(__file__).resolve().parents[3] / "media" / "seed"

        if reset:
            Lead.objects.all().delete()
            Property.objects.all().delete()
            Amenity.objects.all().delete()
            Agent.objects.all().delete()
            self.stdout.write(self.style.WARNING("Existing leads, properties, amenities, and agents deleted."))

        district_centers = {
            "District 1": (10.7769, 106.7009),
            "District 3": (10.7868, 106.6847),
            "Binh Thanh": (10.8016, 106.7108),
            "Thu Duc": (10.8490, 106.7537),
            "District 7": (10.7297, 106.7214),
            "Phu Nhuan": (10.8009, 106.6799),
        }

        agent_names = [
            ("Nguyen Minh Quan", "District 1"),
            ("Tran Hoang Nam", "District 3"),
            ("Le Bao Chau", "Binh Thanh"),
            ("Pham Gia Han", "Thu Duc"),
            ("Vo Duc Khang", "District 7"),
            ("Bui Thanh Truc", "Phu Nhuan"),
            ("Do Nhat Huy", "District 1"),
            ("Nguyen Khanh Linh", "Thu Duc"),
        ]

        amenity_names = {
            "school": ["Vinschool", "Le Quy Don School", "Nguyen Thi Minh Khai High School", "RMIT Campus"],
            "hospital": ["FV Hospital", "Cho Ray Hospital", "Vinmec Central Park", "City International Hospital"],
            "park": ["Tao Dan Park", "Vinhomes Central Park", "Crescent Park", "Le Van Tam Park"],
            "mall": ["Takashimaya", "Vincom Landmark 81", "Crescent Mall", "Thiso Mall Sala"],
            "supermarket": ["Co.opmart", "WinMart", "MM Mega Market", "Lotte Mart"],
            "transport": ["Ben Thanh Station", "Mien Dong Bus Station", "Thu Duc Metro Stop", "Tan Son Nhat Access"],
        }

        property_titles = {
            "apartment": [
                "Luxury apartment with river view",
                "Modern apartment near metro",
                "High-floor apartment in premium tower",
                "Family apartment with smart-home setup",
            ],
            "house": [
                "Townhouse in quiet residential lane",
                "Corner house near main boulevard",
                "Modern family house with rooftop",
                "Renovated house close to CBD",
            ],
            "land": [
                "Residential land plot near growth corridor",
                "Corner land parcel for townhouse project",
                "Investment land with legal documents ready",
                "Riverside land plot with development potential",
            ],
        }

        addresses = {
            "District 1": ["Nguyen Hue", "Le Loi", "Ton Duc Thang", "Mac Thi Buoi"],
            "District 3": ["Vo Van Tan", "Nam Ky Khoi Nghia", "Cach Mang Thang 8", "Nguyen Dinh Chieu"],
            "Binh Thanh": ["Dien Bien Phu", "Nguyen Huu Canh", "Pham Viet Chanh", "Xo Viet Nghe Tinh"],
            "Thu Duc": ["Vo Nguyen Giap", "Mai Chi Tho", "Nguyen Duy Trinh", "Xa Lo Ha Noi"],
            "District 7": ["Nguyen Luong Bang", "Tan Trao", "Nguyen Thi Thap", "Huynh Tan Phat"],
            "Phu Nhuan": ["Phan Xich Long", "Nguyen Van Troi", "Hoang Van Thu", "Truong Sa"],
        }

        interests = ["apartment", "house", "land", "apartment,house", "house,land"]

        created_agents = []
        for idx, (name, district) in enumerate(agent_names[:agent_count], start=1):
            lat, lng = district_centers[district]
            agent, _ = Agent.objects.get_or_create(
                email=f"agent{idx}@geoestate.vn",
                defaults={
                    "name": name,
                    "phone": f"090{idx}23456{idx}",
                    "location": Point(lng + random.uniform(-0.01, 0.01), lat + random.uniform(-0.01, 0.01), srid=4326),
                },
            )
            created_agents.append(agent)

        amenity_types = [choice[0] for choice in Amenity.AmenityType.choices if choice[0] != Amenity.AmenityType.OTHER]
        created_amenities = []
        for idx in range(amenity_count):
            amenity_type = amenity_types[idx % len(amenity_types)]
            district = random.choice(list(district_centers.keys()))
            lat, lng = district_centers[district]
            base_name = random.choice(amenity_names[amenity_type])
            amenity = Amenity.objects.create(
                name=f"{base_name} {district}",
                amenity_type=amenity_type,
                location=Point(lng + random.uniform(-0.02, 0.02), lat + random.uniform(-0.02, 0.02), srid=4326),
            )
            created_amenities.append(amenity)

        property_types = [choice[0] for choice in Property.PropertyType.choices]
        statuses = [Property.ListingStatus.ACTIVE, Property.ListingStatus.ACTIVE, Property.ListingStatus.ACTIVE, Property.ListingStatus.SOLD, Property.ListingStatus.HIDDEN]

        created_properties = []
        for idx in range(property_count):
            district = random.choice(list(district_centers.keys()))
            lat, lng = district_centers[district]
            property_type = random.choice(property_types)
            title = f"{random.choice(property_titles[property_type])} - {district}"
            address = f"{random.randint(12, 250)} {random.choice(addresses[district])}, {district}, Ho Chi Minh City"
            status = random.choice(statuses)

            if property_type == "apartment":
                price = Decimal(random.randrange(1800000000, 12000000000, 100000000))
                area = round(random.uniform(55, 140), 1)
            elif property_type == "house":
                price = Decimal(random.randrange(4500000000, 28000000000, 250000000))
                area = round(random.uniform(70, 240), 1)
            else:
                price = Decimal(random.randrange(2500000000, 35000000000, 250000000))
                area = round(random.uniform(80, 320), 1)

            prop = Property.objects.create(
                agent=random.choice(created_agents) if created_agents else None,
                title=title,
                description=(
                    f"{title}. Located in {district}, this listing is suitable for both end-users and investors. "
                    f"Good access to major roads, amenities, and key urban services."
                ),
                property_type=property_type,
                listing_status=status,
                is_featured=False,
                price=price,
                area=area,
                address=address,
                location=Point(lng + random.uniform(-0.015, 0.015), lat + random.uniform(-0.015, 0.015), srid=4326),
            )
            sample_amenities = random.sample(created_amenities, k=min(random.randint(2, 5), len(created_amenities))) if created_amenities else []
            if sample_amenities:
                prop.amenities.set(sample_amenities)

            image_name = {
                "apartment": "apartment.svg",
                "house": "house.svg",
                "land": "land.svg",
            }.get(property_type, "apartment.svg")
            image_path = seed_dir / image_name
            if image_path.exists():
                with image_path.open("rb") as fh:
                    prop_image = PropertyImage(property=prop, is_primary=True, sort_order=0, caption=title)
                    prop_image.image.save(f"{property_type}-{idx + 1}.svg", File(fh), save=True)

            created_properties.append(prop)

        active_feature_candidates = [p for p in created_properties if p.listing_status == Property.ListingStatus.ACTIVE]
        for prop in active_feature_candidates[: max(3, min(5, len(active_feature_candidates)))]:
            prop.is_featured = True
            prop.save(update_fields=["is_featured"])

        for idx in range(lead_count):
            district = random.choice(list(district_centers.keys()))
            lat, lng = district_centers[district]
            Lead.objects.create(
                name=random.choice(["Nguyen Van An", "Tran Minh Khoa", "Le Thu Ha", "Pham Quoc Bao", "Vo Ngoc Mai", "Hoang Gia Linh"]),
                phone=f"091{idx}56789{idx}",
                budget=Decimal(random.randrange(1500000000, 15000000000, 100000000)),
                desired_location=Point(lng + random.uniform(-0.02, 0.02), lat + random.uniform(-0.02, 0.02), srid=4326),
                property_interest=random.choice(interests),
                notes=f"Looking for a realistic option around {district}.",
                alert_enabled=random.choice([True, False]),
                assigned_agent=random.choice(created_agents) if created_agents else None,
            )

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(created_agents)} agents, {len(created_amenities)} amenities, {len(created_properties)} properties, {lead_count} leads."
        ))
