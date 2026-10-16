import os
from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.base import ContentFile
from apps.accounts.models import User, Address
from apps.catalog.models import Category, Product, Variant, ProductAttribute, ProductImage
from apps.orders.models import DeliveryMethod, DiscountCode, Order, OrderItem


class Command(BaseCommand):
    help = 'Seeds database with 33 fencing products, variants, delivery methods, users, and sample orders'

    def handle(self, *args, **options):
        self.stdout.write("Starting database seed...")

        # 1. Create Users
        admin_user, _ = User.objects.get_or_create(
            email='admin@engarde.com',
            defaults={
                'name': 'Oana Stan (Admin)',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('admin1234')
        admin_user.save()

        customer_user, _ = User.objects.get_or_create(
            email='fencer@engarde.com',
            defaults={
                'name': 'Ana Popescu',
                'is_staff': False,
            }
        )
        customer_user.set_password('fencer1234')
        customer_user.save()

        # User Address
        Address.objects.get_or_create(
            user=customer_user,
            is_default=True,
            defaults={
                'full_name': 'Ana Popescu',
                'street': 'Strada Scrimă Nr. 12, Apt 4',
                'city': 'Bucharest',
                'postal_code': '010101',
                'country': 'Romania',
            }
        )

        Address.objects.get_or_create(
            user=customer_user,
            is_default=False,
            defaults={
                'full_name': 'Ana Popescu (Club Address)',
                'street': 'Bulevardul Sportului 45',
                'city': 'Bucharest',
                'postal_code': '020202',
                'country': 'Romania',
            }
        )

        # 2. Delivery Methods (A5 specification)
        standard_delivery, _ = DeliveryMethod.objects.get_or_create(
            name='Standard Delivery',
            defaults={'cost': Decimal('5.00'), 'estimated_days': '3-5 days'}
        )
        express_delivery, _ = DeliveryMethod.objects.get_or_create(
            name='Express Delivery',
            defaults={'cost': Decimal('12.00'), 'estimated_days': '1-2 days'}
        )

        # 3. Discount Codes (B5 specification)
        DiscountCode.objects.get_or_create(
            code='WELCOME10',
            defaults={
                'type': 'percentage',
                'value': Decimal('10.00'),
                'expires_at': timezone.now() + timedelta(days=90),
                'max_uses': 200,
                'used_count': 5,
            }
        )
        DiscountCode.objects.get_or_create(
            code='FENCER15',
            defaults={
                'type': 'fixed',
                'value': Decimal('15.00'),
                'expires_at': timezone.now() + timedelta(days=60),
                'max_uses': 100,
                'used_count': 12,
            }
        )

        # 4. Categories (5 categories: weapons, protective gear, electrical, spare parts, bags)
        cat_data = [
            ('weapons', 'Weapons', 'Electric and training foils, epees, and sabres configured for precision and balance.'),
            ('protective-gear', 'Protective Gear', 'FIE 800N and 350N CE certified jackets, breeches, underarm plastrons, masks, and gloves.'),
            ('electrical-equipment', 'Electrical Equipment', 'Heavy-duty 2-prong and 3-pin body cords, conductive lames, and scoring apparatus.'),
            ('spare-parts', 'Spare Parts', 'High-grade German and French tips, point screws, replacement springs, guards, and grips.'),
            ('bags', 'Bags', 'Wheelie strip bags, single weapon covers, and coaching backpacks for everyday training and travel.'),
        ]

        categories = {}
        for slug, name, desc in cat_data:
            c, _ = Category.objects.get_or_create(slug=slug, defaults={'name': name, 'description': desc})
            categories[slug] = c

        # 5. Products Catalog (33 products total)
        # Helper to generate an SVG placeholder file
        def generate_svg(product_name, category_name, color='#1e3a8a'):
            svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 450" width="100%" height="100%">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="{color}"/>
    </linearGradient>
  </defs>
  <rect width="600" height="450" rx="16" fill="url(#bg)"/>
  <circle cx="300" cy="180" r="70" fill="none" stroke="#e2e8f0" stroke-width="3" stroke-dasharray="6,6" opacity="0.4"/>
  <!-- Fencing Crossed Blades Icon -->
  <path d="M220 260 L380 100 M220 260 L235 275 M225 255 L240 270" stroke="#f8fafc" stroke-width="4" stroke-linecap="round"/>
  <path d="M380 260 L220 100 M380 260 L365 275 M375 255 L360 270" stroke="#f8fafc" stroke-width="4" stroke-linecap="round"/>
  <circle cx="230" cy="270" r="8" fill="#38bdf8"/>
  <circle cx="370" cy="270" r="8" fill="#38bdf8"/>
  <text x="300" y="330" fill="#f8fafc" font-size="22" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-weight="700" text-anchor="middle">{product_name}</text>
  <text x="300" y="365" fill="#94a3b8" font-size="14" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" text-anchor="middle" letter-spacing="2">{category_name.upper()}</text>
  <rect x="235" y="385" width="130" height="26" rx="13" fill="#38bdf8" fill-opacity="0.2"/>
  <text x="300" y="402" fill="#38bdf8" font-size="12" font-family="sans-serif" font-weight="600" text-anchor="middle">EN GARDE GEAR</text>
</svg>'''
            return ContentFile(svg_content.encode('utf-8'), name=f"{product_name.lower().replace(' ', '_')[:30]}.svg")

        products_spec = [
            # === WEAPONS (7 products) ===
            {
                'cat': 'weapons',
                'name': 'Club Electric Foil',
                'slug': 'club-electric-foil',
                'desc': 'Reliable electric foil tailored for club training and domestic competitions. Balanced tempered spring-steel blade with standard rubber/insulated socket.',
                'attrs': {'weapon_type': 'foil', 'certification': 'Club standard', 'level': 'Training'},
                'variants': [
                    ('FOIL-CLB-F-R5', '5 (Adult)', 'Right', 'French', Decimal('65.00'), 15),
                    ('FOIL-CLB-F-L5', '5 (Adult)', 'Left', 'French', Decimal('65.00'), 8),
                    ('FOIL-CLB-P-R5', '5 (Adult)', 'Right', 'Visconti', Decimal('72.00'), 20),
                    ('FOIL-CLB-P-L5', '5 (Adult)', 'Left', 'Visconti', Decimal('72.00'), 10),
                    ('FOIL-CLB-B-R5', '5 (Adult)', 'Right', 'Belgian', Decimal('74.00'), 8),
                    ('FOIL-CLB-B-L5', '5 (Adult)', 'Left', 'Belgian', Decimal('74.00'), 5),
                    ('FOIL-CLB-P-R2', '2 (Cadet)', 'Right', 'Visconti', Decimal('68.00'), 6),
                    ('FOIL-CLB-P-L2', '2 (Cadet)', 'Left', 'Visconti', Decimal('68.00'), 4),
                    ('FOIL-CLB-F-R0', '0 (Under-10)', 'Right', 'French', Decimal('59.00'), 5),
                    ('FOIL-CLB-F-L0', '0 (Under-10)', 'Left', 'French', Decimal('59.00'), 3),
                ]
            },
            {
                'cat': 'weapons',
                'name': 'FIE Maraging Electric Foil',
                'slug': 'fie-maraging-electric-foil',
                'desc': 'Competition-grade tournament foil forged from premium maraging steel. Homologated by the FIE for world-class durability and high resistance to stress fractures.',
                'attrs': {'weapon_type': 'foil', 'certification': 'FIE homologated', 'level': 'Competition'},
                'variants': [
                    ('FOIL-FIE-P-R5-M', '5 (Medium)', 'Right', 'Visconti', Decimal('155.00'), 12),
                    ('FOIL-FIE-P-L5-M', '5 (Medium)', 'Left', 'Visconti', Decimal('155.00'), 6),
                    ('FOIL-FIE-P-R5-S', '5 (Stiff)', 'Right', 'Visconti', Decimal('155.00'), 8),
                    ('FOIL-FIE-B-R5', '5 (Medium)', 'Right', 'Belgian', Decimal('160.00'), 8),
                    ('FOIL-FIE-B-L5', '5 (Medium)', 'Left', 'Belgian', Decimal('160.00'), 4),
                    ('FOIL-FIE-F-R5', '5 (Medium)', 'Right', 'French', Decimal('149.00'), 4),
                    ('FOIL-FIE-F-L5', '5 (Medium)', 'Left', 'French', Decimal('149.00'), 3),
                ]
            },
            {
                'cat': 'weapons',
                'name': 'Standard Electric Epee',
                'slug': 'standard-electric-epee',
                'desc': 'A robust competition-ready epee with stainless steel bell guard, insulated socket, and responsive medium-stiffness V-profile blade.',
                'attrs': {'weapon_type': 'epee', 'certification': 'Club standard', 'level': 'Training'},
                'variants': [
                    ('EPEE-STD-P-R5', '5 (Adult)', 'Right', 'Visconti', Decimal('78.00'), 18),
                    ('EPEE-STD-P-L5', '5 (Adult)', 'Left', 'Visconti', Decimal('78.00'), 9),
                    ('EPEE-STD-F-R5', '5 (Adult)', 'Right', 'French', Decimal('74.00'), 12),
                    ('EPEE-STD-F-L5', '5 (Adult)', 'Left', 'French', Decimal('74.00'), 6),
                    ('EPEE-STD-B-R5', '5 (Adult)', 'Right', 'Belgian', Decimal('79.00'), 7),
                    ('EPEE-STD-P-R2', '2 (Cadet)', 'Right', 'Visconti', Decimal('72.00'), 5),
                    ('EPEE-STD-F-R0', '0 (Under-10)', 'Right', 'French', Decimal('68.00'), 4),
                ]
            },
            {
                'cat': 'weapons',
                'name': 'FIE BF White Electric Epee',
                'slug': 'fie-bf-white-electric-epee',
                'desc': 'Handmade in France by BF, the undisputed gold standard in competitive epee fencing. Unrivalled balance, precise point control, and legendary maraging lifespan.',
                'attrs': {'weapon_type': 'epee', 'certification': 'FIE homologated', 'level': 'Competition'},
                'variants': [
                    ('EPEE-BFW-P-R5-M', '5 (Medium)', 'Right', 'Visconti', Decimal('185.00'), 10),
                    ('EPEE-BFW-P-R5-D', '5 (Stiff)', 'Right', 'Visconti', Decimal('185.00'), 14),
                    ('EPEE-BFW-P-L5-M', '5 (Medium)', 'Left', 'Visconti', Decimal('185.00'), 5),
                    ('EPEE-BFW-P-L5-D', '5 (Stiff)', 'Left', 'Visconti', Decimal('185.00'), 4),
                    ('EPEE-BFW-B-R5', '5 (Medium)', 'Right', 'Belgian', Decimal('189.00'), 6),
                    ('EPEE-BFW-F-R5', '5 (Medium)', 'Right', 'French', Decimal('179.00'), 7),
                    ('EPEE-BFW-F-L5', '5 (Medium)', 'Left', 'French', Decimal('179.00'), 3),
                ]
            },
            {
                'cat': 'weapons',
                'name': 'Standard Electric Sabre',
                'slug': 'standard-electric-sabre',
                'desc': 'Complete electric sabre with S2000 compliant tempered blade, standard insulated guard, and comfortable non-slip rubber grip.',
                'attrs': {'weapon_type': 'sabre', 'certification': 'Club standard', 'level': 'Training'},
                'variants': [
                    ('SAB-STD-R5', '5 (Adult)', 'Right', 'Sabre Standard', Decimal('62.00'), 16),
                    ('SAB-STD-L5', '5 (Adult)', 'Left', 'Sabre Standard', Decimal('62.00'), 8),
                    ('SAB-STD-R2', '2 (Youth)', 'Right', 'Sabre Standard', Decimal('58.00'), 5),
                    ('SAB-STD-L2', '2 (Youth)', 'Left', 'Sabre Standard', Decimal('58.00'), 4),
                    ('SAB-STD-R0', '0 (Under-10)', 'Right', 'Sabre Standard', Decimal('55.00'), 4),
                ]
            },
            {
                'cat': 'weapons',
                'name': 'FIE Maraging Electric Sabre',
                'slug': 'fie-maraging-electric-sabre',
                'desc': 'FIE certified competitive sabre weapon engineered for high-speed cutting and lightning-fast parries. Exceptional balance and blade longevity.',
                'attrs': {'weapon_type': 'sabre', 'certification': 'FIE homologated', 'level': 'Competition'},
                'variants': [
                    ('SAB-FIE-R5', '5 (Adult)', 'Right', 'Sabre Pro Grip', Decimal('140.00'), 11),
                    ('SAB-FIE-L5', '5 (Adult)', 'Left', 'Sabre Pro Grip', Decimal('140.00'), 5),
                    ('SAB-FIE-R5-LTH', '5 (Adult)', 'Right', 'Leather Grip', Decimal('145.00'), 7),
                    ('SAB-FIE-L5-LTH', '5 (Adult)', 'Left', 'Leather Grip', Decimal('145.00'), 4),
                ]
            },
            {
                'cat': 'weapons',
                'name': 'Non-Electric Practice Foil for Beginners',
                'slug': 'non-electric-practice-foil-beginners',
                'desc': 'Dry practice foil with dummy button tip for introductory classes and footwork drills. Perfect first weapon for beginners.',
                'attrs': {'weapon_type': 'foil', 'certification': 'Beginner', 'level': 'Introductory'},
                # SPEC REQUIREMENT: One product with all variants at stock 0
                'variants': [
                    ('FOIL-DRY-R0', '0 (Under-10)', 'Right', 'French', Decimal('38.00'), 0),
                    ('FOIL-DRY-R2', '2 (Youth)', 'Right', 'French', Decimal('40.00'), 0),
                    ('FOIL-DRY-R5', '5 (Adult)', 'Right', 'French', Decimal('42.00'), 0),
                    ('FOIL-DRY-L5', '5 (Adult)', 'Left', 'French', Decimal('42.00'), 0),
                ]
            },

            # === PROTECTIVE GEAR (9 products) ===
            {
                'cat': 'protective-gear',
                'name': "Apex 350N Fencing Jacket, Men's",
                'slug': 'apex-350n-fencing-jacket-mens',
                'desc': 'Lightweight and breathable CE Level 1 (350 Newton) certified jacket for men. Ergonomic cut with stretch back panel for unrestricted lunging and fleche.',
                'attrs': {'weapon_type': 'all', 'certification': '350N CE Level 1', 'level': 'Club'},
                'variants': [
                    ('JKT-350M-R46', '46', 'Right', '', Decimal('95.00'), 4),
                    ('JKT-350M-R48', '48', 'Right', '', Decimal('95.00'), 6),
                    ('JKT-350M-R50', '50', 'Right', '', Decimal('95.00'), 9),
                    ('JKT-350M-R52', '52', 'Right', '', Decimal('95.00'), 6),
                    ('JKT-350M-R54', '54', 'Right', '', Decimal('95.00'), 4),
                    ('JKT-350M-R56', '56', 'Right', '', Decimal('98.00'), 3),
                    ('JKT-350M-L48', '48', 'Left', '', Decimal('95.00'), 2),
                    ('JKT-350M-L50', '50', 'Left', '', Decimal('95.00'), 3),
                    ('JKT-350M-L52', '52', 'Left', '', Decimal('95.00'), 2),
                ]
            },
            {
                'cat': 'protective-gear',
                'name': "Apex 350N Fencing Jacket, Women's",
                'slug': 'apex-350n-fencing-jacket-womens',
                'desc': 'Tailored female-cut 350N CE Level 1 jacket offering superior comfort, moisture-wicking lining, and contoured chest shaping.',
                'attrs': {'weapon_type': 'all', 'certification': '350N CE Level 1', 'level': 'Club'},
                'variants': [
                    ('JKT-350W-R36', '36', 'Right', '', Decimal('95.00'), 4),
                    ('JKT-350W-R38', '38', 'Right', '', Decimal('95.00'), 5),
                    ('JKT-350W-R40', '40', 'Right', '', Decimal('95.00'), 8),
                    ('JKT-350W-R42', '42', 'Right', '', Decimal('95.00'), 7),
                    ('JKT-350W-R44', '44', 'Right', '', Decimal('95.00'), 4),
                    ('JKT-350W-L38', '38', 'Left', '', Decimal('95.00'), 2),
                    ('JKT-350W-L40', '40', 'Left', '', Decimal('95.00'), 3),
                    ('JKT-350W-L42', '42', 'Left', '', Decimal('95.00'), 2),
                ]
            },
            {
                'cat': 'protective-gear',
                'name': 'Pro 800N FIE Fencing Jacket, Unisex',
                'slug': 'pro-800n-fie-fencing-jacket-unisex',
                'desc': 'Elite FIE certified 800 Newton jacket constructed from high-tensile dyneema blend fibers. Maximum puncture protection required for all international competitions.',
                'attrs': {'weapon_type': 'all', 'certification': '800N FIE Level 2', 'level': 'Competition'},
                'variants': [
                    ('JKT-800F-R46', '46', 'Right', '', Decimal('210.00'), 5),
                    ('JKT-800F-R48', '48', 'Right', '', Decimal('210.00'), 7),
                    ('JKT-800F-R50', '50', 'Right', '', Decimal('210.00'), 10),
                    ('JKT-800F-R52', '52', 'Right', '', Decimal('210.00'), 8),
                    ('JKT-800F-R54', '54', 'Right', '', Decimal('210.00'), 4),
                    ('JKT-800F-R56', '56', 'Right', '', Decimal('215.00'), 3),
                    ('JKT-800F-L48', '48', 'Left', '', Decimal('210.00'), 3),
                    ('JKT-800F-L50', '50', 'Left', '', Decimal('210.00'), 4),
                    ('JKT-800F-L52', '52', 'Left', '', Decimal('210.00'), 2),
                ]
            },
            {
                'cat': 'protective-gear',
                'name': 'Apex 350N Fencing Breeches',
                'slug': 'apex-350n-fencing-breeches',
                'desc': 'Stretch 350N fencing breeches with padded knee protection and adjustable high waist braces. Complies with national tournament standards.',
                'attrs': {'weapon_type': 'all', 'certification': '350N CE Level 1', 'level': 'Club'},
                'variants': [
                    ('BRC-350-R46', '46', 'Right', '', Decimal('70.00'), 5),
                    ('BRC-350-R48', '48', 'Right', '', Decimal('70.00'), 8),
                    ('BRC-350-R50', '50', 'Right', '', Decimal('70.00'), 12),
                    ('BRC-350-R52', '52', 'Right', '', Decimal('70.00'), 9),
                    ('BRC-350-R54', '54', 'Right', '', Decimal('70.00'), 5),
                    ('BRC-350-L48', '48', 'Left', '', Decimal('70.00'), 3),
                    ('BRC-350-L50', '50', 'Left', '', Decimal('70.00'), 4),
                    ('BRC-350-L52', '52', 'Left', '', Decimal('70.00'), 2),
                ]
            },
            {
                'cat': 'protective-gear',
                'name': 'Pro 800N FIE Fencing Breeches',
                'slug': 'pro-800n-fie-fencing-breeches',
                'desc': 'FIE certified 800N tournament breeches providing ultimate safety and total freedom of movement during deep lunges.',
                'attrs': {'weapon_type': 'all', 'certification': '800N FIE Level 2', 'level': 'Competition'},
                'variants': [
                    ('BRC-800-R46', '46', 'Right', '', Decimal('145.00'), 4),
                    ('BRC-800-R48', '48', 'Right', '', Decimal('145.00'), 6),
                    ('BRC-800-R50', '50', 'Right', '', Decimal('145.00'), 8),
                    ('BRC-800-R52', '52', 'Right', '', Decimal('145.00'), 6),
                    ('BRC-800-R54', '54', 'Right', '', Decimal('145.00'), 4),
                    ('BRC-800-L48', '48', 'Left', '', Decimal('145.00'), 3),
                    ('BRC-800-L50', '50', 'Left', '', Decimal('145.00'), 3),
                ]
            },
            {
                'cat': 'protective-gear',
                'name': '800N FIE Underarm Plastron',
                'slug': '800n-fie-underarm-plastron',
                'desc': 'Mandatory extra layer of protection covering the weapon arm and chest. 800 Newton FIE homologated ballistic fabric.',
                'attrs': {'weapon_type': 'all', 'certification': '800N FIE Level 2', 'level': 'All levels'},
                'variants': [
                    ('PLS-800-RXS', 'XS', 'Right', '', Decimal('45.00'), 8),
                    ('PLS-800-RS', 'S', 'Right', '', Decimal('45.00'), 15),
                    ('PLS-800-RM', 'M', 'Right', '', Decimal('45.00'), 25),
                    ('PLS-800-RL', 'L', 'Right', '', Decimal('45.00'), 20),
                    ('PLS-800-RXL', 'XL', 'Right', '', Decimal('45.00'), 8),
                    ('PLS-800-RXXL', 'XXL', 'Right', '', Decimal('48.00'), 5),
                    ('PLS-800-LS', 'S', 'Left', '', Decimal('45.00'), 5),
                    ('PLS-800-LM', 'M', 'Left', '', Decimal('45.00'), 7),
                    ('PLS-800-LL', 'L', 'Left', '', Decimal('45.00'), 5),
                ]
            },
            {
                'cat': 'protective-gear',
                'name': '350N Fencing Mask (Foil & Epee)',
                'slug': '350n-fencing-mask-foil-epee',
                'desc': 'High-tensile steel mesh mask with 350N bib. Removable washable interior padding, padded rear safety contour, and dual security backstraps.',
                'attrs': {'weapon_type': 'foil', 'certification': '350N CE Level 1', 'level': 'Club'},
                'variants': [
                    ('MSK-350-XS', 'XS (Youth)', '', '', Decimal('82.00'), 8),
                    ('MSK-350-S', 'S', '', '', Decimal('85.00'), 10),
                    ('MSK-350-M', 'M', '', '', Decimal('85.00'), 18),
                    ('MSK-350-L', 'L', '', '', Decimal('85.00'), 14),
                    ('MSK-350-XL', 'XL', '', '', Decimal('85.00'), 6),
                ]
            },
            {
                'cat': 'protective-gear',
                'name': '800N FIE Contour Sabre Mask',
                'slug': '800n-fie-contour-sabre-mask',
                'desc': 'Premium stainless mesh sabre mask fully insulated with conductive bib and collar. FIE 1600N/800N homologation for global competitions.',
                'attrs': {'weapon_type': 'sabre', 'certification': '800N FIE Level 2', 'level': 'Competition'},
                'variants': [
                    ('MSK-SAB-S', 'S', '', '', Decimal('160.00'), 4),
                    ('MSK-SAB-M', 'M', '', '', Decimal('160.00'), 7),
                    ('MSK-SAB-L', 'L', '', '', Decimal('160.00'), 5),
                    # SPEC REQUIREMENT: One variant at stock 1
                    ('MSK-SAB-XL', 'XL', '', '', Decimal('160.00'), 1),
                ]
            },
            {
                'cat': 'protective-gear',
                'name': 'Padded Fencing Glove with Anti-Slip Grip',
                'slug': 'padded-fencing-glove-anti-slip-grip',
                'desc': 'Durable clarino palm fencing glove with silicon micro-dots for maximum traction on pistol grips. Reinforced thumb seam and cushioned cuff.',
                'attrs': {'weapon_type': 'all', 'certification': '350N CE Level 1', 'level': 'All levels'},
                'variants': [
                    ('GLV-R70', '7.0', 'Right', '', Decimal('28.00'), 8),
                    ('GLV-R75', '7.5', 'Right', '', Decimal('28.00'), 12),
                    ('GLV-R80', '8.0', 'Right', '', Decimal('28.00'), 20),
                    ('GLV-R85', '8.5', 'Right', '', Decimal('28.00'), 18),
                    ('GLV-R90', '9.0', 'Right', '', Decimal('28.00'), 15),
                    ('GLV-R95', '9.5', 'Right', '', Decimal('28.00'), 10),
                    ('GLV-L75', '7.5', 'Left', '', Decimal('28.00'), 4),
                    ('GLV-L80', '8.0', 'Left', '', Decimal('28.00'), 6),
                    ('GLV-L85', '8.5', 'Left', '', Decimal('28.00'), 5),
                    ('GLV-L90', '9.0', 'Left', '', Decimal('28.00'), 3),
                ]
            },

            # === ELECTRICAL EQUIPMENT (6 products) ===
            {
                'cat': 'electrical-equipment',
                'name': 'Transparent Foil & Sabre 2-Prong Body Cord',
                'slug': 'transparent-foil-sabre-2-prong-body-cord',
                'desc': 'Clear polycarbonate plugs for instant visual wire inspection. Highly flexible silicone stranded copper wire resistant to kinking and internal breaks.',
                'attrs': {'weapon_type': 'foil', 'certification': 'FIE certified specs', 'level': 'All levels'},
                'variants': [
                    ('CRD-2P-18', '1.8 m', '', '', Decimal('18.00'), 35),
                    ('CRD-2P-20', '2.0 m (Standard)', '', '', Decimal('19.00'), 45),
                    ('CRD-2P-22', '2.2 m (Extended)', '', '', Decimal('21.00'), 20),
                ]
            },
            {
                'cat': 'electrical-equipment',
                'name': 'Epee 3-Pin Clear Shell Body Cord',
                'slug': 'epee-3-pin-clear-shell-body-cord',
                'desc': 'Three-pin heavy-gauge epee body cord with strain relief boots and gold-plated contact pins for ultra-low electrical resistance.',
                'attrs': {'weapon_type': 'epee', 'certification': 'FIE certified specs', 'level': 'All levels'},
                'variants': [
                    ('CRD-3P-18', '1.8 m', '', '', Decimal('20.00'), 25),
                    ('CRD-3P-20', '2.0 m (Standard)', '', '', Decimal('21.00'), 40),
                    ('CRD-3P-22', '2.2 m (Long)', '', '', Decimal('23.00'), 15),
                ]
            },
            {
                'cat': 'electrical-equipment',
                'name': 'Ultra-Flex Mask to Lamé Wire Cord',
                'slug': 'ultra-flex-mask-to-lame-wire-cord',
                'desc': 'Coiled crocodile clip mask lead for foil and sabre masks. Strong spring teeth ensure consistent electrical contact during intense bouts.',
                'attrs': {'weapon_type': 'foil', 'certification': 'Standard', 'level': 'All levels'},
                'variants': [
                    ('CRD-MSK-STD', 'Standard Coiled', '', '', Decimal('8.50'), 50),
                    ('CRD-MSK-HVY', 'Heavy-Duty Reinforced', '', '', Decimal('11.00'), 30),
                ]
            },
            {
                'cat': 'electrical-equipment',
                'name': 'Inox Foil Electric Lamé Vest',
                'slug': 'inox-foil-electric-lame-vest',
                'desc': 'Stainless steel wire woven into lightweight fabric. Outstanding corrosion resistance against sweat and oxidation. Back-zip competition design.',
                'attrs': {'weapon_type': 'foil', 'certification': 'FIE homologated', 'level': 'Competition'},
                'variants': [
                    ('LAM-FOIL-R46', '46', 'Right', '', Decimal('115.00'), 5),
                    ('LAM-FOIL-R48', '48', 'Right', '', Decimal('115.00'), 7),
                    ('LAM-FOIL-R50', '50', 'Right', '', Decimal('115.00'), 11),
                    ('LAM-FOIL-R52', '52', 'Right', '', Decimal('115.00'), 9),
                    ('LAM-FOIL-R54', '54', 'Right', '', Decimal('115.00'), 4),
                    ('LAM-FOIL-L48', '48', 'Left', '', Decimal('115.00'), 3),
                    ('LAM-FOIL-L50', '50', 'Left', '', Decimal('115.00'), 4),
                ]
            },
            {
                'cat': 'electrical-equipment',
                'name': 'Inox Sabre Electric Lamé Jacket',
                'slug': 'inox-sabre-electric-lame-jacket',
                'desc': 'Long-sleeve stainless conductive sabre lamé covering full valid target area (torso, arms, neck). Durable front-zip closure with conductive collar.',
                'attrs': {'weapon_type': 'sabre', 'certification': 'FIE homologated', 'level': 'Competition'},
                'variants': [
                    ('LAM-SAB-R46', '46', 'Right', '', Decimal('135.00'), 4),
                    ('LAM-SAB-R48', '48', 'Right', '', Decimal('135.00'), 6),
                    ('LAM-SAB-R50', '50', 'Right', '', Decimal('135.00'), 8),
                    ('LAM-SAB-R52', '52', 'Right', '', Decimal('135.00'), 5),
                    ('LAM-SAB-R54', '54', 'Right', '', Decimal('135.00'), 3),
                    ('LAM-SAB-L48', '48', 'Left', '', Decimal('135.00'), 3),
                    ('LAM-SAB-L50', '50', 'Left', '', Decimal('135.00'), 3),
                ]
            },
            {
                'cat': 'electrical-equipment',
                'name': 'Digital 3-Weapon Tabletop Scoring Apparatus',
                'slug': 'digital-3-weapon-tabletop-scoring-apparatus',
                'desc': 'Microprocessor scoring box for foil, epee, and sabre according to current FIE timing regulations. High-visibility LED lights and loud acoustic buzzer.',
                'attrs': {'weapon_type': 'all', 'certification': 'FIE timing compliant', 'level': 'Club & Tournaments'},
                'variants': [
                    ('BOX-DIGI-STD', 'Standard Unit + Power Adapter', '', '', Decimal('380.00'), 5),
                    ('BOX-DIGI-BAT', 'Rechargeable Battery Edition', '', '', Decimal('420.00'), 3),
                ]
            },

            # === SPARE PARTS (7 products) ===
            {
                'cat': 'spare-parts',
                'name': 'Complete Foil Barrel & Spring Point Assembly',
                'slug': 'complete-foil-barrel-spring-point-assembly',
                'desc': 'Precision German-style foil point assembly including brass barrel, contact spring, pressure spring, and top screw set.',
                'attrs': {'weapon_type': 'foil', 'certification': 'Standard', 'level': 'Armourer'},
                'variants': [
                    ('PRT-FLP-GER', 'German Standard Type', '', '', Decimal('14.00'), 30),
                    ('PRT-FLP-GER-PRO', 'German FIE Gold Contact', '', '', Decimal('16.00'), 25),
                    ('PRT-FLP-FRN', 'French Classic Type', '', '', Decimal('12.50'), 20),
                ]
            },
            {
                'cat': 'spare-parts',
                'name': 'Complete German Epee Point Assembly',
                'slug': 'complete-german-epee-point-assembly',
                'desc': 'FIE homologated German epee tip assembly with hardened contact tip, barrel, pressure spring, and two microscopic headless screws.',
                'attrs': {'weapon_type': 'epee', 'certification': 'FIE homologated', 'level': 'Armourer'},
                'variants': [
                    ('PRT-EPP-STD', 'German FIE Standard Point', '', '', Decimal('16.50'), 40),
                    ('PRT-EPP-TIT', 'Titanium Light Point', '', '', Decimal('22.00'), 20),
                ]
            },
            {
                'cat': 'spare-parts',
                'name': 'German Epee Point Screws (Pack of 10)',
                'slug': 'german-epee-point-screws-pack-10',
                'desc': 'Essential replacement point screws for German epee barrels. Precision-machined threading that stays seated even under heavy impact.',
                'attrs': {'weapon_type': 'epee', 'certification': 'Standard', 'level': 'Armourer'},
                'variants': [
                    ('PRT-SCR-EP10', '10-Pack Standard', '', '', Decimal('4.50'), 60),
                    ('PRT-SCR-EP25', '25-Pack Value Pack', '', '', Decimal('9.50'), 40),
                ]
            },
            {
                'cat': 'spare-parts',
                'name': 'Heavy-Duty Stainless Steel Epee Bell Guard',
                'slug': 'heavy-duty-stainless-steel-epee-bell-guard',
                'desc': 'Pressed aircraft-grade aluminum alloy guard with rolled lip edge to prevent tip punctures and deflect point attacks cleanly.',
                'attrs': {'weapon_type': 'epee', 'certification': 'FIE specification', 'level': 'All levels'},
                'variants': [
                    ('PRT-GRD-EP-STD', 'Standard Polished Duralumin', '', '', Decimal('18.00'), 25),
                    ('PRT-GRD-EP-TIT', 'Titanium Ultra-Light (120g)', '', '', Decimal('36.00'), 12),
                    ('PRT-GRD-EP-XTR', 'Extra Reinforced Heavy Duty', '', '', Decimal('24.00'), 15),
                ]
            },
            {
                'cat': 'spare-parts',
                'name': 'Insulated Foil Bell Guard',
                'slug': 'insulated-foil-bell-guard',
                'desc': 'Official size foil guard with durable epoxy insulation coating on inside surfaces to prevent accidental grounding faults.',
                'attrs': {'weapon_type': 'foil', 'certification': 'FIE specification', 'level': 'All levels'},
                'variants': [
                    ('PRT-GRD-FL-STD', 'Standard Guard (10cm)', '', '', Decimal('14.50'), 22),
                    ('PRT-GRD-FL-SM', 'Youth Guard (9.5cm)', '', '', Decimal('14.00'), 15),
                ]
            },
            {
                'cat': 'spare-parts',
                'name': 'Visconti Ergonomic Pistol Grip Handle',
                'slug': 'visconti-ergonomic-pistol-grip-handle',
                'desc': 'Anatomically molded pistol grip cast from solid aluminum alloy with textured powder-coat finish for maximum wrist control and leverage.',
                'attrs': {'weapon_type': 'foil', 'certification': 'All levels', 'level': 'All levels'},
                'variants': [
                    ('PRT-GRP-VIS-RXS', 'XS', 'Right', 'Visconti', Decimal('16.00'), 10),
                    ('PRT-GRP-VIS-RS', 'S', 'Right', 'Visconti', Decimal('16.00'), 15),
                    ('PRT-GRP-VIS-RM', 'M', 'Right', 'Visconti', Decimal('16.00'), 25),
                    ('PRT-GRP-VIS-RL', 'L', 'Right', 'Visconti', Decimal('16.00'), 18),
                    ('PRT-GRP-VIS-LS', 'S', 'Left', 'Visconti', Decimal('16.00'), 8),
                    ('PRT-GRP-VIS-LM', 'M', 'Left', 'Visconti', Decimal('16.00'), 10),
                    ('PRT-GRP-VIS-LL', 'L', 'Left', 'Visconti', Decimal('16.00'), 6),
                ]
            },
            {
                'cat': 'spare-parts',
                'name': 'High-Adhesion Fencing Blade Tip Tape',
                'slug': 'high-adhesion-fencing-blade-tip-tape',
                'desc': 'Non-conductive, puncture-resistant adhesive tape for insulating the upper 15 cm of foil blades as required by FIE competition rules.',
                'attrs': {'weapon_type': 'foil', 'certification': 'FIE rule compliant', 'level': 'All levels'},
                'variants': [
                    ('PRT-TPE-BLU', 'Royal Blue 10m', '', '', Decimal('5.00'), 40),
                    ('PRT-TPE-RED', 'Crimson Red 10m', '', '', Decimal('5.00'), 35),
                    ('PRT-TPE-WHT', 'Fencing White 10m', '', '', Decimal('5.00'), 35),
                    ('PRT-TPE-BLK', 'Stealth Black 10m', '', '', Decimal('5.00'), 30),
                ]
            },

            # === BAGS (4 products) ===
            {
                'cat': 'bags',
                'name': 'Compact Single Weapon Sword Sleeve Bag',
                'slug': 'compact-single-weapon-sword-sleeve-bag',
                'desc': 'Waterproof ripstop nylon sleeve with shoulder strap and exterior pocket for a mask cord and body wire. Protects blades during commute.',
                'attrs': {'weapon_type': 'all', 'certification': 'Standard', 'level': 'Training'},
                'variants': [
                    ('BAG-SLV-BLK', 'Classic Black', '', '', Decimal('22.00'), 25),
                    ('BAG-SLV-NAV', 'Navy Blue', '', '', Decimal('22.00'), 18),
                    ('BAG-SLV-RED', 'Racing Red', '', '', Decimal('22.00'), 12),
                ]
            },
            {
                'cat': 'bags',
                'name': 'Club Double Pocket Weapon & Mask Carrier Bag',
                'slug': 'club-double-pocket-weapon-mask-carrier-bag',
                'desc': 'Guitare-shaped club bag carrying up to 3 weapons in the bottom chamber and a mask, jacket, and shoes in the spacious upper compartment.',
                'attrs': {'weapon_type': 'all', 'certification': 'Standard', 'level': 'Club'},
                'variants': [
                    ('BAG-CLB-BLK', 'Standard Dual Compartment (Black)', '', '', Decimal('65.00'), 16),
                    ('BAG-CLB-BLU', 'Standard Dual Compartment (Blue)', '', '', Decimal('65.00'), 12),
                ]
            },
            {
                'cat': 'bags',
                'name': 'Pro Wheeled Tournament Strip Bag',
                'slug': 'pro-wheeled-tournament-strip-bag',
                'desc': 'Heavy-duty dual-level wheeled bag with rigid honeycomb base and all-terrain ball-bearing urethane wheels. Features detachable top weapon bag.',
                'attrs': {'weapon_type': 'all', 'certification': 'Heavy-duty travel', 'level': 'Tournaments'},
                'variants': [
                    ('BAG-WHL-BLK', 'Matte Black / Silver', '', '', Decimal('195.00'), 8),
                    ('BAG-WHL-BLU', 'Electric Blue / Navy', '', '', Decimal('195.00'), 6),
                    ('BAG-WHL-RED', 'Crimson / Grey', '', '', Decimal('195.00'), 5),
                ]
            },
            {
                'cat': 'bags',
                'name': 'Armourer Tool & Cord Organizer Roll',
                'slug': 'armourer-tool-cord-organizer-roll',
                'desc': 'Canvas roll-up organizer equipped with elastic loops for test weight, thickness gauges, hex keys, spare screws, and wire testing multimeter.',
                'attrs': {'weapon_type': 'all', 'certification': 'Heavy-duty', 'level': 'Armourer'},
                'variants': [
                    ('BAG-ROL-ARM-KHK', 'Heavy Canvas Roll (Khaki)', '', '', Decimal('29.00'), 15),
                    ('BAG-ROL-ARM-BLK', 'Heavy Canvas Roll (Black)', '', '', Decimal('29.00'), 15),
                ]
            },
        ]

        total_variants_count = 0

        for p_data in products_spec:
            cat = categories[p_data['cat']]
            product, created = Product.objects.get_or_create(
                slug=p_data['slug'],
                defaults={
                    'category': cat,
                    'name': p_data['name'],
                    'description': p_data['desc'],
                    'is_active': True,
                }
            )

            # Product Image
            if not product.images.exists():
                img_file = generate_svg(product.name, cat.name)
                ProductImage.objects.create(
                    product=product,
                    file=img_file,
                    position=0
                )

            # Attributes
            for attr_name, attr_val in p_data.get('attrs', {}).items():
                ProductAttribute.objects.get_or_create(
                    product=product,
                    name=attr_name,
                    defaults={'value': attr_val}
                )

            # Variants
            for sku, size, handedness, grip, price, stock in p_data['variants']:
                Variant.objects.get_or_create(
                    sku=sku,
                    defaults={
                        'product': product,
                        'size': size,
                        'handedness': handedness,
                        'grip_type': grip,
                        'price': price,
                        'stock': stock,
                    }
                )
                total_variants_count += 1

        # 6. Sample Past Orders for Customer Ana Popescu (A8 Requirement)
        # Order 1: EG-1040 (Shipped)
        order1, o1_created = Order.objects.get_or_create(
            number='EG-1040',
            defaults={
                'user': customer_user,
                'status': Order.Status.SHIPPED,
                'delivery_method': standard_delivery,
                'subtotal': Decimal('95.00'),
                'discount': Decimal('0.00'),
                'shipping_cost': Decimal('5.00'),
                'total': Decimal('100.00'),
                'shipping_full_name': 'Ana Popescu',
                'shipping_street': 'Strada Scrimă Nr. 12',
                'shipping_city': 'Bucharest',
                'shipping_postal_code': '010101',
                'shipping_country': 'Romania',
            }
        )
        if o1_created:
            v_jacket = Variant.objects.filter(product__slug='apex-350n-fencing-jacket-womens').first()
            OrderItem.objects.create(
                order=order1,
                variant=v_jacket,
                product_name=v_jacket.product.name,
                variant_label=v_jacket.label,
                unit_price=v_jacket.price,
                quantity=1
            )

        # Order 2: EG-1041 (New)
        order2, o2_created = Order.objects.get_or_create(
            number='EG-1041',
            defaults={
                'user': customer_user,
                'status': Order.Status.NEW,
                'delivery_method': standard_delivery,
                'subtotal': Decimal('48.00'),
                'discount': Decimal('0.00'),
                'shipping_cost': Decimal('5.00'),
                'total': Decimal('53.00'),
                'shipping_full_name': 'Ana Popescu',
                'shipping_street': 'Strada Scrimă Nr. 12',
                'shipping_city': 'Bucharest',
                'shipping_postal_code': '010101',
                'shipping_country': 'Romania',
            }
        )
        if o2_created:
            v_cord = Variant.objects.filter(product__slug='transparent-foil-sabre-2-prong-body-cord').first()
            v_tape = Variant.objects.filter(product__slug='high-adhesion-fencing-blade-tip-tape').first()
            if v_cord:
                OrderItem.objects.create(
                    order=order2,
                    variant=v_cord,
                    product_name=v_cord.product.name,
                    variant_label=v_cord.label,
                    unit_price=v_cord.price,
                    quantity=2
                )
            if v_tape:
                OrderItem.objects.create(
                    order=order2,
                    variant=v_tape,
                    product_name=v_tape.product.name,
                    variant_label=v_tape.label,
                    unit_price=v_tape.price,
                    quantity=2
                )

        # Order 3: EG-1042 (Paid)
        order3, o3_created = Order.objects.get_or_create(
            number='EG-1042',
            defaults={
                'user': customer_user,
                'status': Order.Status.PAID,
                'delivery_method': standard_delivery,
                'subtotal': Decimal('121.00'),
                'discount': Decimal('0.00'),
                'shipping_cost': Decimal('5.00'),
                'total': Decimal('126.00'),
                'shipping_full_name': 'Ana Popescu',
                'shipping_street': 'Strada Scrimă Nr. 12',
                'shipping_city': 'Bucharest',
                'shipping_postal_code': '010101',
                'shipping_country': 'Romania',
            }
        )
        if o3_created:
            v_mask = Variant.objects.filter(product__slug='350n-fencing-mask-foil-epee').first()
            v_glove = Variant.objects.filter(product__slug='padded-fencing-glove-anti-slip-grip').first()
            if v_mask:
                OrderItem.objects.create(
                    order=order3,
                    variant=v_mask,
                    product_name=v_mask.product.name,
                    variant_label=v_mask.label,
                    unit_price=v_mask.price,
                    quantity=1
                )
            if v_glove:
                OrderItem.objects.create(
                    order=order3,
                    variant=v_glove,
                    product_name=v_glove.product.name,
                    variant_label=v_glove.label,
                    unit_price=v_glove.price,
                    quantity=1
                )

        self.stdout.write(self.style.SUCCESS(
            f"Database seeded successfully! Created {len(products_spec)} products with {total_variants_count} variants."
        ))
        self.stdout.write(self.style.SUCCESS(
            "Admin user: admin@engarde.com / admin1234 (Argon2)\nCustomer user: fencer@engarde.com / fencer1234"
        ))
