-- A loan must not report twice for the same month.
select loan_sequence_number, reporting_month, count(*) as n
from {{ ref('stg_performance') }}
group by 1, 2
having count(*) > 1
