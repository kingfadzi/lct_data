#!/usr/bin/env python3

import os
import yaml
import argparse
import json

from sqlalchemy import (
    create_engine,
    Column,
    String,
    ForeignKeyConstraint,
)
from sqlalchemy.orm import (
    declarative_base,
    relationship,
    Session,
    joinedload,
)

Base = declarative_base()

class BusinessService(Base):
    __tablename__ = "vwsfitbusinessservice"
    __table_args__ = {"schema": "public"}

    it_business_service_sysid = Column(String, primary_key=True)
    service_correlation_id    = Column(String, index=True)

    # one‑to‑many → ServiceInstance
    service_instances = relationship(
        "ServiceInstance",
        back_populates="business_service",
        cascade="all, delete-orphan"
    )

class ServiceInstance(Base):
    __tablename__ = "vwsfitserviceinstance"
    __table_args__ = (
        # link to BusinessService
        ForeignKeyConstraint(
            ["it_business_service_sysid"],
            ["public.vwsfitbusinessservice.it_business_service_sysid"]
        ),
        # link to BusinessApp
        ForeignKeyConstraint(
            ["business_application_sysid"],
            ["public.vwsfbusinessapplication.business_application_sys_id"]
        ),
        {"schema": "public"}
    )

    correlation_id             = Column(String, primary_key=True)
    it_business_service_sysid  = Column(String, index=True)
    business_application_sysid = Column(String, index=True)

    # relationships
    business_service = relationship(
        "BusinessService",
        back_populates="service_instances"
    )
    business_app = relationship(
        "BusinessApp",
        back_populates="service_instances"
    )

class BusinessApp(Base):
    __tablename__ = "vwsfbusinessapplication"
    __table_args__ = {"schema": "public"}

    business_application_sys_id   = Column(String, primary_key=True)
    correlation_id                = Column(String, index=True)
    business_application_name     = Column(String)

    # back‑ref to ServiceInstance
    service_instances = relationship(
        "ServiceInstance",
        back_populates="business_app"
    )

def load_config(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def build_engine(cfg):
    db = cfg["database"]
    url = (
        f"postgresql+psycopg2://{db['user']}:{db['password']}"
        f"@{db['host']}:{db['port']}/{db['name']}"
    )
    return create_engine(url, echo=False)

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

    # load DB config & engine
    try:
        cfg = load_config(args.config)
        engine = build_engine(cfg)
    except Exception as e:
        parser.error(f"Failed to load config or connect: {e}")

    # fetch with eager loading
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

    # build JSON output
    if svc is None:
        print("[]")
        return

    result = {
        "service_correlation_id": svc.service_correlation_id,
        "it_business_service_sysid": svc.it_business_service_sysid,
        "service_instances": []
    }

    for inst in svc.service_instances:
        # if no business_app linked, skip
        if inst.business_app is None:
            continue
        result["service_instances"].append({
            "instance_id":    inst.correlation_id,
            "app_id":         inst.business_app.correlation_id,
            "app_name":       inst.business_app.business_application_name
        })

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
