from __future__ import annotations

import argparse
import logging

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError

from backend.config import Settings, get_settings

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create the MongoDB collection and vector search index.")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args()


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )


def ensure_collection(database: Database, collection_name: str) -> Collection:
    existing_collections = set(database.list_collection_names())
    if collection_name not in existing_collections:
        logger.info("Creating collection %s.", collection_name)
        database.create_collection(collection_name)
    else:
        logger.info("Collection %s already exists.", collection_name)

    return database[collection_name]


def build_index_model(settings: Settings) -> dict[str, object]:
    return {
        "name": settings.vector_index_name,
        "definition": {
            "mappings": {
                "dynamic": True,
                "fields": {
                    settings.vector_field_name: {
                        "dimensions": settings.embedding_dimensions,
                        "similarity": "cosine",
                        "type": "knnVector",
                    }
                },
            }
        },
    }


def ensure_vector_search_index(collection: Collection, settings: Settings) -> None:
    existing_indexes = {index.get("name") for index in collection.list_search_indexes()}
    if settings.vector_index_name in existing_indexes:
        logger.info("Vector index %s already exists.", settings.vector_index_name)
        return

    logger.info("Creating vector index %s.", settings.vector_index_name)
    collection.create_search_index(model=build_index_model(settings))


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)
    settings = get_settings()

    client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5_000)

    try:
        database = client[settings.mongodb_database]
        collection = ensure_collection(database, settings.mongodb_collection)
        ensure_vector_search_index(collection, settings)
    except PyMongoError as exc:
        logger.error("MongoDB setup failed: %s", exc)
        logger.debug("MongoDB setup failure details", exc_info=exc)
        return 1
    finally:
        client.close()

    logger.info(
        "MongoDB setup complete for %s.%s.",
        settings.mongodb_database,
        settings.mongodb_collection,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
