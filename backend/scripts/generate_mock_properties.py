import pandas as pd
import os

def create_sample_excel():
    data = [
        {
            "property_id": "prop-001",
            "title": "Luxury 2BHK in Chandigarh",
            "property_type": "apartment",
            "bhk": 2,
            "area_sqft": 1200,
            "price": 7500000,
            "location": "Chandigarh",
            "city": "Chandigarh",
            "locality": "Sector 15",
            "floor": 3,
            "total_floors": 5,
            "age": 2,
            "parking": 1,
            "amenities": "gym, pool, security",
            "developer": "Omaxe",
            "availability": "Ready to move",
            "rental_yield": 4.5,
            "historical_price": 7000000,
            "demand_score": 8.5,
            "latitude": 30.7333,
            "longitude": 76.7794,
            "description": "A beautiful 2BHK apartment suitable for a small family."
        },
        {
            "property_id": "prop-002",
            "title": "Spacious 3BHK in Mohali",
            "property_type": "apartment",
            "bhk": 3,
            "area_sqft": 1800,
            "price": 9500000,
            "location": "Mohali",
            "city": "Mohali",
            "locality": "Phase 8",
            "floor": 2,
            "total_floors": 10,
            "age": 5,
            "parking": 2,
            "amenities": "gym, clubhouse, park",
            "developer": "Hero Homes",
            "availability": "Ready to move",
            "rental_yield": 5.0,
            "historical_price": 9000000,
            "demand_score": 9.0,
            "latitude": 30.7046,
            "longitude": 76.7179,
            "description": "Great investment property with high rental yield."
        },
        {
            "property_id": "prop-003",
            "title": "Affordable 1BHK in Zirakpur",
            "property_type": "apartment",
            "bhk": 1,
            "area_sqft": 600,
            "price": 3000000,
            "location": "Zirakpur",
            "city": "Zirakpur",
            "locality": "VIP Road",
            "floor": 5,
            "total_floors": 6,
            "age": 1,
            "parking": 1,
            "amenities": "security",
            "developer": "Sushma",
            "availability": "Under construction",
            "rental_yield": 3.5,
            "historical_price": 2800000,
            "demand_score": 7.5,
            "latitude": 30.6425,
            "longitude": 76.8173,
            "description": "Budget friendly 1BHK."
        }
    ]
    
    df = pd.DataFrame(data)
    os.makedirs('backend/artifacts', exist_ok=True)
    file_path = 'backend/artifacts/properties.xlsx'
    df.to_excel(file_path, index=False)
    print(f"Created sample property data at {file_path}")

if __name__ == "__main__":
    create_sample_excel()
