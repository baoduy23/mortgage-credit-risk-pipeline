-- FICO scores run 300-850; anything else outside the 9999 "not available" code is bad data.
select loan_sequence_number, credit_score
from {{ ref('stg_origination') }}
where credit_score not between 300 and 850
