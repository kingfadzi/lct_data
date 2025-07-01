from sqlalchemy import (
    create_engine, Column, String, Integer, ForeignKey
)
from sqlalchemy.orm import (
    declarative_base, relationship, Session
)

Base = declarative_base()

class BusinessService(Base):
    __tablename__ = 'vwsfitbusinessservice'
    schema    = 'public'

    it_business_service_sysid = Column(String, primary_key=True)
    service_correlation_id    = Column(String, index=True)
    # backref to service_instances
    service_instances = relationship(
        "ServiceInstance",
        back_populates="business_service"
    )

class ServiceInstance(Base):
    __tablename__ = 'vwsfitserviceinstance'
    schema    = 'public'

    correlation_id             = Column(String, primary_key=True)
    it_business_service_sysid  = Column(String, ForeignKey(
        f"{BusinessService.__tablename__}.it_business_service_sysid"))
    business_application_sysid = Column(String, index=True)

    # relationships
    business_service = relationship(
        "BusinessService",
        back_populates="service_instances"
    )
    business_app = relationship(
        "BusinessApp",
        back_populates="service_instances",
        primaryjoin="ServiceInstance.business_application_sysid==BusinessApp.business_application_sys_id"
    )

class BusinessApp(Base):
    __tablename__ = 'vwsfbusinessapplication'
    schema    = 'public'

    business_application_sys_id = Column(String, primary_key=True)
    correlation_id             = Column(String, index=True)
    business_application_name  = Column(String)

    # backref to service_instances
    service_instances = relationship(
        "ServiceInstance",
        back_populates="business_app"
    )
