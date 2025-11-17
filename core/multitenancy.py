"""
Multi-tenancy Module
Provides organization and user isolation for SaaS deployment
"""

from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime
import logging
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

Base = declarative_base()


class OrganizationORM(Base):
    """Organization model"""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    plan = Column(String(50), default="free")  # free, pro, enterprise
    settings = Column(Text)  # JSON settings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    users = relationship("UserORM", back_populates="organization")
    transactions = relationship("TransactionRecordORM", back_populates="organization")


class UserORM(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    role = Column(String(50), default="member")  # admin, member, viewer
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = relationship("OrganizationORM", back_populates="users")


@dataclass
class TenantContext:
    """Tenant context for request isolation"""
    organization_id: int
    organization_slug: str
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None


class MultiTenancyService:
    """Service for multi-tenancy operations"""
    
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
    
    def get_tenant_from_api_key(self, api_key_info: Dict) -> Optional[TenantContext]:
        """
        Extract tenant context from API key info
        
        Args:
            api_key_info: API key information dict
            
        Returns:
            TenantContext or None
        """
        org_id = api_key_info.get('organization_id')
        user_id = api_key_info.get('user_id')
        
        if not org_id:
            return None
        
        # Get organization details
        if self.db_session:
            try:
                org = self.db_session.query(OrganizationORM).filter(
                    OrganizationORM.id == org_id
                ).first()
                
                if org:
                    return TenantContext(
                        organization_id=org.id,
                        organization_slug=org.slug,
                        user_id=user_id,
                        user_email=api_key_info.get('user_email'),
                        user_role=api_key_info.get('user_role', 'member')
                    )
            except Exception as e:
                logger.error(f"Error getting tenant context: {e}")
        
        # Fallback to API key info
        return TenantContext(
            organization_id=org_id,
            organization_slug=f"org-{org_id}",
            user_id=user_id,
            user_email=api_key_info.get('user_email'),
            user_role=api_key_info.get('user_role', 'member')
        )
    
    def create_organization(
        self,
        name: str,
        slug: Optional[str] = None,
        plan: str = "free"
    ) -> Optional[OrganizationORM]:
        """
        Create a new organization
        
        Args:
            name: Organization name
            slug: Organization slug (auto-generated if not provided)
            plan: Subscription plan
            
        Returns:
            Created organization or None
        """
        if not self.db_session:
            logger.warning("No database session - cannot create organization")
            return None
        
        try:
            # Generate slug if not provided
            if not slug:
                import re
                slug = re.sub(r'[^a-z0-9-]', '', name.lower().replace(' ', '-'))
            
            org = OrganizationORM(
                name=name,
                slug=slug,
                plan=plan,
                settings='{}'
            )
            
            self.db_session.add(org)
            self.db_session.commit()
            self.db_session.refresh(org)
            
            logger.info(f"Created organization: {name} (slug: {slug})")
            return org
            
        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            self.db_session.rollback()
            return None
    
    def get_organization(self, organization_id: int) -> Optional[OrganizationORM]:
        """Get organization by ID"""
        if not self.db_session:
            return None
        
        try:
            return self.db_session.query(OrganizationORM).filter(
                OrganizationORM.id == organization_id
            ).first()
        except Exception as e:
            logger.error(f"Error getting organization: {e}")
            return None


# Global instance
multitenancy_service: Optional[MultiTenancyService] = None


def init_multitenancy(db_session: Optional[Session] = None):
    """Initialize multi-tenancy service"""
    global multitenancy_service
    multitenancy_service = MultiTenancyService(db_session)
    logger.info("Multi-tenancy service initialized")


def get_tenant_context(api_key_info: Dict) -> Optional[TenantContext]:
    """Get tenant context from API key info"""
    if multitenancy_service:
        return multitenancy_service.get_tenant_from_api_key(api_key_info)
    return None
