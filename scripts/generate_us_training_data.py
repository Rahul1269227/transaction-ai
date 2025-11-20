#!/usr/bin/env python3
"""
Generate US Merchant Training Data
Creates realistic US transaction patterns to balance training data
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict

# US Merchant patterns by category
US_MERCHANTS = {
    "shopping": [
        ("AMAZON.COM*{ref}", "AMAZON ORDER #{ref}", "Amazon.com", "AMZN*{ref}"),
        ("WALMART SUPERCENTER #{store}", "WALMART STORE #{store}", "WALMART*{store}", "WAL-MART #{store}"),
        ("TARGET T-{store}", "TARGET STORE #{store}", "TARGET*{store}", "TGT #{store}"),
        ("BEST BUY #{store}", "BESTBUY.COM", "BEST BUY*{ref}", "BBY #{store}"),
        ("COSTCO WHSE #{store}", "COSTCO WHOLESALE #{store}", "COSTCO*{store}"),
        ("HOME DEPOT #{store}", "HOMEDEPOT.COM", "HOME DEPOT*{ref}"),
        ("LOWES #{store}", "LOWE'S #{store}", "LOWES*{store}"),
        ("KOHLS #{store}", "KOHL'S DEPT STORE", "KOHLS*{store}"),
        ("MACYS #{store}", "MACY'S", "MACYS*{store}"),
        ("NORDSTROM #{store}", "NORDSTROM.COM", "NORDSTROM*{ref}"),
        ("SEPHORA #{store}", "SEPHORA.COM", "SEPHORA*{ref}"),
        ("ULTA BEAUTY #{store}", "ULTA.COM", "ULTA*{store}"),
    ],
    "groceries": [
        ("WHOLE FOODS MARKET #{store}", "WHOLE FOODS #{store}", "WHOLEFOODS*{store}", "WFM #{store}"),
        ("TRADER JOES #{store}", "TRADER JOE'S #{store}", "TJS #{store}"),
        ("KROGER #{store}", "KROGER GROCERY", "KROGER*{store}"),
        ("SAFEWAY #{store}", "SAFEWAY STORE #{store}", "SAFEWAY*{store}"),
        ("PUBLIX #{store}", "PUBLIX SUPER MARKET", "PUBLIX*{store}"),
        ("ALDI #{store}", "ALDI GROCERY", "ALDI*{store}"),
        ("WEGMANS #{store}", "WEGMANS FOOD MARKETS", "WEGMANS*{store}"),
        ("SPROUTS #{store}", "SPROUTS FARMERS MARKET", "SPROUTS*{store}"),
    ],
    "food_dining": [
        ("STARBUCKS COFFEE #{store}", "STARBUCKS #{store}", "SBUX #{store}", "STARBUCKS*{store}"),
        ("MCDONALDS F{store}", "MC DONALD'S #{store}", "MCD #{store}", "MCDONALDS*{store}"),
        ("CHIPOTLE #{store}", "CHIPOTLE MEXICAN GRILL", "CHIPOTLE*{store}"),
        ("SUBWAY #{store}", "SUBWAY SANDWICHES", "SUBWAY*{store}"),
        ("PANERA BREAD #{store}", "PANERA #{store}", "PANERA*{store}"),
        ("CHICK-FIL-A #{store}", "CHICKFILA #{store}", "CFA #{store}"),
        ("TACO BELL #{store}", "TACOBELL #{store}", "TACO BELL*{store}"),
        ("DOMINOS PIZZA #{store}", "DOMINO'S #{store}", "DOMINOS*{store}"),
        ("PIZZA HUT #{store}", "PIZZAHUT #{store}", "PIZZA HUT*{store}"),
        ("DUNKIN #{store}", "DUNKIN DONUTS", "DUNKIN'*{store}"),
        ("BURGER KING #{store}", "BK #{store}", "BURGER KING*{store}"),
        ("WENDYS #{store}", "WENDY'S #{store}", "WENDYS*{store}"),
        ("DOORDASH*", "DOORDASH*{merchant}", "DD*{merchant}"),
        ("UBEREATS*", "UBER EATS*{merchant}", "UBER*EATS"),
        ("GRUBHUB*", "GRUBHUB*{merchant}", "GH*{merchant}"),
        ("POSTMATES*", "POSTMATES*{merchant}", "PM*{merchant}"),
    ],
    "fuel": [
        ("SHELL OIL {ref}", "SHELL GAS STATION", "SHELL*{store}"),
        ("CHEVRON {ref}", "CHEVRON SERVICE STATION", "CHEVRON*{store}"),
        ("EXXON {ref}", "EXXONMOBIL {store}", "EXXON*{store}"),
        ("BP {ref}", "BP GAS STATION", "BP*{store}"),
        ("MOBIL {ref}", "MOBIL GAS", "MOBIL*{store}"),
        ("TEXACO {ref}", "TEXACO STATION", "TEXACO*{store}"),
        ("ARCO {ref}", "ARCO AM/PM", "ARCO*{store}"),
        ("VALERO {ref}", "VALERO ENERGY", "VALERO*{store}"),
        ("CIRCLE K {ref}", "CIRCLE K STORES", "CIRCLEK*{store}"),
        ("7-ELEVEN {ref}", "7-11 #{store}", "7ELEVEN*{store}"),
    ],
    "transport": [
        ("UBER *TRIP", "UBER *RIDE", "UBER TECHNOLOGIES", "UBER*{ref}"),
        ("LYFT *RIDE", "LYFT INC", "LYFT*{ref}"),
        ("NYC PARKING METER #{ref}", "PARKING METER {ref}", "PARK MOBILE {ref}"),
        ("ENTERPRISE RENT-A-CAR", "ENTERPRISE RENTACAR", "ENTERPRISE*{ref}"),
        ("HERTZ RENT A CAR", "HERTZ RAC", "HERTZ*{ref}"),
        ("AVIS RENT A CAR", "AVIS CAR RENTAL", "AVIS*{ref}"),
    ],
    "travel": [
        ("DELTA AIR LINES", "DELTA AIRLINES", "DELTA*{ref}", "DAL*{ref}"),
        ("AMERICAN AIRLINES", "AMERICAN AIR", "AA.COM", "AMR*{ref}"),
        ("UNITED AIRLINES", "UNITED AIR", "UNITED.COM", "UAL*{ref}"),
        ("SOUTHWEST AIRLINES", "SOUTHWEST AIR", "SWA*{ref}"),
        ("JETBLUE AIRWAYS", "JETBLUE", "JETBLUE*{ref}"),
        ("MARRIOTT HOTEL", "MARRIOTT.COM", "MARRIOTT*{ref}"),
        ("HILTON HOTELS", "HILTON.COM", "HILTON*{ref}"),
        ("HYATT HOTELS", "HYATT.COM", "HYATT*{ref}"),
        ("AIRBNB*", "AIRBNB.COM", "AIRBNB INC"),
    ],
    "subscriptions_memberships": [
        ("NETFLIX.COM", "NETFLIX MONTHLY", "NETFLIX SUBSCRIPTION", "NETFLIX*"),
        ("SPOTIFY USA", "SPOTIFY PREMIUM", "SPOTIFY.COM", "SPOTIFY*"),
        ("DISNEY+", "DISNEY PLUS", "DISNEYPLUS.COM"),
        ("HULU.COM", "HULU SUBSCRIPTION", "HULU*"),
        ("HBO MAX", "HBOMAX.COM", "HBO*MAX"),
        ("APPLE TV+", "APPLE TV PLUS", "APPLE.COM/BILL"),
        ("AMAZON PRIME", "PRIME VIDEO", "AMAZON PRIME VIDEO"),
        ("YOUTUBE PREMIUM", "YT PREMIUM", "YOUTUBE.COM"),
        ("APPLE MUSIC", "APPLE.COM/BILL MUSIC"),
        ("AUDIBLE", "AUDIBLE.COM", "AUDIBLE MEMBERSHIP"),
        ("KINDLE UNLIMITED", "KINDLE.COM", "AMAZON KINDLE"),
        ("COSTCO MEMBERSHIP", "COSTCO ANNUAL FEE", "COSTCO MEMBERSHIP FEE"),
        ("SAMS CLUB MEMBERSHIP", "SAM'S CLUB FEE", "SAMSCLUB MEMBERSHIP"),
        ("24 HOUR FITNESS", "24HR FITNESS", "24 HOUR FITNESS GYM"),
        ("PLANET FITNESS", "PLANET FITNESS GYM", "PLANETFITNESS*"),
        ("LA FITNESS", "LA FITNESS GYM", "LAFITNESS*"),
        ("PELOTON", "PELOTON MEMBERSHIP", "PELOTON.COM"),
    ],
    "bills": [
        ("AT&T *WIRELESS", "AT&T MOBILITY", "ATT*PAYMENT", "AT&T BILL"),
        ("VERIZON WIRELESS", "VERIZON AUTOPAY", "VERIZON*", "VZW*"),
        ("T-MOBILE", "T-MOBILE USA", "TMOBILE*", "T-MOBILE WIRELESS"),
        ("SPRINT", "SPRINT PCS", "SPRINT WIRELESS"),
        ("COMCAST CABLE", "COMCAST XFINITY", "COMCAST*", "XFINITY*"),
        ("SPECTRUM", "CHARTER SPECTRUM", "SPECTRUM CABLE"),
        ("COX COMMUNICATIONS", "COX CABLE", "COX*"),
        ("AT&T INTERNET", "AT&T U-VERSE", "ATT INTERNET"),
        ("DUKE ENERGY", "DUKE ENERGY BILL", "DUKE*"),
        ("PG&E", "PACIFIC GAS ELECTRIC", "PGE BILL", "PGANDE"),
        ("SOUTHERN CALIFORNIA EDISON", "SCE", "SOCAL EDISON"),
        ("WATER UTILITY", "WATER DISTRICT", "WATER BILL"),
    ],
    "health": [
        ("CVS/PHARMACY #{store}", "CVS PHARMACY", "CVS*{store}"),
        ("WALGREENS #{store}", "WALGREENS PHARMACY", "WAG*{store}"),
        ("RITE AID #{store}", "RITEAID PHARMACY", "RITEAID*{store}"),
        ("KAISER PERMANENTE", "KAISER HEALTH", "KAISER*"),
        ("LABCORP", "LABORATORY CORP", "LABCORP*"),
        ("QUEST DIAGNOSTICS", "QUEST LAB", "QUEST*"),
        ("DENTAL ASSOCIATES", "DENTAL CARE", "DENTIST OFFICE"),
        ("VISION CENTER", "EYE CARE CENTER", "OPTOMETRY"),
    ],
    "electronics_technology": [
        ("APPLE.COM/BILL", "APPLE STORE", "APPLE INC", "APPLE*"),
        ("MICROSOFT STORE", "MICROSOFT.COM", "MSFT*"),
        ("DELL.COM", "DELL INC", "DELL*"),
        ("HP STORE", "HP.COM", "HEWLETT PACKARD"),
        ("STEAM GAMES", "STEAMPOWERED.COM", "STEAM*"),
        ("GAMESTOP #{store}", "GAMESTOP.COM", "GME*{store}"),
        ("PLAYSTATION STORE", "PLAYSTATION NETWORK", "PSN*"),
        ("XBOX STORE", "MICROSOFT XBOX", "XBOX*"),
    ],
    "personal_care": [
        ("SALON", "HAIR SALON", "BEAUTY SALON"),
        ("SPA", "DAY SPA", "SPA SERVICES"),
        ("BARBER SHOP", "BARBERSHOP", "BARBER"),
        ("NAIL SALON", "NAILS", "NAIL SPA"),
        ("GYM", "FITNESS CENTER", "WORKOUT GYM"),
    ],
    "home_improvement": [
        ("IKEA #{store}", "IKEA FURNITURE", "IKEA*{store}"),
        ("BED BATH BEYOND", "BED BATH & BEYOND", "BEDBATH*"),
        ("POTTERY BARN", "POTTERY BARN.COM", "POTTERYBARN*"),
        ("WILLIAMS SONOMA", "WILLIAMS-SONOMA", "WSSONOMA*"),
        ("WAYFAIR.COM", "WAYFAIR INC", "WAYFAIR*"),
    ],
    "entertainment": [
        ("AMC THEATRES #{store}", "AMC THEATERS", "AMC*{store}"),
        ("REGAL CINEMAS", "REGAL THEATERS", "REGAL*"),
        ("CINEMARK", "CINEMARK THEATERS", "CINEMARK*"),
        ("TICKETMASTER", "TICKETMASTER.COM", "LIVENATION"),
    ],
    "transfers_upi": [
        ("VENMO *PAYMENT", "VENMO *TRANSFER", "VENMO*"),
        ("ZELLE TRANSFER", "ZELLE PAYMENT", "ZELLE*"),
        ("PAYPAL *TRANSFER", "PAYPAL PAYMENT", "PAYPAL*"),
        ("CASHAPP *", "CASH APP *", "CASH*APP"),
        ("APPLE CASH", "APPLE PAY CASH", "APPLE*CASH"),
        ("GOOGLE PAY", "GPAY *", "GOOGLEPAY*"),
        ("TRANSFER TO SAVINGS", "INTERNAL TRANSFER", "ACCOUNT TRANSFER"),
        ("WIRE TRANSFER", "WIRED FUNDS", "WIRE*"),
        ("ACH TRANSFER", "ACH PAYMENT", "ACH*"),
    ],
    "atm_cash": [
        ("ATM WITHDRAWAL {ref}", "ATM CASH {ref}", "ATM*{ref}"),
        ("CASH DEPOSIT ATM #{ref}", "ATM DEPOSIT {ref}"),
        ("BANK OF AMERICA ATM", "BOA ATM {ref}", "BOFA ATM*"),
        ("CHASE ATM", "CHASE BANK ATM", "CHASE*ATM"),
        ("WELLS FARGO ATM", "WF ATM", "WELLSFARGO*ATM"),
    ],
    "income_salary": [
        ("DIRECT DEPOSIT PAYROLL", "PAYROLL DEPOSIT", "SALARY DEPOSIT"),
        ("DIRECT DEP {company}", "DD {company}", "PAYROLL {company}"),
        ("DEPOSIT", "CASH DEPOSIT", "CHECK DEPOSIT"),
    ],
    "pets": [
        ("PETSMART #{store}", "PETSMART.COM", "PETSMART*{store}"),
        ("PETCO #{store}", "PETCO.COM", "PETCO*{store}"),
        ("CHEWY.COM", "CHEWY INC", "CHEWY*"),
        ("VET CLINIC", "VETERINARY HOSPITAL", "ANIMAL HOSPITAL"),
    ],
    "insurance": [
        ("STATE FARM INSURANCE", "STATE FARM", "STATEFARM*"),
        ("GEICO INSURANCE", "GEICO", "GEICO*"),
        ("PROGRESSIVE INSURANCE", "PROGRESSIVE", "PROGRESSIVE*"),
        ("ALLSTATE INSURANCE", "ALLSTATE", "ALLSTATE*"),
    ],
}

def generate_ref():
    """Generate random reference number"""
    return ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=random.randint(8, 12)))

def generate_store_number():
    """Generate random store number"""
    return str(random.randint(1000, 9999))

def generate_merchant_name(patterns: tuple, category: str) -> str:
    """Generate merchant name from pattern"""
    # patterns is a tuple of merchant patterns, pick one pattern from the tuple
    merchant_patterns = patterns  # This is one tuple of patterns for a merchant
    pattern = random.choice(merchant_patterns)

    # Replace placeholders safely
    try:
        return pattern.format(
            ref=generate_ref(),
            store=generate_store_number(),
            merchant=random.choice(['CHIPOTLE', 'PIZZA', 'BURGER', 'SUSHI', 'THAI']),
            company=random.choice(['ACME CORP', 'XYZ INC', 'ABC LLC', 'TECH CO'])
        )
    except KeyError:
        # If format fails, just return the pattern as-is
        return pattern

def generate_amount(category: str) -> float:
    """Generate realistic amount for category"""
    ranges = {
        "shopping": (20, 500),
        "groceries": (30, 200),
        "food_dining": (8, 100),
        "fuel": (30, 120),
        "transport": (10, 80),
        "travel": (100, 1500),
        "subscriptions_memberships": (5, 50),
        "bills": (50, 300),
        "health": (20, 500),
        "electronics_technology": (50, 2000),
        "personal_care": (20, 150),
        "home_improvement": (50, 500),
        "entertainment": (15, 150),
        "transfers_upi": (10, 5000),
        "atm_cash": (20, 500),
        "income_salary": (1000, 8000),
        "pets": (20, 200),
        "insurance": (100, 500),
    }
    min_amt, max_amt = ranges.get(category, (10, 500))
    return round(random.uniform(min_amt, max_amt), 2)

def generate_date():
    """Generate random date in the past year"""
    days_ago = random.randint(0, 365)
    date = datetime.now() - timedelta(days=days_ago)
    return date.strftime("%Y-%m-%d")

def generate_training_samples(category: str, merchant_list: List[tuple], count: int) -> List[Dict]:
    """Generate training samples for a category"""
    samples = []
    for _ in range(count):
        # Pick a random merchant from the list
        merchant_patterns = random.choice(merchant_list)
        text = generate_merchant_name(merchant_patterns, category)
        sample = {
            "text": text,
            "label": category,
            "category": category,
            "amount": generate_amount(category),
            "currency": "USD",
            "date": generate_date()
        }
        samples.append(sample)
    return samples

def main():
    """Generate US merchant training data"""

    # Target: 800 samples per category (balanced)
    samples_per_category = 800

    all_samples = []

    print("Generating US merchant training data...")
    print(f"Target: {samples_per_category} samples per category")
    print("=" * 60)

    for category, patterns in US_MERCHANTS.items():
        print(f"Generating {samples_per_category} samples for {category}...")
        samples = generate_training_samples(category, patterns, samples_per_category)
        all_samples.extend(samples)
        print(f"  ✓ Generated {len(samples)} samples")

    # Shuffle samples
    random.shuffle(all_samples)

    # Split into train (80%) and test (20%)
    split_idx = int(len(all_samples) * 0.8)
    train_samples = all_samples[:split_idx]
    test_samples = all_samples[split_idx:]

    # Write to files
    train_file = "data/us_merchants_train.jsonl"
    test_file = "data/us_merchants_test.jsonl"

    with open(train_file, 'w') as f:
        for sample in train_samples:
            f.write(json.dumps(sample) + '\n')

    with open(test_file, 'w') as f:
        for sample in test_samples:
            f.write(json.dumps(sample) + '\n')

    print("=" * 60)
    print(f"✓ Generated {len(train_samples)} training samples → {train_file}")
    print(f"✓ Generated {len(test_samples)} test samples → {test_file}")
    print(f"✓ Total: {len(all_samples)} samples")
    print()
    print("Category distribution:")
    for category in US_MERCHANTS.keys():
        count = sum(1 for s in all_samples if s['category'] == category)
        print(f"  {category}: {count}")

if __name__ == "__main__":
    main()
