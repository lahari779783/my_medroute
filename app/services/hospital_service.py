import requests

from app.core.logger import logger


OVERPASS_URL = "https://overpass-api.de/api/interpreter"


# =====================================================
# 🔥 FETCH NEARBY HOSPITALS
# =====================================================

def get_nearby_hospitals(
    latitude: float,
    longitude: float,
    radius: int = 5000
):

    try:

        logger.info(
            f"event=hospital_search_started "
            f"latitude={latitude} "
            f"longitude={longitude}"
        )

        # ==========================================
        # 🔥 OVERPASS QUERY
        # ==========================================

        query = f"""
        [out:json][timeout:25];

        (
          node["amenity"="hospital"]
          (around:{radius},{latitude},{longitude});

          way["amenity"="hospital"]
          (around:{radius},{latitude},{longitude});

          relation["amenity"="hospital"]
          (around:{radius},{latitude},{longitude});
        );

        out center;
        """

        headers = {
            "User-Agent": "MedRoute/1.0"
        }

        response = requests.get(
            OVERPASS_URL,
            params={"data": query},
            headers=headers,
            timeout=30
        )

        # ==========================================
        # 🔥 RESPONSE VALIDATION
        # ==========================================

        if response.status_code != 200:

            logger.error(
                f"event=hospital_api_failed "
                f"status={response.status_code} "
                f"body={response.text[:200]}"
            )

            return []

        data = response.json()

        hospitals = []

        for element in data.get("elements", []):

            tags = element.get("tags", {})

            hospital = {

                "name": tags.get(
                    "name",
                    "Unknown Hospital"
                ),

                "latitude": (
                    element.get("lat")
                    or element.get("center", {}).get("lat")
                ),

                "longitude": (
                    element.get("lon")
                    or element.get("center", {}).get("lon")
                ),

                "address": tags.get(
                    "addr:full",
                    "Address unavailable"
                )
            }

            hospitals.append(hospital)

        logger.info(
            f"event=hospital_search_completed "
            f"count={len(hospitals)}"
        )

        return hospitals

    except Exception as e:

        logger.error(
            f"event=hospital_search_failed "
            f"error={str(e)}"
        )

        return []