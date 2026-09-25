-- One row per loan per reporting month.
with src as (
    select *
    from read_parquet('{{ var("parquet_root") }}/performance/**/*.parquet', hive_partitioning = true)
)

select
    loan_sequence_number,
    strptime(monthly_reporting_period, '%Y%m')::date        as reporting_month,
    cast(loan_age as integer)                                as loan_age,
    cast(current_actual_upb as double)                       as current_upb,
    current_loan_delinquency_status                          as delinquency_status_raw,
    -- Status is months delinquent ('0', '1', '2', ...); 'RA' = REO acquisition.
    case
        when current_loan_delinquency_status = 'RA' then 'reo'
        when try_cast(current_loan_delinquency_status as integer) = 0 then 'current'
        when try_cast(current_loan_delinquency_status as integer) = 1 then '30dpd'
        when try_cast(current_loan_delinquency_status as integer) = 2 then '60dpd'
        when try_cast(current_loan_delinquency_status as integer) >= 3 then '90plus_dpd'
    end                                                      as dpd_bucket,
    nullif(trim(zero_balance_code), '')                      as zero_balance_code,
    cast(nullif(trim(current_interest_rate), '') as double)  as current_interest_rate,
    nullif(trim(modification_flag), '')                      as modification_flag,
    cast(nullif(trim(actual_loss_calculation), '') as double) as actual_loss,
    source_file
from src
