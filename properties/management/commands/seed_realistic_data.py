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
    help = "Seed dữ liệu mẫu thực tế bằng tiếng Việt cho GeoEstate"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Xoá dữ liệu seed cũ trước khi nạp lại")
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
            self.stdout.write(self.style.WARNING("Đã xoá dữ liệu lead, bất động sản, tiện ích và môi giới cũ."))

        district_centers = {
            "Quận 1": (10.7769, 106.7009),
            "Quận 3": (10.7868, 106.6847),
            "Bình Thạnh": (10.8016, 106.7108),
            "Thủ Đức": (10.8490, 106.7537),
            "Quận 7": (10.7297, 106.7214),
            "Phú Nhuận": (10.8009, 106.6799),
        }

        agent_profiles = [
            ("Nguyễn Minh Quân", "Quận 1"),
            ("Trần Hoàng Nam", "Quận 3"),
            ("Lê Bảo Châu", "Bình Thạnh"),
            ("Phạm Gia Hân", "Thủ Đức"),
            ("Võ Đức Khang", "Quận 7"),
            ("Bùi Thanh Trúc", "Phú Nhuận"),
            ("Đỗ Nhật Huy", "Quận 1"),
            ("Nguyễn Khánh Linh", "Thủ Đức"),
        ]

        amenity_names = {
            "school": [
                "Trường Vinschool",
                "Trường THPT Lê Quý Đôn",
                "Trường THPT Nguyễn Thị Minh Khai",
                "Đại học RMIT",
            ],
            "hospital": [
                "Bệnh viện FV",
                "Bệnh viện Chợ Rẫy",
                "Bệnh viện Vinmec Central Park",
                "Bệnh viện Quốc tế City",
            ],
            "park": [
                "Công viên Tao Đàn",
                "Công viên Vinhomes Central Park",
                "Công viên Crescent",
                "Công viên Lê Văn Tám",
            ],
            "mall": [
                "Takashimaya Sài Gòn",
                "Vincom Landmark 81",
                "Crescent Mall",
                "Thiso Mall Sala",
            ],
            "supermarket": [
                "Co.opmart",
                "WinMart",
                "MM Mega Market",
                "Lotte Mart",
            ],
            "transport": [
                "Ga Bến Thành",
                "Bến xe Miền Đông mới",
                "Ga Metro Thủ Đức",
                "Lối vào sân bay Tân Sơn Nhất",
            ],
        }

        property_titles = {
            "apartment": [
                "Căn hộ cao cấp view sông",
                "Căn hộ gần metro thiết kế hiện đại",
                "Căn hộ tầng cao tại tháp premium",
                "Căn hộ gia đình full nội thất thông minh",
                "Căn hộ 2PN ban công rộng thoáng",
            ],
            "house": [
                "Nhà phố trong khu dân cư yên tĩnh",
                "Nhà góc 2 mặt tiền gần trục chính",
                "Nhà gia đình hiện đại có sân thượng",
                "Nhà cải tạo đẹp gần trung tâm",
                "Nhà phố phù hợp ở kết hợp kinh doanh",
            ],
            "land": [
                "Đất ở gần trục phát triển hạ tầng",
                "Lô đất góc phù hợp xây nhà phố",
                "Đất đầu tư pháp lý rõ ràng",
                "Lô đất ven sông có tiềm năng tăng giá",
                "Đất khu dân cư hiện hữu dễ khai thác",
            ],
        }

        addresses = {
            "Quận 1": ["Nguyễn Huệ", "Lê Lợi", "Tôn Đức Thắng", "Mạc Thị Bưởi"],
            "Quận 3": ["Võ Văn Tần", "Nam Kỳ Khởi Nghĩa", "Cách Mạng Tháng 8", "Nguyễn Đình Chiểu"],
            "Bình Thạnh": ["Điện Biên Phủ", "Nguyễn Hữu Cảnh", "Phạm Viết Chánh", "Xô Viết Nghệ Tĩnh"],
            "Thủ Đức": ["Võ Nguyên Giáp", "Mai Chí Thọ", "Nguyễn Duy Trinh", "Xa lộ Hà Nội"],
            "Quận 7": ["Nguyễn Lương Bằng", "Tân Trào", "Nguyễn Thị Thập", "Huỳnh Tấn Phát"],
            "Phú Nhuận": ["Phan Xích Long", "Nguyễn Văn Trỗi", "Hoàng Văn Thụ", "Trường Sa"],
        }

        lead_names = [
            "Nguyễn Văn An",
            "Trần Minh Khoa",
            "Lê Thu Hà",
            "Phạm Quốc Bảo",
            "Võ Ngọc Mai",
            "Hoàng Gia Linh",
            "Đặng Tuấn Kiệt",
            "Ngô Phương Thảo",
        ]

        interests = ["apartment", "house", "land", "apartment,house", "house,land"]

        created_agents = []
        for idx, (name, district) in enumerate(agent_profiles[:agent_count], start=1):
            lat, lng = district_centers[district]
            slug = name.lower().replace(" ", ".")
            agent, _ = Agent.objects.get_or_create(
                email=f"{slug}@geoestate.vn",
                defaults={
                    "name": name,
                    "phone": f"09{idx}2{idx}4567{idx}",
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
                name=f"{base_name} - {district}",
                amenity_type=amenity_type,
                location=Point(lng + random.uniform(-0.02, 0.02), lat + random.uniform(-0.02, 0.02), srid=4326),
            )
            created_amenities.append(amenity)

        property_types = [choice[0] for choice in Property.PropertyType.choices]
        statuses = [
            Property.ListingStatus.ACTIVE,
            Property.ListingStatus.ACTIVE,
            Property.ListingStatus.ACTIVE,
            Property.ListingStatus.SOLD,
            Property.ListingStatus.HIDDEN,
        ]

        created_properties = []
        for idx in range(property_count):
            district = random.choice(list(district_centers.keys()))
            lat, lng = district_centers[district]
            property_type = random.choice(property_types)
            title = f"{random.choice(property_titles[property_type])} - {district}"
            address = f"{random.randint(12, 250)} {random.choice(addresses[district])}, {district}, TP.HCM"
            status = random.choice(statuses)

            if property_type == "apartment":
                price = Decimal(random.randrange(1800000000, 12000000000, 100000000))
                area = round(random.uniform(55, 140), 1)
                description = (
                    f"{title}. Căn hộ phù hợp gia đình trẻ hoặc khách mua đầu tư cho thuê. "
                    f"Vị trí thuận tiện di chuyển, gần tiện ích lớn và khu dân cư hiện hữu tại {district}."
                )
            elif property_type == "house":
                price = Decimal(random.randrange(4500000000, 28000000000, 250000000))
                area = round(random.uniform(70, 240), 1)
                description = (
                    f"{title}. Nhà có kết cấu tốt, phù hợp ở lâu dài hoặc khai thác kinh doanh nhỏ. "
                    f"Khu vực dân trí ổn định, kết nối nhanh tới các trục đường chính của {district}."
                )
            else:
                price = Decimal(random.randrange(2500000000, 35000000000, 250000000))
                area = round(random.uniform(80, 320), 1)
                description = (
                    f"{title}. Lô đất thích hợp xây mới hoặc đầu tư trung hạn. "
                    f"Pháp lý tham khảo tốt, nằm trong khu vực có tiềm năng tăng giá tại {district}."
                )

            prop = Property.objects.create(
                agent=random.choice(created_agents) if created_agents else None,
                title=title,
                description=description,
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
            budget = Decimal(random.randrange(1500000000, 15000000000, 100000000))
            property_interest = random.choice(interests)
            Lead.objects.create(
                name=random.choice(lead_names),
                phone=f"091{idx}56789{idx}",
                budget=budget,
                desired_location=Point(lng + random.uniform(-0.02, 0.02), lat + random.uniform(-0.02, 0.02), srid=4326),
                property_interest=property_interest,
                notes=f"Khách đang tìm {property_interest} quanh khu vực {district}, ưu tiên pháp lý rõ ràng và dễ thương lượng.",
                alert_enabled=random.choice([True, False]),
                assigned_agent=random.choice(created_agents) if created_agents else None,
            )

        self.stdout.write(self.style.SUCCESS(
            f"Đã seed {len(created_agents)} môi giới, {len(created_amenities)} tiện ích, {len(created_properties)} bất động sản, {lead_count} lead."
        ))
