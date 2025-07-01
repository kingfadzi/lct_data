SELECT
    parent.business_application_name   AS parent_app_name,
    parent.correlation_id               AS parent_correlation_id,
    child.business_application_name    AS component_app_name,
    child.correlation_id                AS component_correlation_id,
    lean_app.lean_control_service_id,
    lean_app.servicenow_app_id,
    service_instance.it_business_service,
    service_instance.it_service_instance,
    service_instance.environment,
    service_instance.Install_type
FROM public.lean_control_application AS lean_app
-- link into ServiceNow service instances
         JOIN public.vwsfitserviceinstance   AS service_instance
              ON lean_app.servicenow_app_id = service_instance.correlation_id
-- link service instances to their Business Application record
         JOIN public.vwsfbusinessapplication AS business_app
              ON service_instance.business_application_sysid = business_app.business_application_sys_id
-- include apps even if they have no child components
         LEFT JOIN public.vwsfbusinessapplication AS child
                   ON business_app.correlation_id = child.correlation_id
-- include parents even if the child has no parent
         LEFT JOIN public.vwsfbusinessapplication AS parent
                   ON child.application_parent_correlation_id = parent.correlation_id
ORDER BY
    parent.business_application_name,
    child.business_application_name;