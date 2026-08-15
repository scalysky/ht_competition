from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import Mock


MODULE_DIR = Path(__file__).resolve().parents[1]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from psql_runner import PsqlRunner  # noqa: E402


class PublicSchemaMetadataTests(unittest.TestCase):
    def test_public_schema_metadata_groups_catalog_rows(self) -> None:
        runner = object.__new__(PsqlRunner)
        runner._run = Mock(  # type: ignore[method-assign]
            side_effect=[
                '\n'.join(
                    [
                        '{"table":"customer","column":"id","type":"bigint",'
                        '"nullable":false,"ordinal_position":1}',
                        '{"table":"orders","column":"id","type":"bigint",'
                        '"nullable":false,"ordinal_position":1}',
                        '{"table":"orders","column":"customer_id","type":"bigint",'
                        '"nullable":false,"ordinal_position":2}',
                    ]
                ),
                '\n'.join(
                    [
                        '{"table":"customer","column":"id","ordinal_position":1}',
                        '{"table":"orders","column":"id","ordinal_position":1}',
                    ]
                ),
                '{"table":"orders","column":"customer_id",'
                '"references_table":"customer","references_column":"id"}',
            ]
        )

        metadata = runner.public_schema_metadata()

        self.assertEqual(
            metadata,
            {
                "tables": [
                    {
                        "name": "customer",
                        "columns": [
                            {
                                "name": "id",
                                "type": "bigint",
                                "nullable": False,
                                "ordinal_position": 1,
                            }
                        ],
                        "primary_key": ["id"],
                    },
                    {
                        "name": "orders",
                        "columns": [
                            {
                                "name": "id",
                                "type": "bigint",
                                "nullable": False,
                                "ordinal_position": 1,
                            },
                            {
                                "name": "customer_id",
                                "type": "bigint",
                                "nullable": False,
                                "ordinal_position": 2,
                            },
                        ],
                        "primary_key": ["id"],
                    },
                ],
                "foreign_keys": [
                    {
                        "table": "orders",
                        "column": "customer_id",
                        "references_table": "customer",
                        "references_column": "id",
                    }
                ],
            },
        )


if __name__ == "__main__":
    unittest.main()
