import logging
import json

logger = logging.getLogger(__name__)

# --- SCHEMAS ---
AANYA_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_center_of_gravity",
            "description": "Calculates the geographic center of gravity for a set of cities, weighted by their demand volume. Useful for finding the optimal location for a centralized Distribution Center.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of city names (e.g., ['Berlin', 'Paris', 'Munich'])"
                    },
                    "weights": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "List of corresponding demand weights or volumes for each city. Must be the same length as cities."
                    }
                },
                "required": ["cities", "weights"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_facility_cost",
            "description": "Estimates the Setup (CapEx) and Annual Running (OpEx) costs for a facility based on its region and size.",
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "The global region (e.g., 'North America', 'Western Europe', 'Eastern Europe', 'Southeast Asia', 'China')"
                    },
                    "size_sqm": {
                        "type": "number",
                        "description": "The size of the facility in square meters (e.g., 50000)"
                    },
                    "facility_type": {
                        "type": "string",
                        "description": "Type of facility: 'Automated DC', 'Manual DC', or 'Cross-Dock'"
                    }
                },
                "required": ["region", "size_sqm", "facility_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_driving_route",
            "description": "Calculates the real-world driving distance and driving time between two cities using the OSRM API.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city1": {
                        "type": "string",
                        "description": "Origin city (e.g., 'Berlin, Germany')"
                    },
                    "city2": {
                        "type": "string",
                        "description": "Destination city (e.g., 'Paris, France')"
                    }
                },
                "required": ["city1", "city2"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_regional_economic_data",
            "description": "Fetches macro-economic data (GDP, Inflation) for a given country code using the World Bank API.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country_code": {
                        "type": "string",
                        "description": "ISO 2-letter or 3-letter country code (e.g., 'US', 'IN', 'DE', 'VN')"
                    }
                },
                "required": ["country_code"]
            }
        }
    }
]

import requests

async def calculate_driving_route(city1: str, city2: str) -> str:
    """Calculates driving route using OSRM."""
    try:
        from geopy.geocoders import Nominatim
        geolocator = Nominatim(user_agent="mycel_aanya_routing")
        
        loc1 = geolocator.geocode(city1)
        loc2 = geolocator.geocode(city2)
        
        if not loc1 or not loc2:
            return f"Error: Could not geocode one of the cities ({city1}, {city2})."
            
        # OSRM expects lon,lat
        osrm_url = f"http://router.project-osrm.org/route/v1/driving/{loc1.longitude},{loc1.latitude};{loc2.longitude},{loc2.latitude}?overview=false"
        
        response = requests.get(osrm_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "routes" in data and len(data["routes"]) > 0:
                route = data["routes"][0]
                distance_km = route.get("distance", 0) / 1000.0
                duration_hrs = route.get("duration", 0) / 3600.0
                
                result = {
                    "origin": city1,
                    "destination": city2,
                    "driving_distance_km": round(distance_km, 2),
                    "driving_duration_hours": round(duration_hrs, 2)
                }
                return json.dumps(result, indent=2)
        return "Error: OSRM route could not be found or API limit reached."
    except Exception as e:
        return f"Error calculating driving route: {str(e)}"

async def get_regional_economic_data(country_code: str) -> str:
    """Fetches GDP and Inflation from World Bank API."""
    try:
        # Indicator for GDP (current US$): NY.GDP.MKTP.CD
        # Indicator for Inflation (consumer prices %): FP.CPI.TOTL.ZG
        
        gdp_url = f"http://api.worldbank.org/v2/country/{country_code}/indicator/NY.GDP.MKTP.CD?format=json&mrnev=1"
        inflation_url = f"http://api.worldbank.org/v2/country/{country_code}/indicator/FP.CPI.TOTL.ZG?format=json&mrnev=1"
        
        gdp_resp = requests.get(gdp_url, timeout=5).json()
        inf_resp = requests.get(inflation_url, timeout=5).json()
        
        result = {"country_code": country_code}
        
        if len(gdp_resp) > 1 and len(gdp_resp[1]) > 0:
            gdp_data = gdp_resp[1][0]
            result["latest_gdp_usd"] = gdp_data.get("value")
            result["gdp_year"] = gdp_data.get("date")
            
        if len(inf_resp) > 1 and len(inf_resp[1]) > 0:
            inf_data = inf_resp[1][0]
            result["latest_inflation_percent"] = inf_data.get("value")
            result["inflation_year"] = inf_data.get("date")
            
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error fetching World Bank data: {str(e)}"

async def calculate_center_of_gravity(cities: list, weights: list) -> str:
    """
    Given a list of cities and their demand weights, calculates the geographic center of gravity.
    """
    if len(cities) != len(weights):
        return "Error: The number of cities must match the number of weights."
    
    if len(cities) == 0:
        return "Error: City list is empty."
        
    try:
        from geopy.geocoders import Nominatim
        from geopy.distance import geodesic
        
        geolocator = Nominatim(user_agent="mycel_aanya_cog")
        
        total_weight = sum(weights)
        if total_weight == 0:
            return "Error: Total weight cannot be zero."
            
        weighted_lat = 0.0
        weighted_lon = 0.0
        
        valid_cities = []
        
        for city, weight in zip(cities, weights):
            location = geolocator.geocode(city)
            if location:
                weighted_lat += location.latitude * weight
                weighted_lon += location.longitude * weight
                valid_cities.append(f"{city} ({location.latitude:.2f}, {location.longitude:.2f})")
            else:
                return f"Error: Could not find coordinates for city: {city}"
                
        center_lat = weighted_lat / total_weight
        center_lon = weighted_lon / total_weight
        
        # Try to reverse geocode the center point to get a nearby city/region
        approx_location = "Unknown Area"
        try:
            # reverse geocode takes "lat, lon"
            location = geolocator.reverse(f"{center_lat}, {center_lon}", exactly_one=True)
            if location:
                approx_location = location.address
        except Exception:
            pass
            
        result = {
            "center_coordinates": f"{center_lat:.4f}, {center_lon:.4f}",
            "approximate_location": approx_location,
            "processed_cities": valid_cities,
            "total_demand_weight": total_weight
        }
        return json.dumps(result, indent=2)
        
    except ImportError:
        return "Error: Geopy is not installed."
    except Exception as e:
        return f"Error calculating center of gravity: {str(e)}"


async def estimate_facility_cost(region: str, size_sqm: float, facility_type: str) -> str:
    """
    Estimates facility costs based on regional multipliers.
    """
    # Base costs per SQM in USD (mock logic based on industry averages)
    region_multipliers = {
        "North America": 1.0,
        "Western Europe": 1.1,
        "Eastern Europe": 0.6,
        "Southeast Asia": 0.4,
        "China": 0.5,
        "Latin America": 0.5,
        "Middle East": 0.8,
        "India": 0.35
    }
    
    # Identify the closest region
    matched_region = "North America"
    for r in region_multipliers.keys():
        if r.lower() in region.lower():
            matched_region = r
            break
            
    multiplier = region_multipliers.get(matched_region, 1.0)
    
    # Facility type CapEx multiplier
    type_multiplier = {
        "Automated DC": 2500, # Highly automated, expensive setup per sqm
        "Manual DC": 800,
        "Cross-Dock": 1200
    }
    
    base_capex_per_sqm = type_multiplier.get(facility_type, 1000)
    
    # Calculate CapEx (Real estate build + Equipment)
    total_capex = size_sqm * base_capex_per_sqm * multiplier
    
    # Calculate OpEx (Annual labor, utilities, maintenance)
    # Automated has lower OpEx relative to size compared to manual (in high labor cost regions)
    if facility_type == "Automated DC":
        base_opex_per_sqm = 150 # Less labor
    else:
        base_opex_per_sqm = 350 # More labor
        
    total_annual_opex = size_sqm * base_opex_per_sqm * multiplier
    
    result = {
        "region_matched": matched_region,
        "facility_type": facility_type,
        "size_sqm": size_sqm,
        "estimated_capex_usd": round(total_capex, 2),
        "estimated_annual_opex_usd": round(total_annual_opex, 2),
        "payback_insight": "Automated DCs have higher CapEx but lower OpEx. Calculate total cost of ownership over 5-10 years when deciding."
    }
    
    return json.dumps(result, indent=2)
