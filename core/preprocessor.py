"""
Transaction Preprocessor
Intelligently extracts key information from structured JSON transactions
"""

import json
import re
from typing import Any, Dict, Optional, Tuple
from datetime import datetime


class TransactionPreprocessor:
    """
    Generic preprocessor that extracts meaningful transaction information
    from complex JSON structures or plain text
    """

    # Common field names for merchants (case-insensitive)
    MERCHANT_FIELDS = [
        'merchant_name', 'merchantname', 'merchant', 'name', 'store_name', 'storename',
        'store', 'business_name', 'businessname', 'seller', 'vendor',
        'payee_name', 'payeename', 'payee', 'recipient', 'display_name', 'displayname'
    ]

    # Common field names for amounts
    AMOUNT_FIELDS = [
        'amount', 'value', 'total', 'total_amount', 'totalamount',
        'transaction_amount', 'transactionamount', 'total_debited',
        'debited_amount', 'payment_amount', 'grand_total', 'grandtotal'
    ]

    # Common field names for transaction types/descriptions
    TYPE_FIELDS = [
        'transaction_type', 'transactiontype', 'type', 'description',
        'transaction_description', 'purpose', 'category', 'memo',
        'narration', 'remarks', 'note', 'reference_text'
    ]

    # Common field names for currency
    CURRENCY_FIELDS = ['currency', 'currency_code', 'currencycode']

    # Comprehensive Merchant Category Codes (MCC) mapping to transaction categories
    # Based on ISO 18245 standard and common banking MCCs
    MCC_MAPPING = {
        # Food & Dining (5812, 5814, 5813, 5811)
        '5812': 'food_dining',  # Restaurants
        '5814': 'food_dining',  # Fast Food
        '5813': 'food_dining',  # Drinking Places (Bars, Taverns)
        '5811': 'food_dining',  # Caterers

        # Groceries (5411, 5422, 5451, 5462, 5499)
        '5411': 'groceries',  # Grocery Stores, Supermarkets
        '5422': 'groceries',  # Freezer and Locker Meat Provisioners
        '5451': 'groceries',  # Dairy Products Stores
        '5462': 'groceries',  # Bakeries
        '5499': 'groceries',  # Miscellaneous Food Stores

        # Transport (4111, 4121, 4131, 4784, 4789, 7511, 7523)
        '4111': 'transport',  # Local/Suburban Commuter Passenger Transportation
        '4112': 'transport',  # Passenger Railways
        '4119': 'transport',  # Ambulance Services
        '4121': 'transport',  # Taxicabs and Limousines
        '4131': 'transport',  # Bus Lines
        '4784': 'transport',  # Tolls and Bridge Fees
        '4789': 'transport',  # Transportation Services
        '7511': 'transport',  # Truck Rentals
        '7523': 'transport',  # Parking Lots, Parking Meters, Garages
        '7549': 'transport',  # Towing Services

        # Travel (3000-3299, 4411, 4511, 7011, 7012, 7032, 7033)
        '3000': 'travel',  # Airlines (general)
        '3001': 'travel',  # American Airlines
        '3002': 'travel',  # Air Canada
        '3003': 'travel',  # Air France
        '3004': 'travel',  # Air India
        '3005': 'travel',  # British Airways
        '3006': 'travel',  # Emirates
        '3007': 'travel',  # Lufthansa
        '3008': 'travel',  # United Airlines
        '3009': 'travel',  # Delta Airlines
        '3010': 'travel',  # Qatar Airways
        '3050': 'travel',  # Low-cost carriers
        '3298': 'travel',  # Miscellaneous Airlines
        '4411': 'travel',  # Steamships and Cruise Lines
        '4511': 'travel',  # Airlines
        '4722': 'travel',  # Travel Agencies and Tour Operators
        '7011': 'travel',  # Hotels, Motels, Resorts
        '7012': 'travel',  # Timeshares
        '7032': 'travel',  # Sporting and Recreational Camps
        '7033': 'travel',  # Trailer Parks and Campgrounds

        # Fuel (5541, 5542, 5983)
        '5541': 'fuel',  # Service Stations (with or without ancillary services)
        '5542': 'fuel',  # Automated Fuel Dispensers
        '5983': 'fuel',  # Fuel Dealers (Non-Automotive)

        # Utilities (4816, 4821)
        '4816': 'Utilities',  # Computer Network/Information Services
        '4821': 'Utilities',  # Telegraph Services

        # Shopping (5200-5999, 5311, 5331, 5399, 5691, 5699, 5732, 5734, 5735, 5999)
        '5200': 'shopping',  # Home Supply Warehouse Stores
        '5211': 'shopping',  # Lumber and Building Materials Stores
        '5231': 'shopping',  # Glass, Paint, and Wallpaper Stores
        '5251': 'shopping',  # Hardware Stores
        '5261': 'shopping',  # Nurseries and Lawn and Garden Supply Stores
        '5271': 'shopping',  # Mobile Home Dealers
        '5300': 'shopping',  # Wholesale Clubs
        '5311': 'shopping',  # Department Stores
        '5331': 'shopping',  # Variety Stores
        '5399': 'shopping',  # Miscellaneous General Merchandise
        '5611': 'shopping',  # Men's and Boys' Clothing and Accessories Stores
        '5621': 'shopping',  # Women's Ready-to-Wear Stores
        '5631': 'shopping',  # Women's Accessory and Specialty Shops
        '5641': 'shopping',  # Children's and Infants' Wear Stores
        '5651': 'shopping',  # Family Clothing Stores
        '5655': 'shopping',  # Sports and Riding Apparel Stores
        '5661': 'shopping',  # Shoe Stores
        '5681': 'shopping',  # Furriers and Fur Shops
        '5691': 'shopping',  # Men's and Women's Clothing Stores
        '5697': 'shopping',  # Tailors, Seamstresses, Mending, and Alterations
        '5698': 'shopping',  # Wig and Toupee Stores
        '5699': 'shopping',  # Miscellaneous Apparel and Accessory Shops
        '5712': 'shopping',  # Furniture, Home Furnishings, and Equipment Stores
        '5713': 'shopping',  # Floor Covering Stores
        '5714': 'shopping',  # Drapery, Window Covering, and Upholstery Stores
        '5718': 'shopping',  # Fireplace, Fireplace Screens, and Accessories Stores
        '5719': 'shopping',  # Miscellaneous Home Furnishing Specialty Stores
        '5722': 'shopping',  # Household Appliance Stores
        '5732': 'shopping',  # Electronics Stores
        '5733': 'shopping',  # Music Stores
        '5734': 'shopping',  # Computer Software Stores
        '5735': 'shopping',  # Record Stores
        '5815': 'shopping',  # Digital Goods Media (Books, Movies, Music)
        '5921': 'shopping',  # Package Stores (Beer, Wine, and Liquor)
        '5931': 'shopping',  # Used Merchandise and Secondhand Stores
        '5932': 'shopping',  # Antique Shops
        '5933': 'shopping',  # Pawn Shops
        '5935': 'shopping',  # Wrecking and Salvage Yards
        '5937': 'shopping',  # Antique Reproduction Stores
        '5940': 'shopping',  # Bicycle Shops
        '5941': 'shopping',  # Sporting Goods Stores
        '5942': 'shopping',  # Book Stores
        '5943': 'shopping',  # Stationery, Office, and School Supply Stores
        '5944': 'shopping',  # Jewelry, Watch, Clock, and Silverware Stores
        '5945': 'shopping',  # Hobby, Toy, and Game Shops
        '5946': 'shopping',  # Camera and Photographic Supply Stores
        '5947': 'shopping',  # Gift, Card, Novelty, and Souvenir Shops
        '5948': 'shopping',  # Luggage and Leather Goods Stores
        '5949': 'shopping',  # Sewing, Needlework, Fabric, and Piece Goods Stores
        '5950': 'shopping',  # Glassware and Crystal Stores
        '5960': 'shopping',  # Direct Marketing - Insurance Services
        '5970': 'shopping',  # Artist Supply and Craft Shops
        '5971': 'shopping',  # Art Dealers and Galleries
        '5972': 'shopping',  # Stamp and Coin Stores
        '5973': 'shopping',  # Religious Goods Stores
        '5977': 'shopping',  # Cosmetics Stores
        '5978': 'shopping',  # Typewriter Stores
        '5992': 'shopping',  # Florists
        '5993': 'shopping',  # Cigar Stores and Stands
        '5994': 'shopping',  # News Dealers and Newsstands
        '5995': 'shopping',  # Pet Shops, Pet Food, and Supplies
        '5996': 'shopping',  # Swimming Pools
        '5997': 'shopping',  # Electric Razor Stores
        '5998': 'shopping',  # Tent and Awning Shops
        '5999': 'shopping',  # Miscellaneous and Specialty Retail Stores

        # Entertainment (7832, 7841, 7922, 7929, 7991, 7992, 7993, 7994, 7996, 7997, 7998, 7999)
        '7832': 'entertainment',  # Motion Picture Theaters
        '7841': 'entertainment',  # Video Rental Stores
        '7922': 'entertainment',  # Theatrical Producers and Ticket Agencies
        '7929': 'entertainment',  # Bands, Orchestras, and Miscellaneous Entertainers
        '7932': 'entertainment',  # Billiard and Pool Establishments
        '7933': 'entertainment',  # Bowling Alleys
        '7991': 'entertainment',  # Tourist Attractions and Exhibits
        '7992': 'entertainment',  # Public Golf Courses
        '7993': 'entertainment',  # Video Amusement Game Supplies
        '7994': 'entertainment',  # Video Game Arcades
        '7995': 'entertainment',  # Betting (including Lottery Tickets, Casino Gaming Chips)
        '7996': 'entertainment',  # Amusement Parks, Carnivals, Circuses, Fortune Tellers
        '7997': 'entertainment',  # Membership Clubs (Sports, Recreation, Athletic)
        '7998': 'entertainment',  # Aquariums, Seaquariums, Dolphinariums
        '7999': 'entertainment',  # Recreation Services
        '5816': 'entertainment',  # Digital Goods - Games

        # Health (5912, 5975, 5976, 8011, 8021, 8031, 8041, 8042, 8043, 8049, 8050, 8062, 8071, 8099)
        '5912': 'health',  # Drug Stores and Pharmacies
        '5975': 'health',  # Hearing Aids - Sales, Service, and Supply
        '5976': 'health',  # Orthopedic Goods - Prosthetic Devices
        '8011': 'health',  # Doctors and Physicians
        '8021': 'health',  # Dentists and Orthodontists
        '8031': 'health',  # Osteopaths
        '8041': 'health',  # Chiropractors
        '8042': 'health',  # Optometrists and Ophthalmologists
        '8043': 'health',  # Opticians, Optical Goods, and Eyeglasses
        '8049': 'health',  # Podiatrists and Chiropodists
        '8050': 'health',  # Nursing and Personal Care Facilities
        '8062': 'health',  # Hospitals
        '8071': 'health',  # Medical and Dental Laboratories
        '8099': 'health',  # Medical Services and Health Practitioners

        # Education (8211, 8220, 8241, 8244, 8249, 8299, 5192, 5942)
        '8211': 'education',  # Elementary and Secondary Schools
        '8220': 'education',  # Colleges, Universities, Professional Schools, and Junior Colleges
        '8241': 'education',  # Correspondence Schools
        '8244': 'education',  # Business and Secretarial Schools
        '8249': 'education',  # Vocational and Trade Schools
        '8299': 'education',  # Educational Services
        '5192': 'education',  # Books, Periodicals, and Newspapers

        # Fees & Charges (6012, 6051, 6540, 9211, 9222, 9223, 9311)
        '6012': 'fees_charges',  # Financial Institutions - Merchandise and Services
        '6051': 'fees_charges',  # Non-Financial Institutions - Foreign Currency, Money Orders
        '6540': 'fees_charges',  # Non-Financial Institutions - Stored Value Card Purchase/Load
        '9211': 'fees_charges',  # Court Costs, Including Alimony and Child Support
        '9222': 'fees_charges',  # Fines
        '9223': 'fees_charges',  # Bail and Bond Payments
        '9311': 'fees_charges',  # Tax Payments

        # Income/Salary (6538, 6540)
        '6538': 'income_salary',  # Pay Anyone - Merchant Funded

        # Transfers/UPI (6536, 6537, 4829)
        '6536': 'transfers_upi',  # MoneySend Intracountry
        '6537': 'transfers_upi',  # MoneySend Intercountry
        '4829': 'transfers_upi',  # Wire Transfers and Money Orders

        # ATM/Cash (6010, 6011, 6050)
        '6010': 'atm_cash',  # Manual Cash Disbursements
        '6011': 'atm_cash',  # Automated Cash Disbursements (ATM)
        '6050': 'atm_cash',  # Quasi Cash

        # Investments (6211, 6300, 6381, 6399)
        '6211': 'investments',  # Security Brokers/Dealers
        '6300': 'investments',  # Insurance Underwriting, Premiums
        '6381': 'investments',  # Insurance - Premiums
        '6399': 'investments',  # Insurance - Not Elsewhere Classified

        # Bills (4814, 4899, 4900)
        '4814': 'bills',  # Telecommunication Services
        '4899': 'bills',  # Cable, Satellite, and Other Pay Television and Radio
        '4900': 'bills',  # Utilities - Electric, Gas, Water, Sanitary

        # Rent (6513)
        '6513': 'rent',  # Real Estate Agents and Managers - Rentals

        # Personal Care & Services (5977, 7230, 7261, 7273, 7277, 7278, 7296, 7297, 7298)
        '5977': 'shopping',  # Cosmetic Stores
        '7230': 'shopping',  # Beauty and Barber Shops
        '7261': 'shopping',  # Funeral Services and Crematories
        '7273': 'shopping',  # Dating and Escort Services
        '7276': 'shopping',  # Tax Preparation Services
        '7277': 'shopping',  # Counseling Services - Debt, Marriage, Personal
        '7278': 'shopping',  # Buying and Shopping Services and Clubs
        '7296': 'shopping',  # Clothing Rental
        '7297': 'shopping',  # Massage Parlors
        '7298': 'shopping',  # Health and Beauty Spas

        # Auto Services (5531, 5532, 5533, 5571, 5511, 7534, 7535, 7538, 7542)
        '5511': 'shopping',  # Automobile and Truck Dealers (New and Used)
        '5521': 'shopping',  # Automobile and Truck Dealers (Used Only)
        '5531': 'shopping',  # Auto and Home Supply Stores
        '5532': 'shopping',  # Automotive Tire Stores
        '5533': 'shopping',  # Automotive Parts and Accessories Stores
        '5571': 'shopping',  # Motorcycle Dealers
        '7531': 'shopping',  # Auto Body Repair Shops
        '7534': 'shopping',  # Tire Retreading and Repair Shops
        '7535': 'shopping',  # Auto Paint Shops
        '7538': 'shopping',  # Auto Service Shops (Non-Dealer)
        '7542': 'shopping',  # Car Washes
        '7549': 'transport',  # Towing Services
    }

    def __init__(self):
        pass

    def preprocess(self, text: str) -> str:
        """
        Main preprocessing function that handles both JSON and plain text

        Args:
            text: Raw transaction text (could be JSON or plain text)

        Returns:
            Cleaned, concise transaction description
        """
        # Try to parse as JSON
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return self._extract_from_json(data)
        except (json.JSONDecodeError, ValueError):
            # Not JSON, return as-is (might be plain text)
            pass

        # If not JSON or extraction failed, return original (cleaned)
        return self._clean_text(text)

    def preprocess_with_fields(self, text: str) -> Tuple[str, Optional[float], Optional[str], Optional[str], Optional[str]]:
        """
        Enhanced preprocessing that extracts both cleaned text and structured fields

        Args:
            text: Raw transaction text (could be JSON or plain text)

        Returns:
            Tuple of (cleaned_text, amount, date, currency, merchant)
        """
        # Try to parse as JSON
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                cleaned_text = self._extract_from_json(data)
                amount = self._extract_amount_from_json(data)
                date = self._extract_date_from_json(data)
                currency = self._find_currency(data) or "INR"
                merchant = self._find_merchant(data)
                return (cleaned_text, amount, date, currency, merchant)
        except (json.JSONDecodeError, ValueError):
            # Not JSON, return as-is (might be plain text)
            pass

        # If not JSON or extraction failed, return original (cleaned)
        return (self._clean_text(text), None, None, "INR", None)

    def _extract_from_json(self, data: Dict[str, Any]) -> str:
        """
        Extract key transaction information from JSON structure

        Strategy:
        1. Find merchant/vendor name
        2. Find transaction type/description
        3. Find amount and currency
        4. Combine into concise description
        """
        parts = []

        # Extract merchant name
        merchant = self._find_merchant(data)
        if merchant:
            parts.append(merchant)

        # Extract transaction type/description
        txn_type = self._find_transaction_type(data)
        if txn_type:
            # Skip if it's generic like "SUCCESS" or just repeats merchant
            if txn_type.upper() not in ['SUCCESS', 'COMPLETED', 'APPROVED']:
                if not merchant or txn_type.lower() not in merchant.lower():
                    parts.append(txn_type)

        # Extract merchant category code (MCC)
        # Note: MCC is now used by dedicated MCC classifier, not appended to text
        # to avoid influencing other classifiers

        # Extract amount
        amount = self._find_amount(data)
        currency = self._find_currency(data)
        if amount:
            amount_str = f"{currency} {amount}" if currency else f"Rs {amount}"
            parts.append(amount_str)

        # Combine parts
        if parts:
            result = ' '.join(parts)
            # Limit length to avoid timeout
            if len(result) > 500:
                result = result[:497] + "..."
            return result

        # Fallback: convert to compact JSON string
        return self._json_to_compact_text(data)

    def _find_field(self, data: Dict[str, Any], field_names: list, depth: int = 3, prefer_longer: bool = True) -> Optional[str]:
        """
        Recursively search for a field in nested JSON structure

        Args:
            data: JSON object
            field_names: List of possible field names (case-insensitive)
            depth: Maximum recursion depth
            prefer_longer: If True, prefer longer string values (e.g., names over IDs)

        Returns:
            Field value as string, or None if not found
        """
        if depth <= 0:
            return None

        candidates = []

        # Check current level
        for key, value in data.items():
            key_lower = key.lower().replace('_', '').replace('-', '')

            for field_name in field_names:
                field_name_clean = field_name.lower().replace('_', '').replace('-', '')
                if key_lower == field_name_clean or field_name_clean in key_lower:
                    if isinstance(value, (str, int, float)):
                        candidates.append(str(value))
                    elif isinstance(value, dict) and 'value' in value:
                        # Handle nested value objects like {"value": 2000, "currency": "INR"}
                        candidates.append(str(value.get('value', '')))

        # If we found candidates at this level, return the best one
        if candidates:
            if prefer_longer:
                # Prefer longer strings (e.g., "Indian Oil" over "MERCH_001")
                return max(candidates, key=len)
            return candidates[0]

        # Recurse into nested objects
        for value in data.values():
            if isinstance(value, dict):
                result = self._find_field(value, field_names, depth - 1, prefer_longer)
                if result:
                    return result

        return None

    def _find_merchant(self, data: Dict[str, Any]) -> Optional[str]:
        """Find merchant/vendor name in JSON"""
        return self._find_field(data, self.MERCHANT_FIELDS)

    def _find_amount(self, data: Dict[str, Any]) -> Optional[str]:
        """Find transaction amount in JSON"""
        amount = self._find_field(data, self.AMOUNT_FIELDS)
        if amount:
            # Format nicely
            try:
                num = float(amount)
                return f"{num:,.2f}"
            except ValueError:
                return amount
        return None

    def _find_transaction_type(self, data: Dict[str, Any]) -> Optional[str]:
        """Find transaction type/description in JSON"""
        return self._find_field(data, self.TYPE_FIELDS)

    def _find_currency(self, data: Dict[str, Any]) -> Optional[str]:
        """Find currency code in JSON"""
        return self._find_field(data, self.CURRENCY_FIELDS)

    def _find_mcc(self, data: Dict[str, Any]) -> Optional[str]:
        """Find merchant category code in JSON"""
        return self._find_field(data, ['merchant_category_code', 'mcc', 'category_code'])

    def _extract_amount_from_json(self, data: Dict[str, Any]) -> Optional[float]:
        """Extract transaction amount from JSON as a float"""
        # Use _find_field directly instead of _find_amount to get raw value
        amount_str = self._find_field(data, self.AMOUNT_FIELDS, prefer_longer=False)
        if amount_str:
            try:
                # Remove commas and convert to float
                return float(str(amount_str).replace(',', ''))
            except (ValueError, AttributeError):
                pass
        return None

    def _extract_date_from_json(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract and parse transaction date from JSON, return ISO format"""
        # Common date field names
        date_fields = ['date', 'transaction_date', 'timestamp', 'value_date', 'datetime', 'created_at']
        date_str = self._find_field(data, date_fields)

        if not date_str:
            return None

        # Try parsing various date formats
        date_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S.%f%z',
        ]

        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str[:19], fmt[:19])  # Truncate to match format length
                return dt.strftime('%Y-%m-%d')
            except (ValueError, IndexError):
                continue

        return None

    def _json_to_compact_text(self, data: Dict[str, Any]) -> str:
        """
        Convert JSON to compact readable text as fallback
        Extracts first few key-value pairs
        """
        parts = []
        count = 0
        max_items = 3

        for key, value in data.items():
            if count >= max_items:
                break
            if isinstance(value, (str, int, float)):
                parts.append(f"{key}: {value}")
                count += 1
            elif isinstance(value, dict):
                # Get first item from nested dict
                for k, v in value.items():
                    if isinstance(v, (str, int, float)):
                        parts.append(f"{k}: {v}")
                        count += 1
                        break

        result = ', '.join(parts)
        if len(result) > 200:
            result = result[:197] + "..."
        return result

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize plain text transaction descriptions
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Limit length
        if len(text) > 500:
            text = text[:497] + "..."

        return text


# Singleton instance
preprocessor = TransactionPreprocessor()


def preprocess_transaction(text: str) -> str:
    """
    Convenience function to preprocess transaction text

    Args:
        text: Raw transaction text (JSON or plain text)

    Returns:
        Cleaned, concise transaction description
    """
    return preprocessor.preprocess(text)
