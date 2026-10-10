ALTER TABLE chairs
    ADD COLUMN total_ride_count INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN total_evaluation_sum INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN latest_latitude INTEGER NULL COMMENT '最新の緯度',
    ADD COLUMN latest_longitude INTEGER NULL COMMENT '最新の経度',
    ADD COLUMN total_distance INTEGER NOT NULL DEFAULT 0 COMMENT '総走行距離',
    ADD COLUMN total_distance_updated_at DATETIME(6) NULL COMMENT '総走行距離の更新日時',
    ADD INDEX idx_active_lat (is_active, latest_latitude);

UPDATE chairs c
JOIN (
  SELECT r.chair_id,
         COUNT(*) AS total_ride_count,
         SUM(r.evaluation) AS total_evaluation_sum
  FROM rides r
  WHERE r.chair_id IS NOT NULL
    AND r.evaluation IS NOT NULL
    AND EXISTS (SELECT 1 FROM ride_statuses rs WHERE rs.ride_id = r.id AND rs.status = 'ARRIVED')
    AND EXISTS (SELECT 1 FROM ride_statuses rs WHERE rs.ride_id = r.id AND rs.status = 'CARRYING')
    AND EXISTS (SELECT 1 FROM ride_statuses rs WHERE rs.ride_id = r.id AND rs.status = 'COMPLETED')
  GROUP BY r.chair_id
) s ON s.chair_id = c.id
SET c.total_ride_count = s.total_ride_count,
    c.total_evaluation_sum = s.total_evaluation_sum;