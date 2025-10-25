select
  *
from
  application_funding
where
  code != '';

select
  *
from
  award
where
  html_content != '';

select
  *
from
  award
where
  abstract like '%artificial%';

select
  count(*)
from
  award;

select
  count(*)
from
  universities;

select
  count(*)
from
  universities
where
  latitude is null;

select
  count(*)
from
  universities
where
  street_address is null;

select
  *
from
  universities
where
  street_address is null;

select
  *
from
  universities
where
  latitude is null;

select
  *
from
  universities
where
  region is null;

select
  count(*)
from
  universities
where
  region is null;

select
  count(*)
from
  professors
where
  homepage is not null;

select
  *
from
  professors
where
  name LIKE '%Brachman%';

SELECT
  regexp_replace (name, '\s*\[[^]]*\]', '', 'g') AS cleaned_name,
  array_agg (name) AS ids,
  COUNT(*) AS count
FROM
  professors
GROUP BY
  cleaned_name
HAVING
  COUNT(*) > 1;

select
  *
from
  professors
where
  name LIKE '%Brachfeld%';

select
  *
from
  universities
where
  institution LIKE '%S+R%';

select
  *
from
  professors
where
  name LIKE '%Nanofabrication%';

SELECT
  pid,
  usename,
  application_name,
  client_addr,
  state,
  query,
  backend_start,
  query_start
FROM
  pg_stat_activity
ORDER BY
  query_start DESC;

select
  count(*)
from
  professor_areas;

select
  *
from
  professor_areas
limit
  100;