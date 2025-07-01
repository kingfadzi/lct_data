#!/usr/bin/env python3

import os
import yaml
import argparse
import json

from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import declarative_base, Session

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

class BusinessApp(Base):
    __tablename__ = 'vwsfbusinessapplication'
    __table_args__ = {'schema': 'public'}
    business_application_sys_id   = Column(String, primary_key=True)
    correlation_id                = Column(String, index=True)
    business_application_name     = Column(String)

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
        description="Return a list of Business Apps, each with its Service Instances"
    )
    parser.add_argument(
        '-c','--config',
        default='config.yaml',
        help='Path to YAML config (default: config.yaml)'
    )
    parser.add_argument(
        'service_correlation_id',
        help='Filter by business_service.service_correlation_id'
    )
    args = parser.parse_args()

    # Load DB config & engine
    cfg = load_config(args.config)
    engine = build_engine(cfg)

    # 1) Fetch the flat join rows
    with Session(engine) as session:
        rows = (
            session
            .query(
                ServiceInstance.correlation_id  .label('instance_id'),
                ServiceInstance.it_service_instance,
                ServiceInstance.environment,
                ServiceInstance.install_type,
                BusinessApp.correlation_id      .label('app_id'),
                BusinessApp.business_application_name.label('app_name'),
            )
            .join(
                BusinessService,
                BusinessService.it_business_service_sysid ==
                ServiceInstance.it_business_service_sysid
            )
            .join(
                BusinessApp,
                ServiceInstance.business_application_sysid ==
                BusinessApp.business_application_sys_id
            )
            .filter(
                BusinessService.service_correlation_id ==
                args.service_correlation_id
            )
            .all()
        )

    # 2) Group by app_id into a nested list
    apps = {}
    for inst_id, svc_inst, env, itype, app_id, app_name in rows:
        if app_id not in apps:
            apps[app_id] = {
                'app_id': app_id,
                'app_name': app_name,
                'service_instances': []
            }
        apps[app_id]['service_instances'].append({
            'instance_id':        inst_id,
            'it_service_instance': svc_inst,
            'environment':        env,
            'install_type':       itype
        })

    result = list(apps.values())

    # 3) Pretty-print JSON
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()