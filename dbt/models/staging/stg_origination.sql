-- One row per loan. Sentinel codes per the Freddie Mac SFLLD User Guide are turned into NULL.
with src as (
    select *
    from read_parquet('{{ var("parquet_root") }}/origination/**/*.parquet', hive_partitioning = true)
)

select
    loan_sequence_number,
    cast(vintage_year as integer)                                    as vintage_year,
    strptime(first_payment_date, '%Y%m')::date                       as first_payment_date,
    nullif(cast(nullif(trim(credit_score), '') as integer), 9999)    as credit_score,
    nullif(cast(nullif(trim(orig_dti), '') as integer), 999)         as orig_dti,
    nullif(cast(nullif(trim(orig_ltv), '') as integer), 999)         as orig_ltv,
    nullif(cast(nullif(trim(orig_cltv), '') as integer), 999)        as orig_cltv,
    cast(orig_upb as double)                                         as orig_upb,
    cast(orig_interest_rate as double)                               as orig_interest_rate,
    cast(orig_loan_term as integer)                                  as orig_loan_term,
    occupancy_status,
    loan_purpose,
    property_state,
    property_type,
    channel,
    first_time_homebuyer_flag,
    seller_name,
    servicer_name,
    source_file
from src
