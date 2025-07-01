#!/usr/bin/env python3

import os
import yaml
import argparse
import json

from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import declarative_base, Session, aliased

# ——— Models ———
Base = declarative_base()

class LeanControlApplication(Base):
    __tablename__ = 'lean_control_application'
    __table_args__ = {'schema': 'public'}
    lean_control_service_id = Column(String, primary_key=True)
    servicenow_app_id       = Column(String, index=True)

class ServiceInstance(Base):
    __tablename__ = 'vwsfitserviceinstance'
    __table_args__ = {'schema': 'public'}
    correlation_id             = Column(String, primary_key=True)
    it_business_service_sysid  = Column(String)
    business_application_sysid = Column(String)
    it_service_instance        = Column(String)
    environment                = Column(String)
    install_type               = Column(String)

class BusinessApp(Base):
    __tablename__ = 'vwsfbusinessapplication'
    __table_args__ = {'schema': 'public'}
    business_application_sys_id      = Column(String, primary_key=True)
    correlation_id                   = Column(String, index=True)
    business_application_name        = Column(String)
    application_parent_correlation_id = Column(String)

# ——— Helpers ———

def load_config(path):
    """Load DB credentials from YAML."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def build_engine(cfg):
    """Construct a SQLAlchemy engine from the config dict."""
    db = cfg['database']
    url = (
        f"postgresql+psycopg2://{db['user']}:{db['password']}"
        f"@{db['host']}:{db['port']}/{db['name']}"
    )
    return create_engine(url, echo=False)

# ——— Main ———

def main():
    parser = argparse.ArgumentParser(
        description="Return a list of parent Business Apps and their children, each with Service Instances"
    )
    parser.add_argument(
        '-c','--config',
        default='config.yaml',
        help='Path to YAML config (default: config.yaml)'
    )
    parser.add_argument(
        'lean_control_service_id',
        help='Filter by lean_control_application.lean_control_service_id'
    )
    args = parser.parse_args()

    # Load DB config & engine
    cfg    = load_config(args.config)
    engine = build_engine(cfg)

    # aliases for self‐join
    ChildApp  = aliased(BusinessApp)
    ParentApp = aliased(BusinessApp)

    # 1) Fetch the flat join rows
    with Session(engine) as session:
        rows = (
            session
            .query(
                ParentApp.correlation_id.label('parent_id'),
                ParentApp.business_application_name.label('parent_name'),
                ChildApp.correlation_id.label('child_id'),
                ChildApp.business_application_name.label('child_name'),
                ServiceInstance.correlation_id.label('instance_id'),
                ServiceInstance.it_service_instance,
                ServiceInstance.environment,
                ServiceInstance.install_type
            )
            # start from lean_control_application → service_instance
            .join(
                LeanControlApplication,
                LeanControlApplication.servicenow_app_id == ServiceInstance.correlation_id
            )
            # then to the child BusinessApp
            .join(
                ChildApp,
                ServiceInstance.business_application_sysid == ChildApp.business_application_sys_id
            )
            # then optionally to its parent BusinessApp
            .outerjoin(
                ParentApp,
                ChildApp.application_parent_correlation_id == ParentApp.correlation_id
            )
            .filter(
                LeanControlApplication.lean_control_service_id ==
                args.lean_control_service_id
            )
            .all()
        )

    # 2) Build nested structure
    apps = {}
    for row in rows:
        pid = row.parent_id
        cid = row.child_id

        if pid is None:
            # no parent → this child is a top‐level app
            app_key = cid
            if app_key not in apps:
                apps[app_key] = {
                    'app_id':           cid,
                    'app_name':         row.child_name,
                    'service_instances': [],
                    'children':         []
                }
            apps[app_key]['service_instances'].append({
                'instance_id':         row.instance_id,
                'it_service_instance': row.it_service_instance,
                'environment':         row.environment,
                'install_type':        row.install_type
            })

        else:
            # has a parent → ensure parent entry
            if pid not in apps:
                apps[pid] = {
                    'app_id':            pid,
                    'app_name':          row.parent_name,
                    'service_instances': [],
                    'children':          {}
                }
            # ensure child entry under this parent
            children = apps[pid]['children']
            if cid not in children:
                children[cid] = {
                    'app_id':            cid,
                    'app_name':          row.child_name,
                    'service_instances': []
                }
            children[cid]['service_instances'].append({
                'instance_id':         row.instance_id,
                'it_service_instance': row.it_service_instance,
                'environment':         row.environment,
                'install_type':        row.install_type
            })

    # Convert any children dicts to lists
    for app in apps.values():
        if isinstance(app['children'], dict):
            app['children'] = list(app['children'].values())

    result = list(apps.values())

    # 3) Pretty-print JSON
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()