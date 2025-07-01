#!/usr/bin/env python3

import os
import yaml
import argparse
import json

from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import declarative_base, Session, aliased

# ——— Models ———
Base = declarative_base()

class BusinessService(Base):
    __tablename__ = 'vwsfitbusinessservice'
    __table_args__ = {'schema': 'public'}
    it_business_service_sysid = Column(String, primary_key=True)
    service_correlation_id    = Column(String, index=True)

class ServiceInstance(Base):
    __tablename__ = 'vwsfitserviceinstance'
    __table_args__ = {'schema': 'public'}
    correlation_id             = Column(String, primary_key=True)
    it_business_service_sysid  = Column(String)
    business_application_sysid = Column(String)
    it_service_instance        = Column('it_service_instance', String)
    environment                = Column('environment',         String)
    install_type               = Column('install_type',        String)

class LeanControlApplication(Base):
    __tablename__ = 'lean_control_application'
    __table_args__ = {'schema': 'public'}
    lean_control_service_id = Column(String, primary_key=True)
    servicenow_app_id       = Column(String, index=True)

class BusinessApp(Base):
    __tablename__ = 'vwsfbusinessapplication'
    __table_args__ = {'schema': 'public'}
    business_application_sys_id      = Column(String, primary_key=True)
    correlation_id                   = Column(String, index=True)
    business_application_name        = Column(String)
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
        prog="find_by_service_correlation_id.py",
        description="Return Business Apps hierarchy with service instances for given service_correlation_id(s)"
    )
    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='Path to YAML config (default: config.yaml)'
    )
    parser.add_argument(
        'service_correlation_ids',
        nargs='*',
        metavar='SERVICE_CORRELATION_ID',
        help=(
            'Zero or more service_correlation_id values; '
            'if omitted, returns data for all services'
        )
    )
    args = parser.parse_args()

    cfg    = load_config(args.config)
    engine = build_engine(cfg)

    ChildApp  = aliased(BusinessApp)
    ParentApp = aliased(BusinessApp)

    with Session(engine) as session:
        q = (
            session.query(
                BusinessService.service_correlation_id.label('service_id'),
                LeanControlApplication.lean_control_service_id.label('product_service_id'),
                ParentApp.correlation_id.label('parent_id'),
                ParentApp.business_application_name.label('parent_name'),
                ChildApp.correlation_id.label('child_id'),
                ChildApp.business_application_name.label('child_name'),
                ServiceInstance.correlation_id.label('instance_id'),
                ServiceInstance.it_service_instance,
                ServiceInstance.environment,
                ServiceInstance.install_type
            )
            .join(
                ServiceInstance,
                BusinessService.it_business_service_sysid == ServiceInstance.it_business_service_sysid
            )
            .join(
                LeanControlApplication,
                LeanControlApplication.servicenow_app_id == ServiceInstance.correlation_id
            )
            .join(
                ChildApp,
                ServiceInstance.business_application_sysid == ChildApp.business_application_sys_id
            )
            .outerjoin(
                ParentApp,
                ChildApp.application_parent_correlation_id == ParentApp.correlation_id
            )
        )

        if args.service_correlation_ids:
            q = q.filter(
                BusinessService.service_correlation_id.in_(
                    args.service_correlation_ids
                )
            )

        rows = q.all()

    # build nested hierarchy
    apps = {}
    for row in rows:
        sid  = row.service_id
        prod = row.product_service_id
        pid  = row.parent_id
        cid  = row.child_id

        if pid is None:
            key = (sid, prod, cid)
            apps.setdefault(key, {
                'lean_control_service_id':   prod,
                'service_correlation_id':    sid,
                'app_id':                    cid,
                'app_name':                  row.child_name,
                'service_instances':         [],
                'children':                  {}
            })['service_instances'].append({
                'instance_id':         row.instance_id,
                'it_service_instance': row.it_service_instance,
                'environment':         row.environment,
                'install_type':        row.install_type
            })
        else:
            key = (sid, prod, pid)
            parent = apps.setdefault(key, {
                'lean_control_service_id':   prod,
                'service_correlation_id':    sid,
                'app_id':                    pid,
                'app_name':                  row.parent_name,
                'service_instances':         [],
                'children':                  {}
            })
            child_dict = parent['children'].setdefault(cid, {
                'app_id':            cid,
                'app_name':          row.child_name,
                'service_instances': []
            })
            child_dict['service_instances'].append({
                'instance_id':         row.instance_id,
                'it_service_instance': row.it_service_instance,
                'environment':         row.environment,
                'install_type':        row.install_type
            })

    results = []
    for _, entry in apps.items():
        entry['children'] = list(entry['children'].values())
        results.append(entry)

    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()