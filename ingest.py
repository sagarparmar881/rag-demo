import asyncio
import os
import hashlib
import logging
from typing import List, Tuple

from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

load_dotenv()

COLLECTION_NAME = "netweb_knowledge_base"

MAX_BYTES = 15_800
UPSERT_BATCH_SIZE = 25

CRAWL_MAX_DEPTH = 2
CRAWL_MAX_PAGES = 30

TEXT_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=4000,
    chunk_overlap=300,
    separators=["\n# ", "\n## ", "\n\n", ". "],
)


# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------

def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )


logger = logging.getLogger("kb-ingestion")


# ------------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------------

def compute_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def split_if_needed(text: str) -> List[str]:
    byte_size = len(text.encode("utf-8"))

    if byte_size <= MAX_BYTES:
        return [text]

    return TEXT_SPLITTER.split_text(text)


def validate_chroma_env() -> None:
    required_vars = [
        "CHROMA_API_KEY",
        "CHROMA_TENANT",
        "CHROMA_DATABASE",
    ]

    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")


# ------------------------------------------------------------------
# Crawling
# ------------------------------------------------------------------

async def crawl_site(url: str):
    logger.info("Starting crawl | url=%s depth=%s pages=%s",
                url, CRAWL_MAX_DEPTH, CRAWL_MAX_PAGES)

    strategy = BFSDeepCrawlStrategy(
        max_depth=CRAWL_MAX_DEPTH,
        max_pages=CRAWL_MAX_PAGES,
    )

    config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.ENABLED,
    )

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(url=url, config=config)

    result_list = results if isinstance(results, list) else [results]
    logger.info("Crawl completed | pages_fetched=%s", len(result_list))

    return result_list


# ------------------------------------------------------------------
# Document Processing
# ------------------------------------------------------------------

def extract_documents(results) -> Tuple[List[str], List[dict], List[str]]:
    documents: List[str] = []
    metadatas: List[dict] = []
    ids: List[str] = []

    seen_ids = set()

    for result in results:
        if not result.success or not result.markdown:
            logger.warning("Skipping failed page | url=%s", result.url)
            continue

        chunks = split_if_needed(result.markdown)
        title = result.metadata.get("title", "Webpage")

        logger.info(
            "Processing page | url=%s chunks=%s",
            result.url,
            len(chunks),
        )

        for chunk in chunks:
            content_hash = compute_hash(chunk)
            chunk_id = f"{result.url}#{content_hash}"

            if chunk_id in seen_ids:
                logger.debug("Duplicate chunk skipped | id=%s", chunk_id)
                continue

            doc_text = (
                f"Source: {title}\n"
                f"URL: {result.url}\n\n"
                f"{chunk}"
            )

            documents.append(doc_text)
            metadatas.append({
                "source": result.url,
                "title": title,
            })
            ids.append(chunk_id)
            seen_ids.add(chunk_id)

    logger.info(
        "Document extraction completed | documents=%s",
        len(documents),
    )

    return documents, metadatas, ids


# ------------------------------------------------------------------
# Persistence
# ------------------------------------------------------------------

def upsert_to_chroma(
    documents: List[str],
    metadatas: List[dict],
    ids: List[str],
) -> None:
    validate_chroma_env()

    logger.info("Connecting to Chroma Cloud")

    client = chromadb.CloudClient(
        api_key=os.getenv("CHROMA_API_KEY"),
        tenant=os.getenv("CHROMA_TENANT"),
        database=os.getenv("CHROMA_DATABASE"),
    )

    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    for i in range(0, len(documents), UPSERT_BATCH_SIZE):
        batch_size = len(documents[i:i + UPSERT_BATCH_SIZE])
        logger.info("Upserting batch | size=%s", batch_size)

        collection.upsert(
            documents=documents[i:i + UPSERT_BATCH_SIZE],
            metadatas=metadatas[i:i + UPSERT_BATCH_SIZE],
            ids=ids[i:i + UPSERT_BATCH_SIZE],
        )

    logger.info("Upsert completed | collection=%s", COLLECTION_NAME)


# ------------------------------------------------------------------
# Main Entry Point
# ------------------------------------------------------------------

async def main(url: str) -> None:
    configure_logging()

    logger.info("KB ingestion started")

    results = await crawl_site(url)
    documents, metadatas, ids = extract_documents(results)

    if not documents:
        logger.warning("No documents extracted | exiting")
        return

    try:
        upsert_to_chroma(documents, metadatas, ids)
        logger.info("KB ingestion successful")
    except Exception as exc:
        logger.exception("KB ingestion failed")
        raise exc


if __name__ == "__main__":
    asyncio.run(main("https://netweb.biz"))
