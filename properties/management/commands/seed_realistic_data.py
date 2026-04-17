from decimal import Decimal
from pathlib import Path
import random
import unicodedata

from django.contrib.gis.geos import Point
from django.core.files import File
from django.core.management.base import BaseCommand

from accounts.models import Agent
from leads.models import Lead
from properties.models import Amenity, Property, PropertyImage


def slugify_vn(text):
    normalized = unicodedata.normalize("NFD", text)
    ascii_text = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    ascii_text = ascii_text.replace("đ", "d").replace("Đ", "D")
    return ascii_text.lower().replace(" ", ".")


class Command(BaseCommand):
    help = "Seed dữ liệu demo tiếng Việt sát thực tế thị trường TP.HCM cho GeoEstate"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Xoá dữ liệu seed cũ trước khi nạp lại")
        parser.add_argument("--properties", type=int, default=30)
        parser.add_argument("--agents", type=int, default=6)
        parser.add_argument("--amenities", type=int, default=40)
        parser.add_argument("--leads", type=int, default=12)

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

        district_profiles = {
            "Quận 1": {
                "center": (10.7769, 106.7009),
                "roads": ["Nguyễn Huệ", "Lê Lợi", "Tôn Đức Thắng", "Mạc Thị Bưởi", "Pasteur"],
                "apartment": {"price": (7000000000, 22000000000, 250000000), "area": (55, 145)},
                "house": {"price": (18000000000, 65000000000, 500000000), "area": (70, 220)},
                "land": {"price": (25000000000, 90000000000, 1000000000), "area": (80, 260)},
                "highlights": ["trung tâm tài chính", "gần phố đi bộ", "phù hợp khai thác cho thuê", "vị trí lõi trung tâm"],
            },
            "Quận 3": {
                "center": (10.7868, 106.6847),
                "roads": ["Võ Văn Tần", "Nam Kỳ Khởi Nghĩa", "Nguyễn Đình Chiểu", "Cách Mạng Tháng 8", "Bà Huyện Thanh Quan"],
                "apartment": {"price": (4500000000, 14000000000, 250000000), "area": (55, 130)},
                "house": {"price": (12000000000, 38000000000, 250000000), "area": (65, 210)},
                "land": {"price": (14000000000, 42000000000, 500000000), "area": (70, 220)},
                "highlights": ["khu dân cư lâu năm", "gần trung tâm", "thuận tiện mở văn phòng", "hẻm xe hơi dễ tiếp cận"],
            },
            "Bình Thạnh": {
                "center": (10.8016, 106.7108),
                "roads": ["Điện Biên Phủ", "Nguyễn Hữu Cảnh", "Phạm Viết Chánh", "Xô Viết Nghệ Tĩnh", "Ung Văn Khiêm"],
                "apartment": {"price": (3200000000, 10500000000, 100000000), "area": (50, 125)},
                "house": {"price": (7800000000, 26000000000, 250000000), "area": (60, 180)},
                "land": {"price": (9000000000, 30000000000, 500000000), "area": (70, 250)},
                "highlights": ["kết nối nhanh sang Quận 1", "gần Landmark 81", "nguồn cầu thuê tốt", "gần trục giao thông lớn"],
            },
            "Thủ Đức": {
                "center": (10.8490, 106.7537),
                "roads": ["Võ Nguyên Giáp", "Mai Chí Thọ", "Nguyễn Duy Trinh", "Xa lộ Hà Nội", "Đỗ Xuân Hợp"],
                "apartment": {"price": (2200000000, 8500000000, 100000000), "area": (48, 120)},
                "house": {"price": (5000000000, 18000000000, 250000000), "area": (65, 220)},
                "land": {"price": (4800000000, 24000000000, 250000000), "area": (80, 320)},
                "highlights": ["hưởng lợi hạ tầng khu Đông", "gần tuyến metro", "phù hợp mua ở lâu dài", "tiềm năng tăng giá tốt"],
            },
            "Quận 7": {
                "center": (10.7297, 106.7214),
                "roads": ["Nguyễn Lương Bằng", "Tân Trào", "Nguyễn Thị Thập", "Huỳnh Tấn Phát", "Hoàng Văn Thái"],
                "apartment": {"price": (3800000000, 13500000000, 100000000), "area": (55, 150)},
                "house": {"price": (9500000000, 32000000000, 250000000), "area": (75, 240)},
                "land": {"price": (11000000000, 36000000000, 500000000), "area": (85, 260)},
                "highlights": ["khu đô thị quy hoạch đồng bộ", "nhiều tiện ích quốc tế", "phù hợp gia đình trẻ", "môi trường sống thoáng"],
            },
            "Phú Nhuận": {
                "center": (10.8009, 106.6799),
                "roads": ["Phan Xích Long", "Nguyễn Văn Trỗi", "Hoàng Văn Thụ", "Trường Sa", "Phan Đăng Lưu"],
                "apartment": {"price": (3000000000, 9800000000, 100000000), "area": (48, 115)},
                "house": {"price": (8500000000, 26000000000, 250000000), "area": (60, 180)},
                "land": {"price": (10000000000, 30000000000, 500000000), "area": (70, 210)},
                "highlights": ["gần sân bay", "di chuyển thuận tiện", "khu dân cư đông đúc", "phù hợp ở kết hợp kinh doanh"],
            },
        }

        agent_profiles = [
            {"name": "Nguyễn Minh Quân", "district": "Quận 1", "specialty": "căn hộ cao cấp trung tâm"},
            {"name": "Trần Hoàng Nam", "district": "Quận 3", "specialty": "nhà phố khu trung tâm"},
            {"name": "Lê Bảo Châu", "district": "Bình Thạnh", "specialty": "căn hộ cho thuê và đầu tư"},
            {"name": "Phạm Gia Hân", "district": "Thủ Đức", "specialty": "nhà ở gia đình khu Đông"},
            {"name": "Võ Đức Khang", "district": "Quận 7", "specialty": "căn hộ khu đô thị mới"},
            {"name": "Bùi Thanh Trúc", "district": "Phú Nhuận", "specialty": "nhà phố gần sân bay"},
            {"name": "Đỗ Nhật Huy", "district": "Bình Thạnh", "specialty": "đất nền và tài sản đầu tư"},
            {"name": "Nguyễn Khánh Linh", "district": "Thủ Đức", "specialty": "bất động sản gần metro"},
        ]

        amenity_names = {
            "school": ["Vinschool", "THPT Lê Quý Đôn", "THPT Nguyễn Thị Minh Khai", "Đại học RMIT", "Đại học Fulbright"],
            "hospital": ["Bệnh viện FV", "Bệnh viện Chợ Rẫy", "Bệnh viện Vinmec Central Park", "Bệnh viện Quốc tế City", "Bệnh viện Hoàn Mỹ"],
            "park": ["Công viên Tao Đàn", "Công viên Vinhomes Central Park", "Công viên Crescent", "Công viên Lê Văn Tám", "Công viên Gia Định"],
            "mall": ["Takashimaya Sài Gòn", "Vincom Landmark 81", "Crescent Mall", "Thiso Mall Sala", "Saigon Centre"],
            "supermarket": ["Co.opmart", "WinMart", "MM Mega Market", "Lotte Mart", "AEON Citimart"],
            "transport": ["Ga Bến Thành", "Bến xe Miền Đông mới", "Ga Metro Thủ Đức", "Cửa ngõ sân bay Tân Sơn Nhất", "Nút giao An Phú"],
        }

        property_titles = {
            "apartment": [
                "Căn hộ cao tầng view sông thoáng mát",
                "Căn hộ 2PN nội thất hoàn chỉnh",
                "Căn hộ gần metro, tiện di chuyển",
                "Căn hộ gia đình tại khu compound",
                "Căn hộ đầu tư cho thuê dòng tiền ổn định",
            ],
            "house": [
                "Nhà phố hẻm xe hơi khu dân trí cao",
                "Nhà góc 2 mặt tiền thuận tiện kinh doanh",
                "Nhà mới hoàn thiện, vào ở ngay",
                "Nhà phố gần trục chính, kết nối trung tâm",
                "Nhà phù hợp vừa ở vừa làm văn phòng",
            ],
            "land": [
                "Lô đất vuông vức, pháp lý rõ ràng",
                "Đất nền khu dân cư hiện hữu",
                "Lô đất phù hợp xây nhà phố hoặc đầu tư",
                "Đất gần trục hạ tầng đang phát triển",
                "Đất vị trí đẹp, tiềm năng tăng giá tốt",
            ],
        }

        lead_profiles = [
            {"name": "Nguyễn Văn An", "interest": "apartment", "budget": (2500000000, 4200000000), "goal": "mua ở cho gia đình trẻ"},
            {"name": "Trần Minh Khoa", "interest": "house", "budget": (9000000000, 15000000000), "goal": "mua ở lâu dài, ưu tiên hẻm xe hơi"},
            {"name": "Lê Thu Hà", "interest": "apartment", "budget": (3500000000, 6500000000), "goal": "mua để ở gần nơi làm việc"},
            {"name": "Phạm Quốc Bảo", "interest": "land", "budget": (5000000000, 12000000000), "goal": "mua đầu tư trung hạn"},
            {"name": "Võ Ngọc Mai", "interest": "apartment,house", "budget": (4500000000, 9000000000), "goal": "tìm tài sản có thể cho thuê lại"},
            {"name": "Hoàng Gia Linh", "interest": "house,land", "budget": (7000000000, 18000000000), "goal": "mua tài sản tích luỹ dài hạn"},
            {"name": "Đặng Tuấn Kiệt", "interest": "apartment", "budget": (2200000000, 3800000000), "goal": "mua căn hộ gần metro"},
            {"name": "Ngô Phương Thảo", "interest": "house", "budget": (8000000000, 14000000000), "goal": "tìm nhà gần trường học cho con"},
        ]

        created_agents = []
        for idx, profile in enumerate(agent_profiles[:agent_count], start=1):
            district = profile["district"]
            lat, lng = district_profiles[district]["center"]
            email_slug = slugify_vn(profile["name"])
            phone = f"09{random.randint(0,9)}{idx}{random.randint(100000,999999)}"
            agent, _ = Agent.objects.get_or_create(
                email=f"{email_slug}@geoestate.vn",
                defaults={
                    "name": profile["name"],
                    "phone": phone,
                    "location": Point(lng + random.uniform(-0.008, 0.008), lat + random.uniform(-0.008, 0.008), srid=4326),
                },
            )
            created_agents.append({"agent": agent, "district": district, "specialty": profile["specialty"]})

        amenity_types = [choice[0] for choice in Amenity.AmenityType.choices if choice[0] != Amenity.AmenityType.OTHER]
        created_amenities = []
        for idx in range(amenity_count):
            amenity_type = amenity_types[idx % len(amenity_types)]
            district = random.choice(list(district_profiles.keys()))
            lat, lng = district_profiles[district]["center"]
            base_name = random.choice(amenity_names[amenity_type])
            amenity = Amenity.objects.create(
                name=f"{base_name} - {district}",
                amenity_type=amenity_type,
                location=Point(lng + random.uniform(-0.018, 0.018), lat + random.uniform(-0.018, 0.018), srid=4326),
            )
            created_amenities.append({"obj": amenity, "district": district})

        statuses = [
            Property.ListingStatus.ACTIVE,
            Property.ListingStatus.ACTIVE,
            Property.ListingStatus.ACTIVE,
            Property.ListingStatus.ACTIVE,
            Property.ListingStatus.SOLD,
            Property.ListingStatus.HIDDEN,
        ]

        created_properties = []
        district_names = list(district_profiles.keys())
        property_types = [choice[0] for choice in Property.PropertyType.choices]

        for idx in range(property_count):
            district = district_names[idx % len(district_names)] if idx < len(district_names) else random.choice(district_names)
            profile = district_profiles[district]
            property_type = random.choice(property_types)
            lat, lng = profile["center"]
            road = random.choice(profile["roads"])
            title = f"{random.choice(property_titles[property_type])} - {district}"
            address = f"{random.randint(12, 250)} {road}, {district}, TP.HCM"
            status = random.choice(statuses)
            market = profile[property_type]
            price = Decimal(random.randrange(*market["price"]))
            area = round(random.uniform(*market["area"]), 1)
            district_highlight = random.choice(profile["highlights"])
            matching_agents = [a for a in created_agents if a["district"] == district]
            assigned_agent = random.choice(matching_agents or created_agents)["agent"] if created_agents else None

            if property_type == Property.PropertyType.APARTMENT:
                desc = (
                    f"{title}. Căn hộ nằm trên trục {road}, thuộc khu vực {district} với lợi thế {district_highlight}. "
                    f"Phù hợp khách mua ở hoặc đầu tư cho thuê, diện tích {area} m², mức giá đang bám mặt bằng khu vực."
                )
            elif property_type == Property.PropertyType.HOUSE:
                desc = (
                    f"{title}. Nhà phố tại {district}, tiếp cận nhanh tuyến {road}, phù hợp nhu cầu ở thực hoặc khai thác văn phòng nhỏ. "
                    f"Khu vực có thanh khoản ổn định, dân cư hiện hữu, pháp lý dễ kiểm tra."
                )
            else:
                desc = (
                    f"{title}. Lô đất thuộc khu vực {district}, gần {road}, nổi bật nhờ {district_highlight}. "
                    f"Phù hợp xây mới hoặc nắm giữ đầu tư, diện tích {area} m² với biên độ tăng giá tốt theo hạ tầng."
                )

            prop = Property.objects.create(
                agent=assigned_agent,
                title=title,
                description=desc,
                property_type=property_type,
                listing_status=status,
                is_featured=False,
                price=price,
                area=area,
                address=address,
                location=Point(lng + random.uniform(-0.012, 0.012), lat + random.uniform(-0.012, 0.012), srid=4326),
            )

            local_amenities = [a["obj"] for a in created_amenities if a["district"] == district]
            fallback_amenities = [a["obj"] for a in created_amenities]
            amenity_pool = local_amenities or fallback_amenities
            if amenity_pool:
                prop.amenities.set(random.sample(amenity_pool, k=min(random.randint(2, 5), len(amenity_pool))))

            image_name = {
                "apartment": "apartment.jpg",
                "house": "house.jpg",
                "land": "land.jpg",
            }.get(property_type, "apartment.jpg")
            image_path = seed_dir / image_name
            if image_path.exists():
                with image_path.open("rb") as fh:
                    prop_image = PropertyImage(property=prop, is_primary=True, sort_order=0, caption=title)
                    prop_image.image.save(f"{property_type}-{idx + 1}.jpg", File(fh), save=True)

            created_properties.append(prop)

        active_properties = [p for p in created_properties if p.listing_status == Property.ListingStatus.ACTIVE]
        active_properties.sort(key=lambda p: (p.district if hasattr(p, "district") else "", -float(p.price)))
        for prop in active_properties[: max(4, min(6, len(active_properties)))]:
            prop.is_featured = True
            prop.save(update_fields=["is_featured"])

        for idx in range(lead_count):
            base = lead_profiles[idx % len(lead_profiles)]
            district = random.choice(district_names)
            lat, lng = district_profiles[district]["center"]
            budget = Decimal(random.randrange(base["budget"][0], base["budget"][1], 100000000))
            matching_agents = [a for a in created_agents if a["district"] == district]
            assigned_agent = random.choice(matching_agents or created_agents)["agent"] if created_agents else None
            note_lines = [
                f"Khách muốn {base['goal']} tại khu vực {district}.",
                f"Quan tâm loại hình: {base['interest']}.",
                random.choice([
                    "Ưu tiên pháp lý rõ ràng, có thể xem nhà cuối tuần.",
                    "Mong muốn thương lượng tốt nếu thanh toán nhanh.",
                    "Ưu tiên gần trường học, bệnh viện hoặc trung tâm thương mại.",
                    "Có thể xuống tiền trong 1-2 tháng nếu gặp tài sản phù hợp.",
                ]),
            ]
            Lead.objects.create(
                name=base["name"],
                phone=f"09{random.randint(0,9)}{random.randint(10000000,99999999)}",
                budget=budget,
                desired_location=Point(lng + random.uniform(-0.018, 0.018), lat + random.uniform(-0.018, 0.018), srid=4326),
                property_interest=base["interest"],
                notes=" ".join(note_lines),
                alert_enabled=random.choice([True, True, False]),
                assigned_agent=assigned_agent,
            )

        self.stdout.write(self.style.SUCCESS(
            f"Đã seed {len(created_agents)} môi giới, {len(created_amenities)} tiện ích, {len(created_properties)} bất động sản, {lead_count} lead với dữ liệu sát thực tế hơn."
        ))
