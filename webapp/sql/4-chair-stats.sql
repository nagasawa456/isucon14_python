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