from cloudevents.http import CloudEvent
import functions_framework
from google.cloud import storage
from rag.rag_pipline import process_rag_corpus
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filename="main_pipeline.log",
    filemode="a"      
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console.setFormatter(formatter)
logging.getLogger().addHandler(console)
logger = logging.getLogger(__name__)

_processed_files = set()

@functions_framework.cloud_event
def pdlc_rag(cloud_event: CloudEvent) -> tuple:
    try:
        data = cloud_event.data
        event_id = cloud_event["id"]
        event_type = cloud_event["type"]

        raw_bucket = data["bucket"]
        filename = data["name"]
        metageneration = data["metageneration"]
        processing_bucket = "kishor-pdlc-process-bucket"

        if filename.startswith('.') or filename.endswith('.tmp'):
            logger.info(f"Skipping temporary file: {filename}")
            return event_id, event_type, raw_bucket, filename

        if event_type != "google.cloud.storage.object.v1.finalized":
            logger.info(f"Ignoring event type: {event_type}")
            return event_id, event_type, raw_bucket, filename

        file_id = f"{raw_bucket}/{filename}/{metageneration}"
        if file_id in _processed_files:
            logger.info(f"File already processed: {filename}")
            return event_id, event_type, raw_bucket, filename

        _processed_files.add(file_id)

        # Add timestamp to filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        base_name = filename.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        extension = filename.rsplit(".", 1)[-1]
        new_filename = f"{base_name}_{timestamp}.{extension}"

        # Determine domain from folder (if any)
        if "/" in filename:
            domain_key = filename.split("/")[0]
            destination_path = f"{domain_key}/{new_filename}"
        else:
            domain_key = "general"
            destination_path = new_filename

        # Move file from raw to process bucket
        storage_client = storage.Client()
        src_bucket = storage_client.bucket(raw_bucket)
        dest_bucket = storage_client.bucket(processing_bucket)

        src_blob = src_bucket.blob(filename)
        dest_blob = dest_bucket.blob(destination_path)

        if not src_blob.exists():
            logger.warning(f"File not found: {filename}")
            return event_id, event_type, raw_bucket, filename

        if dest_blob.exists():
            src_blob.delete()
            logger.info(f"Deleted duplicate from raw: {filename}")
            return event_id, event_type, raw_bucket, filename

        src_bucket.copy_blob(src_blob, dest_bucket, destination_path)
        src_blob.delete()
        time.sleep(2)

        logger.info(f"Running RAG processing for: {destination_path}")
        process_rag_corpus(processing_bucket, destination_path, domain_key.replace("_", " ").title())
        logger.info(f"Completed RAG processing for: {destination_path}")

    except Exception as e:
        logger.error(f"Function error: {e}")
        return (
            event_id if 'event_id' in locals() else "unknown",
            event_type if 'event_type' in locals() else "unknown",
            raw_bucket if 'raw_bucket' in locals() else "unknown",
            filename if 'filename' in locals() else "unknown"
        )

    return event_id, event_type, raw_bucket, filename