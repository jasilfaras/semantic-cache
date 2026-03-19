from __future__ import annotations

import unittest

from pydantic import ValidationError

from backend.config import Settings
from backend.setup_db import build_index_model


class SettingsTests(unittest.TestCase):
    def test_requires_vector_search_candidates_to_cover_limit(self) -> None:
        with self.assertRaises(ValidationError):
            Settings(vector_search_limit=5, vector_search_candidates=4)

    def test_normalizes_cors_origins(self) -> None:
        settings = Settings(cors_origins="http://localhost:5173/, http://127.0.0.1:5173/")

        self.assertEqual(
            ("http://localhost:5173", "http://127.0.0.1:5173"),
            settings.cors_origins,
        )

    def test_build_index_model_uses_configured_vector_shape(self) -> None:
        settings = Settings(vector_field_name="vector", embedding_dimensions=1536)

        index_model = build_index_model(settings)
        vector_definition = index_model["definition"]["mappings"]["fields"]["vector"]

        self.assertEqual(1536, vector_definition["dimensions"])
        self.assertEqual("knnVector", vector_definition["type"])


if __name__ == "__main__":
    unittest.main()
