SELECT
    parent.name AS parent_app_name,
    parent.correlation_id AS parent_correlation_id,
    child.name AS component_app_name,
    child.correlation_id AS component_correlation_id
FROM vwdfbusinessapplication child
         JOIN vwdfbusinessapplication parent
              ON child.application_parent_correlation_id = parent.correlation_id
WHERE child.correlation_id IN (
                               'CORR-1012',
                               'CORR-1013'
    )
ORDER BY parent.name, child.name;