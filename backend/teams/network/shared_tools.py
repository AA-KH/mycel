import logging
import math

logger = logging.getLogger(__name__)

async def calculate_distance(city1: str, city2: str) -> str:
    """
    Calculates the exact air-line (Great Circle) distance in kilometers between two cities using Geopy.
    Falls back to a mock value if Geopy is not installed or cities are not found.
    """
    logger.info(f"Calculating distance between {city1} and {city2}")
    
    try:
        from geopy.geocoders import Nominatim
        from geopy.distance import geodesic
        
        # We need a user_agent for Nominatim
        geolocator = Nominatim(user_agent="mycel_network_team")
        
        location1 = geolocator.geocode(city1)
        location2 = geolocator.geocode(city2)
        
        if location1 and location2:
            coord1 = (location1.latitude, location1.longitude)
            coord2 = (location2.latitude, location2.longitude)
            
            distance_km = geodesic(coord1, coord2).kilometers
            return f"Exact Distance between {city1} and {city2}: {distance_km:.2f} km."
        else:
            return f"Error: Could not find coordinates for one or both cities ({city1}, {city2}). Please verify the names."
            
    except ImportError:
        logger.warning("Geopy is not installed. Using mocked distance.")
        return f"[MOCKED] Distance between {city1} and {city2} is approximately 4500 km. Install geopy for exact values."
    except Exception as e:
        logger.error(f"Geopy error: {e}")
        return f"Error calculating distance: {str(e)}"

async def calculate_eoq(annual_demand: float, ordering_cost: float, holding_cost: float) -> str:
    """
    Calculates the Economic Order Quantity (EOQ).
    Formula: sqrt((2 * D * S) / H)
    """
    logger.info(f"Calculating EOQ for D={annual_demand}, S={ordering_cost}, H={holding_cost}")
    
    try:
        if holding_cost <= 0:
            return "Error: Holding cost (H) must be greater than zero."
        if annual_demand < 0 or ordering_cost < 0:
            return "Error: Demand (D) and Ordering Cost (S) must be non-negative."
            
        eoq = math.sqrt((2 * annual_demand * ordering_cost) / holding_cost)
        
        return f"Economic Order Quantity (EOQ): {eoq:.2f} units."
    except Exception as e:
        logger.error(f"EOQ error: {e}")
        return f"Error calculating EOQ: {str(e)}"
