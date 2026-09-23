# backend/src/routers/dropoff.py

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import text

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.schemas import UserSchema
from src.routers.auth import get_current_active_user
from src.services.qr_generator import qr_generator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dropoff", tags=["dropoff"])


PACKAGING_GUIDE = """
INSTRUCCIONES DE EMBALAJE PARA DEVOLUCIONES DROP-OFF

1. PREPARACION DEL ARTICULO:
   - Verifique que el articulo este limpio y en su estado original
   - Incluya todas las etiquetas y accesorios originales
   - Use el embalaje original si esta disponible

2. EMBALAJE:
   - Proteja el articulo con material acolchado (burbujas o papel)
   - Use una caja resistente del tamano apropiado
   - Asegure todos los elementos sueltos dentro del paquete

3. ETIQUETADO:
   - Pegue la etiqueta QR de devolucion de manera visible en el exterior
   - Asegurese de que el codigo QR no este danado ni doblado
   - Incluya una copia de la etiqueta dentro del paquete

4. PESO Y MEDIDAS:
   - El peso maximo permitido es de 15 kg
   - Dimensiones maximas: 60x40x40 cm

5. PUNTO DE ENTREGA:
   - Dirijase al punto de drop-off seleccionado
   - Entregue el paquete al personal del punto
   - Solicite un comprobante de entrega

NOTA: Para articulos hipercustomizados o defectuosos, se requiere
      recogida mediante Pickup. No intente entregarlos en puntos drop-off.
"""


@router.get("/points")
async def get_drop_off_points(
    latitude: Optional[float] = Query(None, description="Latitud del cliente"),
    longitude: Optional[float] = Query(None, description="Longitud del cliente"),
    max_distance_km: float = Query(10.0, ge=1.0, le=50.0, description="Distancia maxima en km"),
    current_user: UserSchema = Depends(get_current_active_user),
):
    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        query = text("""
            SELECT point_id, name, address, latitude, longitude,
                   max_weight_kg, max_volume_m3, opening_hours, available
            FROM drop_off_points
            WHERE available = true
            ORDER BY name
        """)

        results = db.execute(query).fetchall()

        points = []
        for row in results:
            point_lat = float(row[3])
            point_lon = float(row[4])

            distance = None
            if latitude is not None and longitude is not None:
                distance = calculate_distance(latitude, longitude, point_lat, point_lon)

            if distance is None or distance <= max_distance_km:
                address_data = row[2] if isinstance(row[2], dict) else {}
                points.append({
                    "point_id": row[0],
                    "name": row[1],
                    "address": address_data,
                    "latitude": point_lat,
                    "longitude": point_lon,
                    "max_weight_kg": float(row[5]) if row[5] else 15.0,
                    "max_volume_m3": float(row[6]) if row[6] else 0.1,
                    "opening_hours": row[7],
                    "available": row[8],
                    "distance_km": round(distance, 2) if distance else None,
                })

        points.sort(key=lambda x: x.get("distance_km") or float("inf"))

        return points
    finally:
        db.close()


@router.get("/points/{point_id}")
async def get_drop_off_point(
    point_id: str,
    current_user: UserSchema = Depends(get_current_active_user),
):
    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        query = text("""
            SELECT point_id, name, address, latitude, longitude,
                   max_weight_kg, max_volume_m3, opening_hours, available
            FROM drop_off_points
            WHERE point_id = :point_id
        """)

        result = db.execute(query, {"point_id": point_id}).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Punto de drop-off {point_id} no encontrado"
            )

        address_data = result[2] if isinstance(result[2], dict) else {}

        return {
            "point_id": result[0],
            "name": result[1],
            "address": address_data,
            "latitude": float(result[3]),
            "longitude": float(result[4]),
            "max_weight_kg": float(result[5]) if result[5] else 15.0,
            "max_volume_m3": float(result[6]) if result[6] else 0.1,
            "opening_hours": result[7],
            "available": result[8],
        }
    finally:
        db.close()


@router.get("/qr/{return_id}")
async def get_drop_off_qr(
    return_id: str,
    current_user: UserSchema = Depends(get_current_active_user),
):
    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        query = text("""
            SELECT return_id, trace_id, channel, qr_code, qr_code_expires_at,
                   status, destination, method
            FROM returns
            WHERE return_id = :return_id
        """)

        result = db.execute(query, {"return_id": return_id}).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Devolucion {return_id} no encontrada"
            )

        if result[5] not in ["PRE_APROBADO", "APROBADO"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La devolucion no esta aprobada para drop-off"
            )

        if result[7] != "DROP_OFF":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta devolucion no utiliza metodo drop-off"
            )

        qr_data = qr_generator.generate_return_qr(
            return_id=result[0],
            trace_id=str(result[1]),
            channel=result[2],
        )

        update_query = text("""
            UPDATE returns
            SET qr_code = :qr_code,
                qr_code_expires_at = :expires_at
            WHERE return_id = :return_id
        """)
        db.execute(update_query, {
            "qr_code": qr_data["qr_code"],
            "expires_at": qr_data["expires_at"],
            "return_id": return_id,
        })
        db.commit()

        return {
            "return_id": return_id,
            "qr_code": qr_data["qr_code"],
            "token": qr_data["token"],
            "expires_at": qr_data["expires_at"],
            "instructions": "Muestre este codigo QR en el punto de drop-off",
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating QR for return {return_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar codigo QR: {str(e)}"
        )
    finally:
        db.close()


@router.get("/instructions/{return_id}")
async def get_packaging_instructions(
    return_id: str,
    current_user: UserSchema = Depends(get_current_active_user),
):
    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        query = text("""
            SELECT return_id, channel, items, destination, method
            FROM returns
            WHERE return_id = :return_id
        """)

        result = db.execute(query, {"return_id": return_id}).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Devolucion {return_id} no encontrada"
            )

        return {
            "return_id": return_id,
            "channel": result[1],
            "destination": result[3],
            "method": result[4],
            "packaging_guide": PACKAGING_GUIDE,
            "general_instructions": [
                "Verifique que el articulo este en su estado original",
                "Incluya todos los accesorios y etiquetas",
                "Embale correctamente para evitar danos durante el transporte",
                "Pegue la etiqueta QR de manera visible en el exterior",
            ],
            "drop_off_instructions": [
                "Dirijase al punto de drop-off mas cercano",
                "Entregue el paquete al personal del punto",
                "Solicite un comprobante de entrega con fecha",
            ],
            "pickup_instructions": [
                "Espere la llegada del transportista en la fecha programada",
                "Tenga el paquete listo y accesible",
                "Verifique la identificacion del transportista",
            ],
        }
    finally:
        db.close()


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math
    R = 6371

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c
