import math

from app.core.logger import logger


# =====================================================
# 🔥 DISTANCE CALCULATION
# =====================================================

def calculate_distance_km(
    lat1,
    lon1,
    lat2,
    lon2
):

    radius = 6371

    dlat = math.radians(lat2 - lat1)

    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(math.radians(lat1))
        *
        math.cos(math.radians(lat2))
        *
        math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return round(radius * c, 2)


# =====================================================
# 🔥 HOSPITAL SCORING ENGINE
# =====================================================

def rank_hospitals(
    hospitals,
    emergency
):

    ranked = []

    for hospital in hospitals:

        hospital_lat = hospital.get("latitude")
        hospital_lon = hospital.get("longitude")

        if not hospital_lat or not hospital_lon:
            continue

        # ==========================================
        # 🔥 DISTANCE SCORE
        # ==========================================

        distance_km = calculate_distance_km(
            emergency.latitude,
            emergency.longitude,
            hospital_lat,
            hospital_lon
        )

        # closer hospital => higher score
        distance_score = max(
            0,
            1 - (distance_km / 20)
        )

        # ==========================================
        # 🔥 ICU BONUS
        # ==========================================

        icu_score = 0

        if emergency.requires_icu:
            icu_score = 0.25

        # ==========================================
        # 🔥 SEVERITY BONUS
        # ==========================================

        severity_score = 0

        if emergency.severity == "critical":
            severity_score = 0.30

        elif emergency.severity == "high":
            severity_score = 0.20

        elif emergency.severity == "moderate":
            severity_score = 0.10

        # ==========================================
        # 🔥 FINAL SCORE
        # ==========================================

        final_score = round(
            (
                distance_score * 0.45
                +
                icu_score
                +
                severity_score
            ),
            2
        )

        # ==========================================
        # 🔥 EXPLAINABILITY
        # ==========================================

        reason = (
            f"{emergency.severity} emergency "
            f"located {distance_km} km away"
        )

        if emergency.requires_icu:
            reason += " requiring ICU support"

        ranked.append({

            "hospital": hospital.get("name"),

            "distance_km": distance_km,

            "score": final_score,

            "recommended": final_score >= 0.7,

            "match_reason": reason,

            "latitude": hospital_lat,

            "longitude": hospital_lon
        })

    # ==========================================
    # 🔥 SORT BY SCORE
    # ==========================================

    ranked.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    logger.info(
        f"event=hospitals_ranked "
        f"count={len(ranked)}"
    )

    return ranked[:10]