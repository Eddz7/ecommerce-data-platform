SELECT
    source_table,
    split_part(rejection_reason, ':', 1) AS reason_category,
    COUNT(*) AS occurrences
FROM rejected_records
GROUP BY source_table, reason_category
ORDER BY source_table, occurrences DESC;
