import os
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import OpenAI
import chromadb


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

load_dotenv()

APP_TITLE = "RAG API (Chroma Cloud + OpenAI)"
COLLECTION_NAME = "netweb_knowledge_base"
OPENAI_MODEL = "gpt-4.1-nano"
TOP_K = 10


# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------

def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )


configure_logging()
logger = logging.getLogger("rag-api")


# ------------------------------------------------------------------
# Environment Validation
# ------------------------------------------------------------------

def validate_env() -> None:
    required_vars = [
        "OPENAI_API_KEY",
        "CHROMA_API_KEY",
        "CHROMA_TENANT",
        "CHROMA_DATABASE",
    ]

    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")


validate_env()


# ------------------------------------------------------------------
# Clients
# ------------------------------------------------------------------

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_chroma_client() -> chromadb.CloudClient:
    return chromadb.CloudClient(
        api_key=os.getenv("CHROMA_API_KEY"),
        tenant=os.getenv("CHROMA_TENANT"),
        database=os.getenv("CHROMA_DATABASE"),
    )


# ------------------------------------------------------------------
# API Models
# ------------------------------------------------------------------

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, description="User question")


class QueryResponse(BaseModel):
    answer: str


# ------------------------------------------------------------------
# FastAPI App
# ------------------------------------------------------------------

app = FastAPI(title=APP_TITLE)


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest) -> QueryResponse:
    """
    RAG flow:
    1. Retrieve context from Chroma Cloud
    2. Generate answer using OpenAI
    """
    logger.info("Query received")

    try:
        # --- Retrieval ---
        chroma_client = get_chroma_client()
        collection = chroma_client.get_collection(name=COLLECTION_NAME)

        search_results = collection.query(
            query_texts=[request.question],
            n_results=TOP_K,
        )

        documents = search_results.get("documents", [[]])[0]
        if not documents:
            logger.warning("No relevant documents found")
            return QueryResponse(answer="No relevant information found.")

        context = "\n\n".join(documents)
        approx_token_count = len(context.split())

        logger.info(
            "Context prepared | chunks=%s approx_tokens=%s",
            len(documents),
            approx_token_count,
        )

        # --- Generation ---
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a factual assistant. "
                        "Answer strictly using the provided context. "
                        "If the answer is not present, say you don't know."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {request.question}",
                },
            ],
            temperature=0,
        )

        answer = response.choices[0].message.content
        logger.info("Answer generated successfully")

        return QueryResponse(answer=answer)

    except Exception as exc:
        logger.exception("RAG query failed")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


# ------------------------------------------------------------------
# Local Dev Runner
# ------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
