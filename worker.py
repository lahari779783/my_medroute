import time
import json

from app.core.redis_client import redis_client
from app.database import SessionLocal
from app.models.emergency import Emergency
from app.services.triage_service import analyze_symptoms

QUEUE = "emergency_queue"
PROCESSING_QUEUE = "emergency_processing"
FAILED_QUEUE = "emergency_failed"

MAX_RETRIES = 3


def process_emergency(emergency_id):
    db = SessionLocal()

    try:
        print(f"[INFO] Processing {emergency_id}")

        # 🔥 FETCH EMERGENCY
        emergency = db.query(Emergency).filter(
            Emergency.id == emergency_id
        ).first()

        if not emergency:
            print(f"[ERROR] Emergency not found: {emergency_id}")
            return False

        # 🔥 ATOMIC STATE TRANSITION
        updated = db.query(Emergency).filter(
            Emergency.id == emergency_id,
            Emergency.status == "CREATED"
        ).update({"status": "PROCESSING"})

        db.commit()

        if not updated:
            print(f"[INFO] Already processed: {emergency_id}")
            return True

        # =====================================================
        # 🔥 GENAI TRIAGE
        # =====================================================

        triage = analyze_symptoms(emergency.symptoms)

        print("\n================ TRIAGE RESULT ================")
        print(triage)
        print("================================================\n")

        # 🔥 simulate remaining work
        time.sleep(5)

        # 🔥 FINAL STATE
        db.query(Emergency).filter(
            Emergency.id == emergency_id
        ).update({"status": "MATCHED"})

        db.commit()

        print(f"[SUCCESS] Completed {emergency_id}")

        return True

    except Exception as e:
        print(f"[ERROR] Failed {emergency_id}: {str(e)}")
        return False

    finally:
        db.close()


def worker():
    print("🚀 Worker started...")

    while True:

        # 🔥 move safely to processing queue
        data = redis_client.brpoplpush(
            QUEUE,
            PROCESSING_QUEUE,
            timeout=5
        )

        if not data:
            continue
        print("[RAW REDIS DATA]", data)
        task = json.loads(data)

        emergency_id = task["emergency_id"]
        retries = task.get("retries", 0)

        success = process_emergency(emergency_id)

        # 🔥 always remove from processing queue
        redis_client.lrem(PROCESSING_QUEUE, 1, data)

        if success:
            continue

        # =====================================================
        # 🔥 FAILURE HANDLING
        # =====================================================

        retries += 1
        task["retries"] = retries

        if retries >= MAX_RETRIES:

            print(f"[DLQ] Moving to failed queue: {emergency_id}")

            redis_client.rpush(
                FAILED_QUEUE,
                json.dumps(task)
            )

            db = SessionLocal()

            db.query(Emergency).filter(
                Emergency.id == emergency_id
            ).update({"status": "FAILED"})

            db.commit()
            db.close()

        else:

            print(f"[RETRY] Retrying {emergency_id} (attempt {retries})")

            redis_client.rpush(
                QUEUE,
                json.dumps(task)
            )


if __name__ == "__main__":
    worker()