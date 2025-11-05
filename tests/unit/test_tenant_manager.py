"""
Unit tests for tenant manager
"""
import pytest
from app.core.tenant_manager import TenantContext


class TestTenantContext:
    """Tests for TenantContext"""
    
    def test_set_and_get_tenant(self):
        """Test setting and getting tenant"""
        TenantContext.set_tenant("123")
        
        tenant_id = TenantContext.get_tenant()
        
        assert tenant_id == "123"
    
    def test_clear_tenant(self):
        """Test clearing tenant"""
        TenantContext.set_tenant("123")
        TenantContext.clear_tenant()
        
        tenant_id = TenantContext.get_tenant()
        
        assert tenant_id is None
    
    def test_is_tenant_context(self):
        """Test checking tenant context"""
        TenantContext.set_tenant("123")
        
        assert TenantContext.is_tenant_context() is True
        
        TenantContext.clear_tenant()
        
        assert TenantContext.is_tenant_context() is False
    
    def test_require_tenant_with_tenant(self):
        """Test require_tenant when tenant is set"""
        TenantContext.set_tenant("123")
        
        tenant_id = TenantContext.require_tenant()
        
        assert tenant_id == "123"
    
    def test_require_tenant_without_tenant(self):
        """Test require_tenant when tenant is not set"""
        TenantContext.clear_tenant()
        
        with pytest.raises(Exception):  # HTTPException
            TenantContext.require_tenant()

