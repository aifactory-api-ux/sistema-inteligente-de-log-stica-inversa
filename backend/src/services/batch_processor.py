# backend/src/services/batch_processor.py

import io
import logging
import time
from datetime import datetime
from decimal import Decimal
from typing import Optional

import pandas as pd

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import settings

logger = logging.getLogger(__name__)


class BatchValidationError:
    def __init__(self, row_number: int, field: str, message: str):
        self.row_number = row_number
        self.field = field
        self.message = message

    def to_dict(self) -> dict:
        return {
            "row_number": self.row_number,
            "field": self.field,
            "message": self.message,
        }


class BatchRecord:
    def __init__(
        self,
        row_number: int,
        sku: str,
        product_name: str,
        quantity: int,
        unit_price: Decimal,
        weight_kg: Optional[Decimal] = None,
        volume_m3: Optional[Decimal] = None,
        reason_code: str = "",
        reason_description: Optional[str] = None,
        condition: str = "NEW",
        batch_id: Optional[str] = None,
        is_customized: bool = False,
    ):
        self.row_number = row_number
        self.sku = sku
        self.product_name = product_name
        self.quantity = quantity
        self.unit_price = unit_price
        self.weight_kg = weight_kg
        self.volume_m3 = volume_m3
        self.reason_code = reason_code
        self.reason_description = reason_description
        self.condition = condition
        self.batch_id = batch_id
        self.is_customized = is_customized
        self.is_valid = True
        self.validation_errors = []

    def to_dict(self) -> dict:
        return {
            "row_number": self.row_number,
            "sku": self.sku,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "weight_kg": float(self.weight_kg) if self.weight_kg else None,
            "volume_m3": float(self.volume_m3) if self.volume_m3 else None,
            "reason_code": self.reason_code,
            "reason_description": self.reason_description,
            "condition": self.condition,
            "batch_id": self.batch_id,
            "is_customized": self.is_customized,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BatchRecord":
        return cls(
            row_number=data.get("row_number", 0),
            sku=data.get("sku", ""),
            product_name=data.get("product_name", ""),
            quantity=int(data.get("quantity", 1)),
            unit_price=Decimal(str(data.get("unit_price", 0))),
            weight_kg=Decimal(str(data["weight_kg"])) if data.get("weight_kg") else None,
            volume_m3=Decimal(str(data["volume_m3"])) if data.get("volume_m3") else None,
            reason_code=data.get("reason_code", ""),
            reason_description=data.get("reason_description"),
            condition=data.get("condition", "NEW"),
            batch_id=data.get("batch_id"),
            is_customized=bool(data.get("is_customized", False)),
        )


class BatchProcessingResult:
    def __init__(
        self,
        batch_id: str,
        total_records: int = 0,
        valid_records: int = 0,
        invalid_records: int = 0,
        records: Optional[list[BatchRecord]] = None,
        processing_time_ms: int = 0,
        status: str = "PENDING",
        total_value: Decimal = Decimal("0.00"),
        total_weight: Decimal = Decimal("0.00"),
        total_volume: Decimal = Decimal("0.00"),
    ):
        self.batch_id = batch_id
        self.total_records = total_records
        self.valid_records = valid_records
        self.invalid_records = invalid_records
        self.records = records or []
        self.processing_time_ms = processing_time_ms
        self.status = status
        self.total_value = total_value
        self.total_weight = total_weight
        self.total_volume = total_volume

    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "records": [r.to_dict() for r in self.records],
            "processing_time_ms": self.processing_time_ms,
            "status": self.status,
            "total_value": float(self.total_value),
            "total_weight": float(self.total_weight),
            "total_volume": float(self.total_volume),
        }


class BatchProcessor:
    REQUIRED_COLUMNS = ["sku", "product_name", "quantity", "unit_price", "reason_code"]
    OPTIONAL_COLUMNS = ["weight_kg", "volume_m3", "reason_description", "condition", "is_customized"]
    ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

    def __init__(self):
        self.b2b_lot_size_threshold = settings.business_rules.B2B_LOT_SIZE_THRESHOLD
        self.b2b_weight_threshold_kg = settings.business_rules.B2B_WEIGHT_THRESHOLD_KG

    def validate_csv_structure(self, df: pd.DataFrame) -> tuple[bool, list[str]]:
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            return False, [f"Columna requerida faltante: {col}" for col in missing_columns]
        return True, []

    def validate_record(self, row: dict, row_number: int) -> BatchRecord:
        errors = []

        sku = row.get("sku", "").strip() if row.get("sku") else ""
        if not sku:
            errors.append("SKU es requerido")

        product_name = row.get("product_name", "").strip() if row.get("product_name") else ""
        if not product_name:
            errors.append("product_name es requerido")

        try:
            quantity = int(row.get("quantity", 0))
            if quantity < 1 or quantity > 9999:
                errors.append("quantity debe estar entre 1 y 9999")
        except (ValueError, TypeError):
            errors.append("quantity debe ser un numero entero valido")
            quantity = 0

        try:
            unit_price = Decimal(str(row.get("unit_price", 0)))
            if unit_price < 0:
                errors.append("unit_price no puede ser negativo")
        except (ValueError, TypeError):
            errors.append("unit_price debe ser un numero valido")
            unit_price = Decimal("0")

        weight_kg = None
        if row.get("weight_kg"):
            try:
                weight_kg = Decimal(str(row["weight_kg"]))
                if weight_kg < 0:
                    errors.append("weight_kg no puede ser negativo")
            except (ValueError, TypeError):
                errors.append("weight_kg debe ser un numero valido")

        volume_m3 = None
        if row.get("volume_m3"):
            try:
                volume_m3 = Decimal(str(row["volume_m3"]))
                if volume_m3 < 0:
                    errors.append("volume_m3 no puede ser negativo")
            except (ValueError, TypeError):
                errors.append("volume_m3 debe ser un numero valido")

        reason_code = row.get("reason_code", "").strip() if row.get("reason_code") else ""
        if not reason_code:
            errors.append("reason_code es requerido")

        record = BatchRecord(
            row_number=row_number,
            sku=sku,
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            weight_kg=weight_kg,
            volume_m3=volume_m3,
            reason_code=reason_code,
            reason_description=row.get("reason_description"),
            condition=str(row.get("condition", "NEW")),
            batch_id=row.get("batch_id"),
            is_customized=bool(row.get("is_customized", False)),
        )

        if errors:
            record.is_valid = False
            record.validation_errors = errors

        return record

    def process_csv(
        self,
        csv_content: bytes,
        batch_id: str,
        customer_id: str
    ) -> BatchProcessingResult:
        start_time = time.time()

        try:
            df = pd.read_csv(io.StringIO(csv_content.decode("utf-8")))
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            raise ValueError(f"Error al leer el archivo CSV: {str(e)}")

        is_valid, errors = self.validate_csv_structure(df)
        if not is_valid:
            raise ValueError(", ".join(errors))

        records = []
        valid_count = 0
        invalid_count = 0
        total_value = Decimal("0")
        total_weight = Decimal("0")
        total_volume = Decimal("0")

        for idx, row in df.iterrows():
            row_number = idx + 1
            row_dict = row.to_dict()
            row_dict["batch_id"] = batch_id

            record = self.validate_record(row_dict, row_number)

            if record.is_valid:
                valid_count += 1
                total_value += record.unit_price * record.quantity
                if record.weight_kg:
                    total_weight += record.weight_kg * record.quantity
                if record.volume_m3:
                    total_volume += record.volume_m3 * record.quantity
            else:
                invalid_count += 1

            records.append(record)

        processing_time_ms = int((time.time() - start_time) * 1000)

        if invalid_count == 0:
            status = "PENDING"
        elif valid_count == 0:
            status = "FAILED"
        else:
            status = "PARTIAL"

        return BatchProcessingResult(
            batch_id=batch_id,
            total_records=len(records),
            valid_records=valid_count,
            invalid_records=invalid_count,
            records=records,
            processing_time_ms=processing_time_ms,
            status=status,
            total_value=total_value,
            total_weight=total_weight,
            total_volume=total_volume,
        )

    def check_b2b_limits(
        self,
        total_items: int,
        total_weight_kg: Decimal
    ) -> tuple[bool, str]:
        if total_items > self.b2b_lot_size_threshold:
            return False, f"Lote excede tamano maximo de {self.b2b_lot_size_threshold} unidades"

        if float(total_weight_kg) > self.b2b_weight_threshold_kg:
            return False, f"Lote excede peso maximo de {self.b2b_weight_threshold_kg} kg"

        return True, ""


batch_processor = BatchProcessor()
