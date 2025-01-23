import requests
from datetime import datetime
import json
import csv

def fetch_hotel_data():
    """Fetch hotel data from the API."""
    headers = {
        'sec-ch-ua-platform': '"macOS"',
        'Referer': 'https://www.verychic.fr/',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
    }

    params = {
        'branding': 'VRC',
        'currency': 'EUR',
        'detailed': 'false',
        'language': 'fr',
        'opinionCount': '0',
        'page': '0',
        'size': '2000',
        'memberStatus': 'PROSPECT',
        'channel': 'B2C_HOTEL',
        'publishingStatus': 'nonexpired',
        'channelVersion': '24.12.0',
    }

    response = requests.get('https://api.verychic.com/verychic-endpoints/v1/products.json', params=params, headers=headers)
    response.raise_for_status()
    return response.json()

def extract_hotel_data(data):
    """Extract relevant hotel data from the API response."""
    current_date = datetime.now().strftime('%Y-%m-%d')
    hotels = []

    for hotel in data['content']:
        hotel_info = {
            'name': hotel.get('name', 'N/A'),
            'destinationName': hotel.get('destinationName', 'N/A'),
            'normalizedPrice': hotel.get('normalizedPrice', 0.0),
            'discount': hotel.get('discount', 0.0),
            'offerStartDate': hotel.get('offerStartDate', 'N/A'),
            'offerEndDate': hotel.get('offerEndDate', 'N/A'),
            'retrievalDate': current_date
        }
        hotels.append(hotel_info)

    return hotels

def split_destination(destination):
    """Split destination into city and country."""
    if destination:
        parts = destination.split(',', 1)
        city = parts[0].strip() if len(parts) > 1 else ''
        country = parts[-1].strip()
        return city, country
    return '', ''

def get_category(hotel_name):
    """Assign category based on stars in the hotel name."""
    if '*****' in hotel_name:
        return '5*'
    elif '****' in hotel_name:
        return '4*'
    else:
        return 'Other'

def transform_date(date_string):
    """Transform date to a specific format."""
    try:
        dt = datetime.strptime(date_string, "%Y-%m-%dT%H:%M%z")
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return 'N/A'

def process_hotels(hotels):
    """Process and enrich hotel data."""
    processed_hotels = []
    for hotel in hotels:
        city, country = split_destination(hotel.get('destinationName', ''))
        category = get_category(hotel.get('name', ''))
        start_date = transform_date(hotel.get('offerStartDate', 'N/A'))
        end_date = transform_date(hotel.get('offerEndDate', 'N/A'))
        last_minute = 'X' if 'Dernière minute' in hotel.get('name', '') else ''

        processed_hotels.append({
            'hotel_name': hotel.get('name', 'N/A'),
            'City': city,
            'Country': country,
            'Category': category,
            'Price': hotel.get('normalizedPrice', 0.0),
            'Discount': hotel.get('discount', 0.0),
            'start_date': start_date,
            'end_date': end_date,
            'Dernière Minute': last_minute
        })
    return processed_hotels

def save_to_json(data, file_path):
    """Save data to a JSON file."""
    with open(file_path, 'w', encoding='utf-8') as output_file:
        json.dump(data, output_file, ensure_ascii=False, indent=4)

def save_to_csv(data, file_path):
    """Save data to a CSV file."""
    fieldnames = ['hotel_name', 'City', 'Country', 'Category', 'Price', 'Discount', 'start_date', 'end_date', 'Dernière Minute']
    with open(file_path, 'w', newline='', encoding='utf-8-sig') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=',')
        writer.writeheader()
        writer.writerows(data)

def main():
    """Main script execution."""
    try:
        raw_data = fetch_hotel_data()
        hotels = extract_hotel_data(raw_data)
        # save_to_json(hotels, 'extracted_hotels.json')

        processed_hotels = process_hotels(hotels)
        today = datetime.today().strftime('%d_%m_%Y')
        csv_file_path = f"../data/verychic_hotels_{today}.csv"
        save_to_csv(processed_hotels, csv_file_path)

        print(f"Data successfully saved to JSON and CSV: {csv_file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
