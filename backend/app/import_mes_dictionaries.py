"""Import MES dictionary/reference seed into SemiPLM dictionary_items.

This imports only generated MES_* dictionary rows. It does not contain or
persist MES credentials. Generate the seed from a read-only crawl first:
mes_discovery/mes_dictionary_seed.json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy import or_

from . import models
from .database import SessionLocal


MES_DICT_PREFIXES = ("MES_",)
MES_DICT_CODES = ("MES_OBJECT_DEF", "MES_VIEW_OBJECT_DEF")


def is_mes_dict_code(code: str) -> bool:
    return code.startswith(MES_DICT_PREFIXES) or code in MES_DICT_CODES


def import_mes_dictionaries(seed_path: Path, replace: bool = True) -> dict:
    payload = json.loads(seed_path.read_text(encoding="utf-8"))
    entries = payload.get("entries", [])
    if not entries:
        raise ValueError(f"No entries found in {seed_path}")

    db = SessionLocal()
    try:
        if replace:
            db.query(models.DictionaryItem).filter(
                or_(
                    models.DictionaryItem.dict_code.like("MES_%"),
                    models.DictionaryItem.dict_code.in_(MES_DICT_CODES),
                )
            ).delete(synchronize_session=False)
            db.flush()

        inserted = 0
        updated = 0
        for row in entries:
            code = str(row.get("dict_code", "")).strip()
            if not is_mes_dict_code(code):
                continue

            item_value = str(row.get("item_value", "")).strip()
            object_scope = str(row.get("object_scope", "")).strip()
            existing = (
                db.query(models.DictionaryItem)
                .filter(
                    models.DictionaryItem.dict_code == code,
                    models.DictionaryItem.item_value == item_value,
                    models.DictionaryItem.object_scope == object_scope,
                )
                .first()
            )
            data = {
                "dict_code": code,
                "dict_name": str(row.get("dict_name", "")).strip(),
                "item_value": item_value,
                "item_label": str(row.get("item_label", "")).strip(),
                "object_scope": object_scope,
                "sequence": int(row.get("sequence") or 1),
                "status": str(row.get("status") or "启用"),
            }
            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                db.add(models.DictionaryItem(**data))
                inserted += 1

        db.commit()
        total_mes = (
            db.query(models.DictionaryItem)
            .filter(
                or_(
                    models.DictionaryItem.dict_code.like("MES_%"),
                    models.DictionaryItem.dict_code.in_(MES_DICT_CODES),
                )
            )
            .count()
        )
        return {
            "seed": str(seed_path),
            "inserted": inserted,
            "updated": updated,
            "total_mes_dictionary_items": total_mes,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    default_seed = Path(__file__).resolve().parents[2] / "mes_discovery" / "mes_dictionary_seed.json"
    parser = argparse.ArgumentParser(description="Import generated MES dictionary seed into SemiPLM.")
    parser.add_argument("--seed", type=Path, default=default_seed)
    parser.add_argument("--no-replace", action="store_true", help="Upsert without deleting existing MES_* rows first.")
    args = parser.parse_args()

    result = import_mes_dictionaries(args.seed, replace=not args.no_replace)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
