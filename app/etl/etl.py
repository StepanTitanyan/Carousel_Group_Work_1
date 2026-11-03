from pathlib import Path

import pandas as pd
from sqlalchemy.dialects.postgresql import insert

from Database.database import SessionLocal
from Database.models import Alternative, Carousel


DATA_DIR = Path(__file__).resolve().parent / "data"


def _read_csv(filename: str) -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / filename, comment="#")


def _upsert_rows(session, model, rows, key_columns, update_columns):
    if not rows:
        return

    statement = insert(model).values(rows)
    excluded = statement.excluded
    statement = statement.on_conflict_do_update(
        index_elements=key_columns,
        set_={column: getattr(excluded, column) for column in update_columns},
    )
    session.execute(statement)


def load_seed_data():
    carousels = _read_csv("carousels.csv").to_dict(orient="records")
    alternatives = _read_csv("alternatives.csv").to_dict(orient="records")

    with SessionLocal() as session:
        _upsert_rows(
            session,
            Carousel,
            carousels,
            key_columns=["carousel_id"],
            update_columns=["name", "total_alternatives", "visible_count", "is_active"],
        )
        _upsert_rows(
            session,
            Alternative,
            alternatives,
            key_columns=["alt_id"],
            update_columns=[
                "carousel_id",
                "title",
                "alpha",
                "beta",
                "impressions",
                "clicks",
            ],
        )
        session.commit()


if __name__ == "__main__":
    load_seed_data()
