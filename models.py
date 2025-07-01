#!/usr/bin/env python3

import os
import yaml
import argparse
import json

from sqlalchemy import (
    create_engine,
    Column,
    String
)
from sqlalchemy.orm import (
    declarative_base,
    relationship,
    Session,
    joinedload,
    foreign
)

# ——— Define your ORM models ———
Base = declarative_base()

class BusinessService(Base):
    __tablename__ = "vwsfitbusinessservice"
    __table_args__ = {"schema": "public"}

    it_business_service_sysid = Column(String, primary_key=True)
    service_correlation_id    = Column(String, index=True)

    service_instances = relationship(
        "ServiceInstance",
        back_populates="business_service",
        primaryjoin=(
            "BusinessService.it_business_service_sysid"
            "==foreign(ServiceInstance.it_business_service_sysid)"
        )
    )

class ServiceInstance(Base):
    __tablename__ = "vwsfitserviceinstance"
    __table_args__ = {"schema": "public"}

    correlation_id             = Column(String, primary_key=True)
    it_business_service_sysid  = Column(String, index=True)
    business_application_sysid = Column(String, index=True)

    # extra columns you referenced in your SELECT
    it_service_instance = Column("it_service_instance", String)
    environment         = Column("environment",        String)
    install_type        = Column("Install_type",       String)

    business_service = relationship(
        "BusinessService",
        back_populates="service_instances",
        primaryjoin=(
            "foreign(ServiceInstance.it_business_service_sysid)"
            "==BusinessService.it_business_service_sysid"
        )
    )
    business_app = relationship(
        "BusinessApp",
        back_populates="service_instances",
        primaryjoin=(
            "foreign(ServiceInstance.business_application_sysid)"
            "==BusinessApp.business_application_sys_id"
        )
    )

class BusinessApp(Base):
    __tablename__ = "vwsfbusinessapplication"
    __table_args__ = {"schema": "public"}

    business_application_sys_id  = Column(String, primary_key=True)
    correlation_id               = Column(String, index=True)
    business_application_name    = Column(String)

    service_instances = relationship(
        "ServiceInstance",
        back_populates="business_app",
        primaryjoin=(
            "BusinessApp.business_application_sys_id"
            "==foreign(ServiceInstance.business_application_sysid)"
        )
    )

# ——— Helpers ———

def load_config(path):
    """Load DB credentials from YAML."""
    with open(path, "r") as f:
        return yaml.safe_load(f)

def build_engine(cfg):
    """Build a SQLAlchemy engine from the config dict."""
    db = cfg["database"]
    url = (
        f"postgresql+psycopg2://{db['user']}:{db['password']}"
        f"@{db['host']}:{db['port']}/{db['name']}"
    )
    return create_engine(url, echo=False)

# ——— Main CLI ———

def main():
    parser = argparse.ArgumentParser(
        description="Return a BusinessService → ServiceInstances → BusinessApp hierarchy"
    )
    parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="Path to YAML config (default: config.yaml)"
    )
    parser.add_argument(
        "service_correlation_id",
        help="The business_service.service_correlation_id to look up"
    )
    args = parser.parse_args()

    # Load config & engine
    try:
        cfg = load_config(args.config)
        engine = build_engine(cfg)
    except Exception as e:
        parser.error(f"Failed to load config or connect: {e}")

    # Fetch with eager loading
    with Session(engine) as session:
        svc = (
            session
            .query(BusinessService)
            .options(
                joinedload(BusinessService.service_instances)
                .joinedload(ServiceInstance.business_app)
            )
            .filter_by(service_correlation_id=args.service_correlation_id)
            .one_or_none()
        )

    # Build nested JSON
    if svc is None:
        print("[]")
        return

    result = {
        "service_correlation_id": svc.service_correlation_id,
        "it_business_service_sysid": svc.it_business_service_sysid,
        "service_instances": []
    }

    for inst in svc.service_instances:
        if inst.business_app is None:
            continue
        result["service_instances"].append({
            "instance_id":         inst.correlation_id,
            "it_service_instance": inst.it_service_instance,
            "environment":         inst.environment,
            "install_type":        inst.install_type,
            "app": {
                "id":   inst.business_app.correlation_id,
                "name": inst.business_app.business_application_name
            }
        })

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()