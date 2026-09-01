import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

async def fetch_trend_data(keyword: str) -> str:
    """
    Fetches real Google Trends data for a keyword over the last 3 months.
    Uses pytrends to get live search interest.
    """
    logger.info(f"Fetching live Google Trends data for: {keyword}")
    
    def _fetch():
        try:
            import warnings
            warnings.simplefilter(action='ignore', category=FutureWarning)
            from pytrends.request import TrendReq
            
            # Using timezone offset 0 (UTC)
            pytrend = TrendReq(hl='en-US', tz=360)
            
            # timeframe='today 3-m' means the last 3 months
            pytrend.build_payload(kw_list=[keyword], timeframe='today 3-m')
            
            df = pytrend.interest_over_time()
            if df.empty:
                return f"No significant search trend data found for '{keyword}' on Google Trends."
                
            # Drop the isPartial column if it exists
            if 'isPartial' in df.columns:
                df = df.drop(columns=['isPartial'])
                
            # Calculate simple statistics
            recent_avg = df.iloc[-7:].mean().iloc[0]  # Avg of last 7 days
            older_avg = df.iloc[:7].mean().iloc[0]    # Avg of first 7 days (3 months ago)
            
            trend_direction = "STABLE"
            if recent_avg > older_avg * 1.15:
                trend_direction = "RISING"
            elif recent_avg < older_avg * 0.85:
                trend_direction = "FALLING"
                
            max_interest = df.max().iloc[0]
            current_interest = df.iloc[-1].iloc[0]
            
            report = (
                f"LIVE TREND ANALYSIS for '{keyword}' (Past 3 Months):\n"
                f"- Trend Direction: {trend_direction}\n"
                f"- Current Interest Score: {current_interest}/100\n"
                f"- Peak Interest Score: {max_interest}/100\n"
                f"- 3-Month Start Avg: {older_avg:.1f}/100\n"
                f"- Past Week Avg: {recent_avg:.1f}/100\n"
            )
            return report
            
        except ImportError:
            return f"TREND ANALYSIS for '{keyword}': pytrends is not installed. Mocking -> High demand."
        except Exception as e:
            logger.error(f"Pytrends failed for {keyword}: {e}")
            return f"TREND ANALYSIS for '{keyword}': Error fetching data ({str(e)}). Consider it a highly volatile keyword."

    # Run the blocking pytrends request in a background thread to prevent blocking the async loop
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _fetch)


async def get_economic_indicators(region: str) -> str:
    """
    Simulates fetching macro-economic indicators (CPI, Inflation, Consumer Confidence) for a region.
    In a real system, this would call World Bank or regional reserve APIs.
    """
    logger.info(f"Fetching economic indicators for: {region}")
    # Mocking macro data for now
    region_lower = region.lower()
    if "europe" in region_lower or "eu" in region_lower:
        return f"ECONOMIC DATA for '{region}': High inflation (CPI up 4.2%). Consumer Confidence Index is at a 12-month low. Purchasing power for non-essential goods is severely constrained."
    elif "us" in region_lower or "america" in region_lower:
        return f"ECONOMIC DATA for '{region}': Stable inflation (CPI 2.8%). Consumer Confidence is moderate. Strong job market supporting retail spending."
    elif "asia" in region_lower or "china" in region_lower:
        return f"ECONOMIC DATA for '{region}': Deflationary pressures in manufacturing hubs. High export capacity, but domestic consumer spending is slowing down (-1.5% YoY)."
    else:
        return f"ECONOMIC DATA for '{region}': Baseline macroeconomic environment. CPI is around 3%, stable purchasing power."
