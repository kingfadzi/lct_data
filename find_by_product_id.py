#!/usr/bin/env python3

import os
import yaml
import argparse
import json
import logging
import sqlparse
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import declarative_base, Session, aliased

# ——— Setup Logging ———
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# ——— Models ———
Base = declarative_base()

class LeanControlApplication(Base):
    __tablename__ = 'lean_control_application'
    __table_args__ = {'schema': 'public'}
    lean_control_service_id = Column(String, primary_key=True)
    servicenow_app_id       = Column(String, index=True)

class ProductBacklogDetails(Base):
    __tablename__ = 'lean_control_product_backlog_details'
    __table_args__ = {'schema': 'public'}
    lct_product_id  = Column(String, primary_key=True)
    jira_backlog_id = Column(String)

class ServiceInstance(Base):
    __tablename__ = 'vwsfitserviceinstance'
    __table_args__ = {'schema': 'public'}
    correlation_id             = Column(String, primary_key=True)
    it_business_service        = Column('it_business_service', String)
    business_application_sysid = Column(String)
    it_service_instance        = Column(String)
    environment                = Column(String)
    install_type               = Column(String)

class BusinessApp(Base):
    __tablename__ = 'vwsfbusinessapplication'
    __table_args__ = {'schema': 'public'}
    business_application_sys_id       = Column(String, primary_key=True)
    correlation_id                    = Column(String, index=True)
    business_application_name         = Column(String)
    application_parent_correlation_id = Column(String)

# ——— Helpers ———

def load_config(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def build_engine(cfg):
    db = cfg['database']
    url = (
        f"postgresql+psycopg2://{db['user']}:{db['password']}"
        f"@{db['host']}:{db['port']}/{db['name']}"
    )
    return create_engine(url, echo=False)

# ——— Main ———
def main():
    parser = argparse.ArgumentParser(
        prog="find_by_product_id.py",
        description="Return business services, each with nested apps and service instances"
    )
    parser.add_argument(
        '-c', '--config', default='config.yaml',
        help='Path to YAML config (default: config.yaml)'
    )
    parser.add_argument(
        'lean_control_service_ids', nargs='*', metavar='LEAN_CONTROL_SERVICE_ID',
        help='Zero or more lean_control_service_id values; if omitted, returns all'
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    engine = build_engine(cfg)

    ChildApp  = aliased(BusinessApp)
    ParentApp = aliased(BusinessApp)

    with Session(engine) as session:
        # build query
        q = (
            session.query(
                ServiceInstance.it_business_service.label('biz_service_id'),
                LeanControlApplication.lean_control_service_id.label('lean_control_service_id'),
                ProductBacklogDetails.jira_backlog_id.label('jira_backlog_id'),
                ParentApp.correlation_id.label('parent_id'),
                ParentApp.business_application_name.label('parent_name'),
                ChildApp.correlation_id.label('child_id'),
                ChildApp.business_application_name.label('child_name'),
                ServiceInstance.correlation_id.label('instance_id'),
                ServiceInstance.it_service_instance,
                ServiceInstance.environment,
                ServiceInstance.install_type
            )
            .join(LeanControlApplication,
                  LeanControlApplication.servicenow_app_id == ServiceInstance.correlation_id)
            .join(ProductBacklogDetails,
                  ProductBacklogDetails.lct_product_id == LeanControlApplication.lean_control_service_id)
            .join(ChildApp,
                  ServiceInstance.business_application_sysid == ChildApp.business_application_sys_id)
            .outerjoin(ParentApp,
                       ChildApp.application_parent_correlation_id == ParentApp.correlation_id)
        )

        if args.lean_control_service_ids:
            q = q.filter(
                LeanControlApplication.lean_control_service_id.in_(args.lean_control_service_ids)
            )

        # log SQL
        raw_sql = str(q.statement.compile(
            dialect=engine.dialect, compile_kwargs={'literal_binds': True}
        ))
        formatted_sql = sqlparse.format(raw_sql, reindent=True, keyword_case='upper')
        logger.debug("Generated SQL:\n%s", formatted_sql)

        rows = q.all()

    # group into services -> apps -> instances
    services = {}
    for row in rows:
        svc_id = row.biz_service_id
        lean_id = row.lean_control_service_id
        jira_id = row.jira_backlog_id
        pid = row.parent_id
        cid = row.child_id
        inst = {
            'instance_id': row.instance_id,
            'it_service_instance': row.it_service_instance,
            'environment': row.environment,
            'install_type': row.install_type
        }

        # initialize service
        service = services.setdefault(svc_id, {
            'it_business_service': svc_id,
            'lean_control_service_id': lean_id,
            'jira_backlog_id': jira_id,
            'apps': {}
        })

        # determine app key and record
        if pid is None:
            app_key = cid
            app_name = row.child_name
        else:
            app_key = pid
            app_name = row.parent_name

        app = service['apps'].setdefault(app_key, {
            'app_id': app_key,
            'app_name': app_name,
            'service_instances': [],
            'children': {}
        })

        # dedupe instance
        if not any(si['instance_id'] == inst['instance_id'] for si in app['service_instances']):
            app['service_instances'].append(inst)

        # children grouping
        if pid is not None:
            child = app['children'].setdefault(cid, {
                'app_id': cid,
                'app_name': row.child_name,
                'service_instances': []
            })
            if not any(si['instance_id']==inst['instance_id'] for si in child['service_instances']):
                child['service_instances'].append(inst)

    # finalize structure
    output = []
    for svc in services.values():
        # convert apps dict to list and children dicts
        apps_list = []
        for app in svc['apps'].values():
            app['children'] = list(app['children'].values())
            apps_list.append(app)
        svc['apps'] = apps_list
        output.append(svc)

    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()