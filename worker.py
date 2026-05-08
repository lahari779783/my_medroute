import time
import json

from concurrent.futures import (
    ThreadPoolExecutor,
    TimeoutError
)

from app.core.logger import logger
from app.core.redis_client import redis_client
from app.database import SessionLocal

from app.models.emergency import Emergency

from app.services.triage_service import analyze_symptoms
from app.services.hospital_service import get_nearby_hospitals
from app.services.ranking_service import rank_hospitals

from app.models.user import User
from app.models.profile import MedicalProfile

QUEUE = "emergency_queue"
PROCESSING_QUEUE = "emergency_processing"
FAILED_QUEUE = "emergency_failed"

MAX_RETRIES = 3
JOB_TIMEOUT = 30


# =====================================================
# 🔥 PROCESS EMERGENCY
# =====================================================

def process_emergency(emergency_id):

    db = SessionLocal()

    start_time = time.time()

    try:

        logger.info(
            f"event=processing_started "
            f"emergency_id={emergency_id}"
        )

        # ==========================================
        # 🔥 FETCH EMERGENCY
        # ==========================================

        emergency = db.query(Emergency).filter(
            Emergency.id == emergency_id
        ).first()

        if not emergency:

            logger.error(
                f"event=emergency_not_found "
                f"emergency_id={emergency_id}"
            )

            return False

        # ==========================================
        # 🔥 SAFE STATE CHECK
        # ==========================================

        if emergency.status != "CREATED":

            logger.warning(
                f"event=already_processed "
                f"emergency_id={emergency_id}"
            )

            return True

        # ==========================================
        # 🔥 UPDATE STATUS
        # ==========================================

        emergency.status = "PROCESSING"

        db.add(emergency)

        db.commit()

        # ==========================================
        # 🔥 GENAI TRIAGE
        # ==========================================

        triage = analyze_symptoms(
            emergency.symptoms
        )

        # ==========================================
        # 🔥 STORE TRIAGE INTELLIGENCE
        # ==========================================

        emergency.severity = triage.severity

        emergency.confidence = triage.confidence

        emergency.requires_icu = triage.requires_icu

        emergency.rationale = triage.rationale

        emergency.triage_source = triage.source

        emergency.specializations = json.dumps(
            triage.specializations
        )

        db.add(emergency)

        db.commit()

        logger.info(
            f"event=triage_completed "
            f"emergency_id={emergency_id} "
            f"severity={triage.severity} "
            f"source={triage.source}"
        )

        # ==========================================
        # 🔥 FETCH NEARBY HOSPITALS
        # ==========================================

        hospitals = get_nearby_hospitals(
            latitude=emergency.latitude,
            longitude=emergency.longitude
        )

        logger.info(
            f"event=hospitals_fetched "
            f"emergency_id={emergency_id} "
            f"count={len(hospitals)}"
        )

        # ==========================================
        # 🔥 RANK HOSPITALS
        # ==========================================

        ranked_hospitals = rank_hospitals(
            hospitals,
            emergency
        )

        logger.info(
            f"event=hospital_ranking_completed "
            f"emergency_id={emergency_id} "
            f"count={len(ranked_hospitals)}"
        )

        # ==========================================
        # 🔥 STORE RANKED HOSPITALS
        # ==========================================

        emergency.matched_hospitals = json.dumps(
            ranked_hospitals
        )

        db.add(emergency)

        db.commit()

        # ==========================================
        # 🔥 SIMULATE REMAINING WORK
        # ==========================================

        time.sleep(5)

        # ==========================================
        # 🔥 FINAL STATUS
        # ==========================================

        emergency.status = "MATCHED"

        db.add(emergency)

        db.commit()

        processing_time = round(
            time.time() - start_time,
            2
        )

        logger.info(
            f"event=processing_completed "
            f"emergency_id={emergency_id} "
            f"processing_time={processing_time}s"
        )

        return True

    except Exception as e:

        logger.error(
            f"event=processing_failed "
            f"emergency_id={emergency_id} "
            f"error={str(e)}"
        )

        return False

    finally:

        db.close()


# =====================================================
# 🔥 PROCESS WITH TIMEOUT
# =====================================================

def process_with_timeout(emergency_id):

    with ThreadPoolExecutor(max_workers=1) as executor:

        future = executor.submit(
            process_emergency,
            emergency_id
        )

        try:

            return future.result(
                timeout=JOB_TIMEOUT
            )

        except TimeoutError:

            logger.error(
                f"event=job_timeout "
                f"emergency_id={emergency_id}"
            )

            return False


# =====================================================
# 🔥 WORKER LOOP
# =====================================================

def worker():

    logger.info("event=worker_started")

    while True:

        data = redis_client.brpoplpush(
            QUEUE,
            PROCESSING_QUEUE,
            timeout=5
        )

        if not data:
            continue

        logger.info(
            f"event=job_received raw_data={data}"
        )

        task = json.loads(data)

        emergency_id = task["emergency_id"]

        retries = task.get("retries", 0)

        success = process_with_timeout(
            emergency_id
        )

        redis_client.lrem(
            PROCESSING_QUEUE,
            1,
            data
        )

        if success:
            continue

        retries += 1

        task["retries"] = retries

        if retries >= MAX_RETRIES:

            logger.error(
                f"event=job_moved_to_dlq "
                f"emergency_id={emergency_id}"
            )

            redis_client.rpush(
                FAILED_QUEUE,
                json.dumps(task)
            )

            db = SessionLocal()

            emergency = db.query(Emergency).filter(
                Emergency.id == emergency_id
            ).first()

            if emergency:

                emergency.status = "FAILED"

                db.add(emergency)

                db.commit()

            db.close()

        else:

            logger.warning(
                f"event=job_retry "
                f"emergency_id={emergency_id} "
                f"attempt={retries}"
            )

            redis_client.rpush(
                QUEUE,
                json.dumps(task)
            )


if __name__ == "__main__":
    worker()