from http import HTTPStatus

from fastapi import APIRouter
from sqlalchemy import text

from .models import Chair, Ride
from .sql import engine

router = APIRouter(prefix="/api/internal")


# このAPIをインスタンス内から一定間隔で叩かせることで、椅子とライドをマッチングさせる
@router.get("/matching", status_code=HTTPStatus.NO_CONTENT)
def internal_get_matching() -> None:
    # 最も待たせているリクエストに、乗車地点へ最も早く到着できる空車をマッチさせる
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT * FROM rides WHERE chair_id IS NULL ORDER BY created_at LIMIT 1"
            )).fetchone()
        if row is None:
            return
        ride = Ride.model_validate(row)
        

    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT chairs.*
                FROM chairs
                INNER JOIN chair_models
                  ON chair_models.name = chairs.model
                INNER JOIN (
                  SELECT cl.chair_id, cl.latitude, cl.longitude
                  FROM chair_locations cl
                  INNER JOIN (
                    SELECT chair_id, MAX(created_at) AS created_at
                    FROM chair_locations
                    GROUP BY chair_id
                  ) latest
                    ON latest.chair_id = cl.chair_id
                   AND latest.created_at = cl.created_at
                ) loc ON loc.chair_id = chairs.id
                WHERE chairs.is_active = TRUE
                  AND NOT EXISTS (
                    SELECT 1
                    FROM rides
                    INNER JOIN ride_statuses
                    ON ride_statuses.ride_id = rides.id
                    WHERE rides.chair_id = chairs.id
                    GROUP BY rides.id
                    HAVING COUNT(ride_statuses.chair_sent_at) <> 6
                )
                ORDER BY (
                  ABS(:pickup_latitude - loc.latitude)
                  + ABS(:pickup_longitude - loc.longitude)
                ) / chair_models.speed
                LIMIT 1
                """
                ),
                {
                    "pickup_latitude": ride.pickup_latitude,
                    "pickup_longitude": ride.pickup_longitude,
                },
        ).fetchone()
        if row is None:
            return
        matched = Chair.model_validate(row)
    assert matched is not None
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE rides SET chair_id = :chair_id WHERE id = :id"),
            {"chair_id": matched.id, "id": ride.id},
        )
