from db.client import MongoDBClient
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def cleanup_expired_images():
    client = MongoDBClient()
    try:
        deleted_count = client.cleanup_old_images(days_old=30)
        logging.info(f"Cleaned up {deleted_count} expired image records")
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    cleanup_expired_images()