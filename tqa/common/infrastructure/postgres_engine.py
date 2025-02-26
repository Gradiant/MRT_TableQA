import logging
from typing import Optional

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine.row import Row

from tqa.common.configuration.config import DBConfig
from tqa.common.infrastructure.abstract_engine import AbstractEngine


class PostgresEngine(AbstractEngine):
    def __init__(self, config: Optional[DBConfig] = None):
        self._db_config = config or DBConfig()
        self._engine: Engine

        self.connect()

    def connect(self):
        connection_query = str(self._db_config)
        logging.info(f"Connecting to database {connection_query}")
        self._engine = create_engine(connection_query)

    def test_connection(self) -> bool:
        result = []
        with self._engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).all()

        return len(result) == 1

    def execute(self, sql: str) -> None:
        with self._engine.connect() as connection:
            connection.execute(text(sql))

    def query(self, sql: str) -> list[Row]:
        result = None
        with self._engine.connect() as connection:
            result = connection.execute(text(sql)).all()

        return result
