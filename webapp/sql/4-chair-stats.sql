ALTER TABLE chairs
    ADD COLUMN total_ride_count INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN total_evaluation_sum INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN latest_latitude INTEGER NULL COMMENT '最新の緯度',
    ADD COLUMN latest_longitude INTEGER NULL COMMENT '最新の経度',
    ADD COLUMN total_distance INTEGER NOT NULL DEFAULT 0 COMMENT '総走行距離',
    ADD COLUMN total_distance_updated_at DATETIME(6) NULL COMMENT '総走行距離の更新日時',
    ADD COLUMN is_assignable TINYINT(1) NOT NULL DEFAULT 1 COMMENT '未完了のライドがなく割り当て可能か',
    ADD INDEX idx_active_lat (is_active, is_assignable, latest_latitude);

DROP TABLE IF EXISTS chair_unsent;
CREATE TABLE chair_unsent
(
  chair_id  VARCHAR(26) NOT NULL COMMENT '椅子ID',
  status_id VARCHAR(26) NULL COMMENT '未送信のステータスID',
  PRIMARY KEY (chair_id)
)
  COMMENT = '椅子へ未送信の状態';

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

UPDATE chairs c
JOIN rides r ON r.chair_id = c.id AND r.evaluation IS NULL
SET c.is_assignable = FALSE;