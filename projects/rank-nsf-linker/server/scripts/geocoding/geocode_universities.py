import os
import time
import requests
import psycopg2
import pandas as pd
import dotenv

dotenv.load_dotenv()

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
CACHE_CSV = "geocoded_cache.csv"

# -----------------------
# 1. Connect to Postgres
# -----------------------
conn = psycopg2.connect(
    host="localhost",  # assuming port mapping to local 5432
    port=5432,
    dbname="rank-nsf-linker",
    user="postgres",
    password=os.getenv("POSTGRES_PASSWORD", "postgres")  # or whatever you set
)
conn.autocommit = True
cur = conn.cursor()

# -----------------------
# 2. Load CSV cache
# -----------------------
if os.path.exists(CACHE_CSV):
    cache_df = pd.read_csv(CACHE_CSV)
else:
    cache_df = pd.DataFrame(columns=["institution", "latitude", "longitude"])

def from_cache(institution):
    row = cache_df.loc[cache_df["institution"] == institution]
    if not row.empty:
        return row.iloc[0]["latitude"], row.iloc[0]["longitude"]
    return None, None

def add_to_cache(institution, lat, lon):
    global cache_df
    cache_df = pd.concat([cache_df, pd.DataFrame([{
        "institution": institution,
        "latitude": lat,
        "longitude": lon
    }])], ignore_index=True)
    cache_df.to_csv(CACHE_CSV, index=False)

# -----------------------
# 3. Fetch un-geocoded rows
# -----------------------
cur.execute("""
    SELECT institution, street_address, city, zip_code, country
    FROM public.universities
    WHERE latitude IS NULL OR longitude IS NULL;
""")
rows = cur.fetchall()

print(f"Found {len(rows)} ungeocoded rows")

# -----------------------
# 4. Mapbox Geocode helper
# -----------------------
def geocode(address):
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json"
    params = {"access_token": MAPBOX_TOKEN, "limit": 1}
    r = requests.get(url, params=params)
    if r.status_code != 200:
        print("Mapbox error:", r.status_code, r.text)
        return None, None
    data = r.json()
    if data.get("features"):
        lon, lat = data["features"][0]["geometry"]["coordinates"]
        return lat, lon
    return None, None

# -----------------------
# 5. Iterate through rows
# -----------------------
for r in rows:
    institution, street, city, zip_code, country = r
    lat, lon = from_cache(institution)

    if lat and lon:
        print(f"✅ Cache hit: {institution}")
    else:
        # Build query
        address = ", ".join([str(x) for x in [institution, street, city, zip_code, country] if x])
        lat, lon = geocode(address)
        time.sleep(0.2)  # respect rate limits

        if lat and lon:
            print(f"🌍 Geocoded {institution}: ({lat}, {lon})")
            add_to_cache(institution, lat, lon)
        else:
            print(f"⚠️ Failed to geocode {institution}")
            continue

    # -----------------------
    # 6. UPSERT into Postgres
    # -----------------------
    cur.execute("""
        UPDATE public.universities
        SET latitude = %s, longitude = %s
        WHERE institution = %s;
    """, (lat, lon, institution))

print("✅ All done.")

cur.close()
conn.close()
