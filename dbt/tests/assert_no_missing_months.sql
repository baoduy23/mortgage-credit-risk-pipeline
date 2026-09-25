-- Monthly history must be continuous between a loan's first and last reporting month.
select loan_sequence_number
from {{ ref('stg_performance') }}
group by 1
having count(distinct reporting_month)
    <> datediff('month', min(reporting_month), max(reporting_month)) + 1
