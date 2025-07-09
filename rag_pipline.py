from vertexai import rag
from vertexai.generative_models import GenerativeModel, Tool
import vertexai
from google.cloud import storage
from datetime import datetime
import json
import logging

# === Configure Logger ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# === Configuration ===
PROJECT_ID = "kishor-rag-pdlc-project"
LOCATION = "us-central1"
GENERAL_CORPUS_NAME = "pdlc-rag-corpus-3"
RESULT_BUCKET = "pdlc-rag-results-2"
RESULT_PATH = "rag_results.ndjson"

# === Vertex AI Init ===
vertexai.init(project=PROJECT_ID, location=LOCATION)

# === Add Timestamp to NDJSON Result File ===
def append_timestamp_to_result_file(bucket_name: str, blob_name: str):
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    bucket = storage.Client().bucket(bucket_name)
    blob = bucket.blob(blob_name)

    try:
        raw_lines = blob.download_as_text().splitlines()
        updated_lines = []

        for line in raw_lines:
            try:
                record = json.loads(line)
                if "Filename" in record and record["Filename"].endswith(".pdf"):
                    parts = record["Filename"].rsplit(".pdf", 1)
                    record["Filename"] = f"{parts[0]}_{timestamp_str}.pdf"
                updated_lines.append(json.dumps(record))
            except json.JSONDecodeError:
                updated_lines.append(line)

        blob.upload_from_string("\n".join(updated_lines))
        logger.info("Updated result file: gs://%s/%s", bucket_name, blob_name)

    except Exception as e:
        logger.error("Failed to update result file: %s", str(e))
        raise

# === Main Corpus Processing Function ===
def process_rag_corpus(process_bucket_name: str, filename: str, domain_name: str) -> None:
    source_gcs_path = f"gs://{process_bucket_name}/{filename}"
    result_gcs_path = f"gs://{RESULT_BUCKET}/{RESULT_PATH}"
    logger.info("Starting RAG processing for file: %s", source_gcs_path)

    try:
        # === Use fixed corpus for general, dynamic for others ===
        if domain_name.lower() == "general":
            display_name = GENERAL_CORPUS_NAME
        else:
            display_name = f"pdlc-rag-corpus-{domain_name.lower().replace(' ', '-')}"

        corpora = rag.list_corpora()
        existing_corpus = next((c for c in corpora if c.display_name == display_name), None)

        if existing_corpus:
            rag_corpus = existing_corpus
            logger.info("Using existing corpus: %s", rag_corpus.name)
        else:
            logger.info("Creating new corpus: %s", display_name)
            embedding_model_config = rag.RagEmbeddingModelConfig(
                vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
                    publisher_model="publishers/google/models/text-embedding-005"
                )
            )

            rag_corpus = rag.create_corpus(
                display_name=display_name,
                backend_config=rag.RagVectorDbConfig(
                    rag_embedding_model_config=embedding_model_config
                ),
            )

        # Clean previous result file
        storage_client = storage.Client()
        result_bucket = storage_client.bucket(RESULT_BUCKET)
        result_blob = result_bucket.blob(RESULT_PATH)

        if result_blob.exists():
            logger.warning("Previous result file found. Deleting: %s", result_gcs_path)
            result_blob.delete()

        # Start import
        response = rag.import_files(
            rag_corpus.name,
            paths=[source_gcs_path],
            transformation_config=rag.TransformationConfig(
                chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
            ),
            max_embedding_requests_per_min=1000,
            import_result_sink=result_gcs_path,
        )

        logger.info("Imported: %d | Skipped: %d", response.imported_rag_files_count, response.skipped_rag_files_count)
        append_timestamp_to_result_file(RESULT_BUCKET, RESULT_PATH)

    except Exception as e:
        logger.error("Error in RAG processing: %s", str(e))
        raise


