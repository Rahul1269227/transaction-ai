#!/usr/bin/env python3
"""Generate realistic training data for weak categories using real merchant names."""

import json
import random
from datetime import datetime, timedelta

# Real-world merchants and transaction patterns
CATEGORY_DATA = {
    'home_improvement': {
        'merchants': [
            'Home Depot', 'Lowes', 'Ace Hardware', 'Menards', 'True Value',
            'Benjamin Moore', 'Sherwin Williams', 'Floor & Decor',
            'Build.com', 'Ferguson', 'Lumber Liquidators', 'The Tile Shop',
            'Tractor Supply Co', 'Harbor Freight Tools', 'Northern Tool',
            'Wayfair', 'Overstock', 'Houzz', 'Build Direct', 'Carpet One'
        ],
        'items': [
            'lumber', 'paint', 'tools', 'hardware', 'screws and nails',
            'flooring', 'tiles', 'cabinets', 'countertops', 'lighting fixtures',
            'plumbing supplies', 'electrical supplies', 'insulation', 'drywall',
            'doors and windows', 'roofing materials', 'deck materials',
            'garden supplies', 'power tools', 'hand tools', 'measuring tape',
            'drill bits', 'saw blades', 'sandpaper', 'wood stain', 'primer',
            'caulk', 'spackle', 'grout', 'mortar', 'concrete mix',
            'PVC pipes', 'copper fittings', 'light switches', 'outlets',
            'circuit breakers', 'wire', 'conduit', 'junction boxes',
            'bathroom fixtures', 'kitchen faucet', 'shower head', 'toilet',
            'vanity', 'mirror', 'towel bars', 'shelf brackets', 'hinges',
            'door knobs', 'locks', 'weatherstripping', 'garage door opener'
        ],
        'services': [
            'contractor services', 'plumbing repair', 'electrical work',
            'HVAC installation', 'roof repair', 'window installation',
            'flooring installation', 'painting service', 'drywall repair',
            'deck building', 'fence installation', 'gutter cleaning',
            'handyman services', 'appliance installation'
        ]
    },

    'pets': {
        'merchants': [
            'PetSmart', 'Petco', 'Chewy.com', 'Pet Supplies Plus',
            'Tractor Supply Co', 'Only Natural Pet', 'Mud Bay',
            'VCA Animal Hospital', 'Banfield Pet Hospital', 'BluePearl',
            'PetVet365', 'Wagly', 'Wag!', 'Rover.com', 'Camp Bow Wow',
            'Dogtopia', 'PetsHotel', 'Pet Paradise', 'K9 Resort',
            'Chuck & Dons', 'Hollywood Feed', 'Pet Valu', 'Pet Supermarket',
            'Kriser\'s Natural Pet', 'Bentley\'s Pet Stuff'
        ],
        'items': [
            'dog food', 'cat food', 'dog treats', 'cat treats', 'bird seed',
            'fish food', 'rabbit pellets', 'hamster food', 'reptile food',
            'pet vitamins', 'flea treatment', 'heartworm medication',
            'pet shampoo', 'nail clippers', 'brush and comb', 'pet bed',
            'dog crate', 'cat litter', 'litter box', 'scratching post',
            'pet toys', 'chew toys', 'interactive toys', 'catnip',
            'dog collar', 'leash', 'harness', 'ID tags', 'pet bowl',
            'water fountain', 'aquarium', 'fish tank filter', 'gravel',
            'pet carrier', 'gate', 'training pads', 'waste bags',
            'automatic feeder', 'pet camera', 'grooming supplies'
        ],
        'services': [
            'veterinary exam', 'vaccination', 'spay/neuter surgery',
            'dental cleaning', 'microchipping', 'pet grooming',
            'nail trim', 'ear cleaning', 'flea bath', 'dog boarding',
            'doggy daycare', 'pet sitting', 'dog walking', 'training class',
            'behavior consultation', 'emergency vet visit', 'x-ray',
            'blood work', 'prescription medication'
        ],
        'brands': [
            'Purina', 'Royal Canin', 'Blue Buffalo', 'Hills Science Diet',
            'Iams', 'Pedigree', 'Taste of the Wild', 'Wellness', 'Orijen',
            'Acana', 'Nutro', 'Natural Balance', 'Merrick', 'Fromm',
            'Fancy Feast', 'Friskies', 'Meow Mix', 'Whiskas', 'Sheba'
        ]
    },

    'kids_family': {
        'merchants': [
            'Firstcry', 'Hopscotch', 'Mothercare', 'BabyOye', 'Hamleys',
            'Toys R Us', 'The Childrens Place', 'Carter\'s', 'OshKosh',
            'Gymboree', 'Gap Kids', 'Old Navy Kids', 'H&M Kids',
            'Target Kids', 'Walmart Kids', 'Buy Buy Baby', 'Babies R Us',
            'Pottery Barn Kids', 'Crate & Kids', 'Land of Nod',
            'Little Tikes', 'Step2', 'Fisher-Price', 'Melissa & Doug',
            'KidKraft', 'Radio Flyer', 'Bright Horizons', 'KinderCare',
            'The Goddard School', 'Primrose Schools', 'La Petite Academy',
            'Tutor Time', 'Learning Care Group', 'Kiddie Academy'
        ],
        'items': [
            'baby clothes', 'toddler shoes', 'kids clothing', 'school uniform',
            'backpack', 'lunch box', 'water bottle', 'diapers', 'baby wipes',
            'diaper rash cream', 'baby formula', 'baby food', 'bottles',
            'pacifiers', 'teething toys', 'baby monitor', 'crib', 'bassinet',
            'changing table', 'high chair', 'stroller', 'car seat',
            'baby carrier', 'play mat', 'swing', 'bouncer', 'walker',
            'educational toys', 'building blocks', 'puzzles', 'board games',
            'action figures', 'dolls', 'stuffed animals', 'art supplies',
            'coloring books', 'crayons', 'markers', 'paint set',
            'play kitchen', 'toy cars', 'train set', 'LEGO sets',
            'bicycle', 'scooter', 'helmet', 'knee pads', 'sports equipment',
            'soccer ball', 'basketball', 'baseball glove', 'jump rope'
        ],
        'services': [
            'daycare tuition', 'preschool fees', 'nursery admission',
            'kindergarten registration', 'after school program',
            'summer camp', 'swimming lessons', 'music lessons',
            'dance classes', 'karate classes', 'art classes',
            'tutoring services', 'speech therapy', 'occupational therapy',
            'pediatric consultation', 'birthday party venue',
            'children\'s haircut', 'kids activities', 'playgroup'
        ],
        'brands': [
            'Pampers', 'Huggies', 'Luvs', 'Seventh Generation',
            'Enfamil', 'Similac', 'Gerber', 'Earth\'s Best',
            'Johnson & Johnson', 'Mustela', 'Aveeno Baby', 'Burt\'s Bees Baby'
        ]
    },

    'electronics_technology': {
        'merchants': [
            'Best Buy', 'Apple Store', 'Microsoft Store', 'B&H Photo',
            'Micro Center', 'Newegg', 'Amazon Electronics', 'Crutchfield',
            'Fry\'s Electronics', 'Staples', 'Office Depot', 'Office Max',
            'RadioShack', 'GameStop', 'Target Electronics', 'Walmart Electronics',
            'Costco Electronics', 'Sam\'s Club Electronics', 'Dell',
            'HP Store', 'Lenovo', 'ASUS', 'Acer', 'Sony Store',
            'Samsung Store', 'LG Electronics', 'Verizon', 'AT&T',
            'T-Mobile', 'Sprint', 'Reliance Digital', 'Croma',
            'Vijay Sales', 'Poorvika', 'Sangeetha Mobiles'
        ],
        'items': [
            'laptop', 'desktop computer', 'monitor', 'keyboard', 'mouse',
            'webcam', 'microphone', 'speakers', 'headphones', 'earbuds',
            'gaming headset', 'iPhone', 'Samsung phone', 'Android phone',
            'smartphone', 'tablet', 'iPad', 'Apple Watch', 'smartwatch',
            'fitness tracker', 'printer', 'scanner', 'router', 'modem',
            'network switch', 'ethernet cable', 'USB cable', 'HDMI cable',
            'external hard drive', 'SSD', 'USB flash drive', 'memory card',
            'graphics card', 'CPU processor', 'motherboard', 'RAM',
            'power supply', 'computer case', 'cooling fan', 'thermal paste',
            'laptop charger', 'phone charger', 'power bank', 'battery pack',
            'camera', 'DSLR', 'lens', 'tripod', 'camera bag',
            'gaming console', 'PlayStation', 'Xbox', 'Nintendo Switch',
            'gaming controller', 'VR headset', 'TV', 'soundbar',
            'streaming device', 'Chromecast', 'Fire TV', 'Roku',
            'smart home hub', 'smart bulb', 'security camera', 'doorbell camera'
        ],
        'services': [
            'laptop repair', 'screen replacement', 'battery replacement',
            'data recovery', 'virus removal', 'software installation',
            'tech support', 'Geek Squad service', 'phone activation',
            'device setup', 'warranty extension', 'AppleCare',
            'Dell warranty', 'HP support', 'tech consultation'
        ],
        'brands': [
            'Apple', 'Dell', 'HP', 'Lenovo', 'ASUS', 'Acer', 'MSI',
            'Samsung', 'LG', 'Sony', 'Canon', 'Nikon', 'Logitech',
            'Corsair', 'Razer', 'SteelSeries', 'Bose', 'JBL', 'Beats',
            'Anker', 'Belkin', 'Samsung', 'Western Digital', 'Seagate'
        ]
    },

    'subscriptions_memberships': {
        'services': [
            # Streaming
            'Netflix', 'Disney+ Hotstar', 'Amazon Prime Video', 'Hulu',
            'HBO Max', 'Apple TV+', 'Paramount+', 'Peacock', 'Discovery+',
            'YouTube Premium', 'YouTube TV', 'Sling TV', 'FuboTV',

            # Music
            'Spotify Premium', 'Apple Music', 'Amazon Music Unlimited',
            'YouTube Music', 'Tidal', 'Pandora Plus', 'SoundCloud Go',

            # Cloud Storage
            'iCloud Storage', 'Google One', 'Dropbox Plus', 'OneDrive',
            'pCloud', 'Sync.com', 'Box', 'Backblaze',

            # Software
            'Adobe Creative Cloud', 'Microsoft 365', 'Office 365',
            'Grammarly Premium', 'Canva Pro', 'Notion Plus',
            'Evernote Premium', 'LastPass Premium', '1Password',
            'NordVPN', 'ExpressVPN', 'Surfshark', 'ProtonVPN',

            # Professional
            'LinkedIn Premium', 'Medium Membership', 'Substack',
            'Patreon', 'GitHub Pro', 'Slack Premium', 'Zoom Pro',
            'Webex Premium', 'Asana Premium', 'Trello Premium',

            # News & Reading
            'New York Times Digital', 'Wall Street Journal', 'Washington Post',
            'The Economist', 'Bloomberg', 'Financial Times', 'The Atlantic',
            'Kindle Unlimited', 'Audible', 'Scribd', 'Blinkist',

            # Fitness
            'Peloton Membership', 'Apple Fitness+', 'Beachbody On Demand',
            'Daily Burn', 'Aaptiv', 'Fitbit Premium', 'Strava Summit',

            # Gaming
            'PlayStation Plus', 'Xbox Game Pass', 'Nintendo Switch Online',
            'EA Play', 'Ubisoft+', 'Discord Nitro', 'Twitch Turbo',

            # Learning
            'Coursera Plus', 'Udemy Business', 'LinkedIn Learning',
            'Skillshare Premium', 'MasterClass', 'Duolingo Plus',
            'Babbel', 'Rosetta Stone',

            # Other
            'Amazon Prime', 'Costco Membership', 'Sam\'s Club Plus',
            'AAA Membership', 'Gym Membership 24 Hour Fitness',
            'Planet Fitness Black Card', 'LA Fitness', 'Equinox',
            'ClassPass', 'Headspace', 'Calm', 'BetterHelp'
        ],
        'descriptors': [
            'monthly subscription', 'annual membership', 'yearly renewal',
            'premium plan', 'family plan', 'student plan', 'pro subscription',
            'plus membership', 'unlimited plan', 'recurring payment',
            'auto-renewal', 'membership fee', 'subscription renewal'
        ]
    }
}

# Transaction patterns
PAYMENT_METHODS = ['UPI', 'NEFT', 'IMPS', 'Debit Card', 'Credit Card', 'Online Payment', 'Payment to', 'Transfer to']
LOCATIONS = ['India', 'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Pune', 'Kolkata', 'Ahmedabad']
DESCRIPTORS = ['Purchase', 'Payment', 'Transaction', 'Order', 'Bill', 'Invoice', 'Charge']

def generate_transaction_id():
    """Generate realistic transaction ID."""
    return f"TXN{random.randint(100000, 999999)}"

def generate_date():
    """Generate random date in last year."""
    days_ago = random.randint(0, 365)
    date = datetime.now() - timedelta(days=days_ago)
    return date.strftime('%d/%m')

def generate_amount():
    """Generate realistic amount."""
    return round(random.uniform(50, 5000), 2)

def generate_home_improvement_transaction():
    """Generate realistic home improvement transaction."""
    patterns = [
        lambda: f"{random.choice(CATEGORY_DATA['home_improvement']['merchants'])} {random.choice(CATEGORY_DATA['home_improvement']['items'])}",
        lambda: f"{random.choice(PAYMENT_METHODS)} - {random.choice(CATEGORY_DATA['home_improvement']['merchants'])}",
        lambda: f"{random.choice(CATEGORY_DATA['home_improvement']['merchants'])} {random.choice(CATEGORY_DATA['home_improvement']['items'])} purchase",
        lambda: f"Payment to {random.choice(CATEGORY_DATA['home_improvement']['merchants'])} for {random.choice(CATEGORY_DATA['home_improvement']['items'])}",
        lambda: f"{random.choice(CATEGORY_DATA['home_improvement']['services'])} {generate_date()}",
        lambda: f"{random.choice(CATEGORY_DATA['home_improvement']['merchants'])} - {random.choice(CATEGORY_DATA['home_improvement']['items'])} {generate_transaction_id()}",
        lambda: f"Online payment {random.choice(CATEGORY_DATA['home_improvement']['merchants'])}",
        lambda: f"{random.choice(CATEGORY_DATA['home_improvement']['items'])} from {random.choice(CATEGORY_DATA['home_improvement']['merchants'])}",
        lambda: f"{random.choice(CATEGORY_DATA['home_improvement']['merchants'])} {random.choice(LOCATIONS)}",
        lambda: f"{random.choice(CATEGORY_DATA['home_improvement']['services'])} - {generate_transaction_id()}",
    ]
    return random.choice(patterns)()

def generate_pets_transaction():
    """Generate realistic pets transaction."""
    patterns = [
        lambda: f"{random.choice(CATEGORY_DATA['pets']['merchants'])} {random.choice(CATEGORY_DATA['pets']['items'])}",
        lambda: f"{random.choice(CATEGORY_DATA['pets']['brands'])} {random.choice(CATEGORY_DATA['pets']['items'])}",
        lambda: f"{random.choice(PAYMENT_METHODS)} - {random.choice(CATEGORY_DATA['pets']['merchants'])}",
        lambda: f"{random.choice(CATEGORY_DATA['pets']['services'])} at {random.choice(CATEGORY_DATA['pets']['merchants'])}",
        lambda: f"Payment to {random.choice(CATEGORY_DATA['pets']['merchants'])}",
        lambda: f"{random.choice(CATEGORY_DATA['pets']['merchants'])} - {random.choice(CATEGORY_DATA['pets']['items'])} {generate_transaction_id()}",
        lambda: f"{random.choice(CATEGORY_DATA['pets']['services'])} {generate_date()}",
        lambda: f"Chewy.com {random.choice(CATEGORY_DATA['pets']['items'])} auto-ship",
        lambda: f"{random.choice(CATEGORY_DATA['pets']['merchants'])} online order",
        lambda: f"{random.choice(CATEGORY_DATA['pets']['services'])} - {generate_transaction_id()}",
    ]
    return random.choice(patterns)()

def generate_kids_family_transaction():
    """Generate realistic kids/family transaction."""
    patterns = [
        lambda: f"{random.choice(CATEGORY_DATA['kids_family']['merchants'])} {random.choice(CATEGORY_DATA['kids_family']['items'])}",
        lambda: f"{random.choice(CATEGORY_DATA['kids_family']['brands'])} {random.choice(CATEGORY_DATA['kids_family']['items'])}",
        lambda: f"{random.choice(PAYMENT_METHODS)} - {random.choice(CATEGORY_DATA['kids_family']['merchants'])}",
        lambda: f"{random.choice(CATEGORY_DATA['kids_family']['services'])} - {generate_date()}",
        lambda: f"Payment to {random.choice(CATEGORY_DATA['kids_family']['merchants'])}",
        lambda: f"{random.choice(CATEGORY_DATA['kids_family']['merchants'])} - {random.choice(CATEGORY_DATA['kids_family']['items'])} {generate_transaction_id()}",
        lambda: f"{random.choice(CATEGORY_DATA['kids_family']['services'])} {generate_transaction_id()}",
        lambda: f"{random.choice(CATEGORY_DATA['kids_family']['merchants'])} online purchase",
        lambda: f"{random.choice(CATEGORY_DATA['kids_family']['items'])} from {random.choice(CATEGORY_DATA['kids_family']['merchants'])}",
        lambda: f"{random.choice(CATEGORY_DATA['kids_family']['merchants'])} {random.choice(LOCATIONS)}",
    ]
    return random.choice(patterns)()

def generate_electronics_transaction():
    """Generate realistic electronics transaction."""
    patterns = [
        lambda: f"{random.choice(CATEGORY_DATA['electronics_technology']['merchants'])} {random.choice(CATEGORY_DATA['electronics_technology']['items'])}",
        lambda: f"{random.choice(CATEGORY_DATA['electronics_technology']['brands'])} {random.choice(CATEGORY_DATA['electronics_technology']['items'])}",
        lambda: f"{random.choice(PAYMENT_METHODS)} - {random.choice(CATEGORY_DATA['electronics_technology']['merchants'])}",
        lambda: f"{random.choice(CATEGORY_DATA['electronics_technology']['items'])} purchase at {random.choice(CATEGORY_DATA['electronics_technology']['merchants'])}",
        lambda: f"Payment to {random.choice(CATEGORY_DATA['electronics_technology']['merchants'])}",
        lambda: f"{random.choice(CATEGORY_DATA['electronics_technology']['merchants'])} - {random.choice(CATEGORY_DATA['electronics_technology']['items'])} {generate_transaction_id()}",
        lambda: f"{random.choice(CATEGORY_DATA['electronics_technology']['services'])} {generate_date()}",
        lambda: f"{random.choice(CATEGORY_DATA['electronics_technology']['merchants'])} online order",
        lambda: f"{random.choice(CATEGORY_DATA['electronics_technology']['items'])} from {random.choice(CATEGORY_DATA['electronics_technology']['merchants'])}",
        lambda: f"{random.choice(CATEGORY_DATA['electronics_technology']['brands'])} Store {random.choice(LOCATIONS)}",
    ]
    return random.choice(patterns)()

def generate_subscription_transaction():
    """Generate realistic subscription transaction."""
    service = random.choice(CATEGORY_DATA['subscriptions_memberships']['services'])
    patterns = [
        lambda: f"{service} {random.choice(CATEGORY_DATA['subscriptions_memberships']['descriptors'])}",
        lambda: f"{random.choice(PAYMENT_METHODS)} - {service}",
        lambda: f"{service} - {random.choice(CATEGORY_DATA['subscriptions_memberships']['descriptors'])}",
        lambda: f"Payment to {service}",
        lambda: f"{service} {generate_transaction_id()}",
        lambda: f"{service} auto-renewal",
        lambda: f"Recurring payment - {service}",
        lambda: f"{service} subscription fee",
        lambda: f"{service} - monthly charge",
        lambda: f"{service} {generate_date()}",
    ]
    return random.choice(patterns)()

def generate_realistic_data(category, num_samples):
    """Generate realistic training data for a category."""
    generators = {
        'home_improvement': generate_home_improvement_transaction,
        'pets': generate_pets_transaction,
        'kids_family': generate_kids_family_transaction,
        'electronics_technology': generate_electronics_transaction,
        'subscriptions_memberships': generate_subscription_transaction
    }

    data = []
    generator = generators[category]

    for _ in range(num_samples):
        text = generator()
        data.append({
            'text': text,
            'category': category
        })

    return data

def main():
    """Generate realistic data for all weak categories."""
    weak_categories = [
        'home_improvement',
        'pets',
        'kids_family',
        'electronics_technology',
        'subscriptions_memberships'
    ]

    # Generate 3000 samples per category
    samples_per_category = 3000

    for category in weak_categories:
        print(f"\nGenerating {samples_per_category} realistic samples for {category}...")

        data = generate_realistic_data(category, samples_per_category)

        # Split 80/20 train/test
        train_size = int(samples_per_category * 0.8)
        train_data = data[:train_size]
        test_data = data[train_size:]

        # Save to files
        train_file = f'data/improved_weak_categories/{category}_train.jsonl'
        test_file = f'data/improved_weak_categories/{category}_test.jsonl'

        with open(train_file, 'w') as f:
            for item in train_data:
                f.write(json.dumps(item) + '\n')

        with open(test_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')

        print(f"  ✓ Generated {len(train_data)} training samples")
        print(f"  ✓ Generated {len(test_data)} test samples")
        print(f"  ✓ Saved to {train_file} and {test_file}")

        # Show samples
        print(f"\n  Sample transactions:")
        for i, sample in enumerate(train_data[:5]):
            print(f"    {i+1}. {sample['text']}")

    print(f"\n{'='*80}")
    print("REALISTIC DATA GENERATION COMPLETE!")
    print(f"{'='*80}")
    print(f"Total samples generated: {len(weak_categories) * samples_per_category}")
    print(f"Categories improved: {', '.join(weak_categories)}")

if __name__ == '__main__':
    main()
