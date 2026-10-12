from http import HTTPStatus

from fastapi import APIRouter
from sqlalchemy import text

from .models import Chair, Ride
from .sql import engine

router = APIRouter(prefix="/api/internal")

# これより遠い椅子は別地域にいるので割り当てない
MAX_PICKUP_DISTANCE = 400


# このAPIをインスタンス内から一定間隔で叩かせることで、椅子とライドをマッチングさせる
@router.get("/matching", status_code=HTTPStatus.NO_CONTENT)
def internal_get_matching() -> None:
    # 最も待たせているリクエストに、乗車地点へ最も早く到着できる空車をマッチさせる
    with engine.begin() as conn:
        rides = conn.execute(
            text("SELECT id, pickup_latitude, pickup_longitude, destination_latitude, destination_longitude FROM rides WHERE chair_id IS NULL ORDER BY created_at"
            )).fetchall()
        if not rides:
            return
        
    # 空いている椅子を全部取る
        chairs = conn.execute(
            text(
                """
                SELECT c.id,
                       c.latest_latitude AS latitude, 
                       c.latest_longitude AS longitude, 
                       cm.speed
                FROM chairs c
                JOIN chair_models cm ON cm.name = c.model
                WHERE c.is_active = TRUE
                  AND c.latest_latitude IS NOT NULL
                  AND c.latest_longitude IS NOT NULL
                  AND NOT EXISTS (
                    SELECT 1
                    FROM rides r
                    WHERE r.chair_id = c.id
                      AND (SELECT COUNT(rs.chair_sent_at)
                           FROM ride_statuses rs
                           WHERE rs.ride_id = r.id) < 6
                      )
                """
                ),
        ).fetchall()
        if not chairs:
            return

        # 古いライドから、乗車位置まで一定距離以内で一番早い椅子を割り当てる
        candidates = list(chairs)
        params = []
        for ride in rides:
            if not candidates:
                break
            near = [
                chair
                for chair in candidates
                if abs(chair.latitude - ride.pickup_latitude)
                + abs(chair.longitude - ride.pickup_longitude)
                < MAX_PICKUP_DISTANCE
            ]
            if not near:
                continue
            nearest = min(
                near,
                key=lambda chair: (abs(chair.latitude - ride.pickup_latitude)
                + abs(chair.longitude - ride.pickup_longitude)
                + abs(ride.pickup_latitude - ride.destination_latitude)
                + abs(ride.pickup_longitude - ride.destination_longitude)) / chair.speed,
            )
            params.append(
                {
                    "ride_id": ride.id,
                    "chair_id": nearest.id,
                }
            )
            candidates.remove(nearest)

        if not params:
            return

        conn.execute(
            text("SELECT chair_id FROM chair_unsent WHERE chair_id = :chair_id FOR UPDATE"),
            params,
        )
        conn.execute(
            text(
                """
                UPDATE rides
                SET chair_id = :chair_id
                WHERE id = :ride_id
                AND chair_id IS NULL
                """
            ),
            params,
        )
        
        conn.execute(
            text(
                """
                INSERT INTO chair_unsent (chair_id, status_id)
                SELECT :chair_id, rs.id
                FROM ride_statuses rs
                WHERE rs.ride_id = :ride_id AND rs.status = 'MATCHING'
                ON DUPLICATE KEY UPDATE
                  status_id = IF(status_id IS NULL, VALUES(status_id), status_id)
                """
            ),
            params,
        )
