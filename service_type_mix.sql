SELECT
    parent.business_application_name   AS parent_app_name,
    parent.correlation_id               AS parent_correlation_id,
    child.business_application_name    AS component_app_name,
    child.correlation_id                AS component_correlation_id,
    lean_app.lean_control_application_id,
    lean_app.servicenow_app_id
FROM public.lean_control_application AS lean_app
-- still require a matching ServiceInstance and its BusinessApplication
         JOIN public.vwsfitserviceinstance   AS service_instance
              ON lean_app.servicenow_app_id = service_instance.correlation_id
         JOIN public.vwsfbusinessapplication AS business_app
              ON service_instance.business_application_sysid = business_app.business_application_sys_id
-- but now allow business_app → child to be missing
         LEFT JOIN public.vwsfbusinessapplication AS child
                   ON business_app.correlation_id = child.correlation_id
-- and allow child → parent to be missing too
         LEFT JOIN public.vwsfbusinessapplication AS parent
                   ON child.application_parent_correlation_id = parent.correlation_id
ORDER BY
    parent.business_application_name,
    child.business_application_name
;