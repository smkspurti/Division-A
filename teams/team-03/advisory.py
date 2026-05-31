import os
import json
from groq import Groq
from dotenv import load_dotenv


load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


SYSTEM_PROMPT = """You are an agricultural market advisor for Karnataka farmers.
You speak only in simple, clear Kannada (ಕನ್ನಡ).
Your job is to explain commodity price forecasts in plain language that a farmer can understand.
Do not use technical jargon. Do not use English words.
Keep the advisory to 3-4 short sentences.
Format:
- Line 1: State the commodity and current price
- Line 2: What price trend is expected in the next 7 days
- Line 3: Practical advice — sell now, wait, or store
"""


def generate_kannada_advisory(forecast_data: dict) -> str:
    """
    Takes a single commodity forecast dict and returns a Kannada advisory string.
    """
    commodity    = forecast_data.get("commodity", "Unknown")
    last_price   = forecast_data.get("last_known_price", 0)
    last_date    = forecast_data.get("last_known_date", "")
    trend        = forecast_data.get("trend", "stable")
    avg_forecast = forecast_data.get("avg_forecast_price", last_price)
    pct_change   = round(((avg_forecast - last_price) / last_price) * 100, 1) if last_price else 0

    user_prompt = f"""
Commodity: {commodity}
Current Price (as of {last_date}): ₹{last_price} per quintal
Forecasted Average Price (next 7 days): ₹{avg_forecast} per quintal
Price Trend: {trend}
Percentage Change: {pct_change}%

Please write a 3-4 sentence advisory in Kannada for farmers about whether to sell now or wait.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ],
        max_tokens=300,
        temperature=0.4,
    )

    return response.choices[0].message.content.strip()


def generate_all_advisories(forecasts_path: str = "forecasts.json") -> dict:
    with open(forecasts_path, "r") as f:
        forecasts = json.load(f)

    advisories = {}
    for commodity, data in forecasts.items():
        if "error" in data:
            advisories[commodity] = f"ಮಾಹಿತಿ ಲಭ್ಯವಿಲ್ಲ ({data['error']})"
            continue
        print(f"Generating Kannada advisory for: {commodity}")
        try:
            advisory = generate_kannada_advisory(data)
            advisories[commodity] = advisory
            print(f"  ✓ Done")
        except Exception as e:
            advisories[commodity] = f"ಮಾಹಿತಿ ಲಭ್ಯವಿಲ್ಲ ({str(e)})"

    with open("advisories.json", "w", encoding="utf-8") as f:
        json.dump(advisories, f, ensure_ascii=False, indent=2)

    print("Saved advisories.json")
    return advisories


if __name__ == "__main__":
    generate_all_advisories()
