import os
import time
import pandas as pd
import psycopg2
import requests
import dotenv

dotenv.load_dotenv()

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
CACHE_CSV = "reverse_geocoded_cache.csv"

# -----------------------
# 1. Connect to Postgres
# -----------------------
conn = psycopg2.connect(
    host="localhost",  # docker exposes 5432 -> localhost
    port=5432,
    dbname="rank-nsf-linker",
    user="postgres",
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
)
conn.autocommit = True
cur = conn.cursor()

# -----------------------
# 2. Load CSV cache
# -----------------------
if os.path.exists(CACHE_CSV):
    cache_df = pd.read_csv(CACHE_CSV)
else:
    cache_df = pd.DataFrame(
        columns=[
            "institution",
            "latitude",
            "longitude",
            "street_address",
            "city",
            "zip_code",
            "country",
        ]
    )


def from_cache(institution):
    row = cache_df.loc[cache_df["institution"] == institution]
    if not row.empty:
        r = row.iloc[0]
        return r["street_address"], r["city"], r["zip_code"], r["country"]
    return None, None, None, None


def add_to_cache(institution, lat, lon, street, city, zip_code, country):
    global cache_df
    cache_df = pd.concat(
        [
            cache_df,
            pd.DataFrame(
                [
                    {
                        "institution": institution,
                        "latitude": lat,
                        "longitude": lon,
                        "street_address": street,
                        "city": city,
                        "zip_code": zip_code,
                        "country": country,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    cache_df.to_csv(CACHE_CSV, index=False)


# -----------------------
# 3. Fetch rows missing address
# -----------------------
cur.execute(
    """
    SELECT institution, latitude, longitude
    FROM public.universities
    WHERE (street_address IS NULL OR city IS NULL OR zip_code IS NULL)
      AND latitude IS NOT NULL
      AND longitude IS NOT NULL;
"""
)
rows = cur.fetchall()
print(f"Found {len(rows)} rows needing reverse geocoding")


# -----------------------
# 4. Mapbox reverse geocode helper
# -----------------------
def reverse_geocode(lat, lon):
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{lon},{lat}.json"
    params = {"access_token": MAPBOX_TOKEN, "limit": 1}
    r = requests.get(url, params=params)
    if r.status_code != 200:
        print("Mapbox error:", r.status_code, r.text)
        return None, None, None, None

    data = r.json()
    if not data.get("features"):
        return None, None, None, None

    feature = data["features"][0]
    context = feature.get("context", [])
    street = feature.get("text", "")
    city = zip_code = country = ""

    for c in context:
        if c["id"].startswith("place."):
            city = c.get("text", "")
        elif c["id"].startswith("postcode."):
            zip_code = c.get("text", "")
        elif c["id"].startswith("country."):
            country = c.get("text", "")

    return street, city, zip_code, country


# -----------------------
# 5. Process each row
# -----------------------
for r in rows:
    institution, lat, lon = r
    street, city, zip_code, country = from_cache(institution)

    if street:
        print(f"✅ Cache hit for ({lat}, {lon})")
    else:
        street, city, zip_code, country = reverse_geocode(lat, lon)
        time.sleep(0.2)
        if not street and not city:
            print(f"⚠️ Failed reverse geocode ({lat}, {lon})")
            continue
        add_to_cache(institution, lat, lon, street, city, zip_code, country)
        print(f"🏙️ Reverse geocoded ({institution} - {lat}, {lon}) -> {street}, {city}")

    # -----------------------
    # 6. Update Postgres
    # -----------------------
    cur.execute(
        """
        UPDATE public.universities
        SET street_address = COALESCE(%s, street_address),
            city = COALESCE(%s, city),
            zip_code = COALESCE(%s, zip_code),
            country = COALESCE(%s, country)
        WHERE institution = %s;
    """,
        (street, city, zip_code, country, institution),
    )

print("✅ Reverse geocoding complete.")
cur.close()
conn.close()
