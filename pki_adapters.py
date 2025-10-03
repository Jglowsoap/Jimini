#!/usr/bin/env python3
"""
🔌 PKI SYSTEM ADAPTERS & MIDDLEWARE
===================================

Gateway adapters for LDAP, Entrust IDG, UMS, DB2, ServiceNow integration.
Intercepts requests/responses and applies Jimini policy enforcement.
"""

import httpx
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from fastapi import HTTPException
from contextlib import asynccontextmanager

from jimini_gateway import JiminiPolicyEngine, SystemType, Direction, DecisionType

logger = logging.getLogger("jimini.adapters")

# 🔌 **BASE ADAPTER CLASS**

class PKISystemAdapter:
    """Base class for PKI system adapters"""
    
    def __init__(self, system_type: SystemType, base_url: str, engine: JiminiPolicyEngine):
        self.system_type = system_type
        self.base_url = base_url
        self.engine = engine
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def intercept_request(self, 
                              method: str, 
                              endpoint: str, 
                              data: Dict[str, Any],
                              tenant_id: str,
                              session_id: str) -> Dict[str, Any]:
        """Intercept and evaluate outbound request"""
        
        # Serialize request data for evaluation
        request_content = json.dumps(data, separators=(',', ':'))
        
        # Evaluate against policies
        decision = await self.engine.evaluate_request(
            content=request_content,
            system=self.system_type,
            endpoint=endpoint,
            direction=Direction.OUTBOUND,
            tenant_id=tenant_id,
            session_id=session_id
        )
        
        # Handle decision
        if decision.decision == DecisionType.BLOCK:
            logger.warning(f"BLOCKED {self.system_type.value} request to {endpoint}")
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Request blocked by policy",
                    "decision": decision.dict(),
                    "request_id": decision.request_id
                }
            )
        
        # Apply masking for flagged content
        if decision.decision == DecisionType.FLAG and decision.masked_fields:
            masked_data = self._apply_masking(data, decision.masked_fields, tenant_id, session_id)
            logger.info(f"Applied masking to {len(decision.masked_fields)} fields")
            return masked_data
        
        return data
    
    def _apply_masking(self, data: Dict[str, Any], masked_fields: List[str], tenant_id: str, session_id: str) -> Dict[str, Any]:
        """Apply field-level masking to request data"""
        masked_data = data.copy()
        
        for field_path in masked_fields:
            # Simple dot notation field masking
            if '.' in field_path:
                parts = field_path.split('.')
                current = masked_data
                for part in parts[:-1]:
                    if part in current and isinstance(current[part], dict):
                        current = current[part]
                    else:
                        break
                else:
                    final_key = parts[-1]
                    if final_key in current:
                        original_value = str(current[final_key])
                        current[final_key] = self.engine.mask_field(
                            original_value, field_path, tenant_id, session_id
                        )
        
        return masked_data

# 🗂️ **LDAP ADAPTER**

class LDAPAdapter(PKISystemAdapter):
    """Adapter for LDAP directory services"""
    
    def __init__(self, ldap_server: str, engine: JiminiPolicyEngine):
        super().__init__(SystemType.LDAP, ldap_server, engine)
    
    async def search(self, 
                    base_dn: str, 
                    search_filter: str, 
                    attributes: List[str],
                    tenant_id: str,
                    session_id: str) -> Dict[str, Any]:
        """Secure LDAP search with policy enforcement"""
        
        search_data = {
            "base_dn": base_dn,
            "filter": search_filter,
            "attributes": attributes
        }
        
        # Intercept and validate
        validated_data = await self.intercept_request(
            method="SEARCH",
            endpoint="/ldap/search",
            data=search_data,
            tenant_id=tenant_id,
            session_id=session_id
        )
        
        # Simulate LDAP search (replace with actual LDAP client)
        search_results = {
            "entries": [
                {
                    "dn": f"cn=user1,{base_dn}",
                    "attributes": {
                        "cn": "John Doe",
                        "mail": "john.doe@agency.gov",
                        "telephoneNumber": "555-123-4567",
                        "employeeID": "E12345"
                    }
                }
            ],
            "result_code": 0,
            "message": "Search completed successfully"
        }
        
        # Apply response filtering
        return await self._filter_response(search_results, tenant_id, session_id)
    
    async def _filter_response(self, response: Dict[str, Any], tenant_id: str, session_id: str) -> Dict[str, Any]:
        """Filter LDAP response for PII"""
        response_content = json.dumps(response, separators=(',', ':'))
        
        decision = await self.engine.evaluate_request(
            content=response_content,
            system=self.system_type,
            endpoint="/ldap/response",
            direction=Direction.INBOUND,
            tenant_id=tenant_id,
            session_id=session_id
        )
        
        if decision.masked_fields:
            # Apply masking to response
            filtered_response = self._apply_masking(response, decision.masked_fields, tenant_id, session_id)
            return filtered_response
        
        return response

# 🔐 **ENTRUST IDG ADAPTER**

class EntrustIDGAdapter(PKISystemAdapter):
    """Adapter for Entrust Identity Guard"""
    
    def __init__(self, idg_api_url: str, api_key: str, engine: JiminiPolicyEngine):
        super().__init__(SystemType.ENTRUST_IDG, idg_api_url, engine)
        self.api_key = api_key
    
    async def create_certificate(self, 
                               cert_request: Dict[str, Any],
                               tenant_id: str,
                               session_id: str) -> Dict[str, Any]:
        """Create certificate with policy enforcement"""
        
        # Intercept certificate request
        validated_request = await self.intercept_request(
            method="POST",
            endpoint="/certificates",
            data=cert_request,
            tenant_id=tenant_id,
            session_id=session_id
        )
        
        # Call Entrust IDG API (simulated)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Simulate certificate creation
        cert_response = {
            "certificate_id": "cert_abc123",
            "status": "issued",
            "subject": validated_request.get("subject", "CN=Unknown"),
            "valid_from": datetime.now().isoformat(),
            "valid_to": (datetime.now().replace(year=datetime.now().year + 1)).isoformat(),
            "serial_number": "1234567890ABCDEF"
        }
        
        return await self._filter_response(cert_response, tenant_id, session_id)

# 🎫 **UMS ADAPTER**

class UMSAdapter(PKISystemAdapter):
    """Adapter for User Management System"""
    
    def __init__(self, ums_api_url: str, engine: JiminiPolicyEngine):
        super().__init__(SystemType.UMS, ums_api_url, engine)
    
    async def get_user_profile(self, 
                              user_id: str,
                              tenant_id: str,
                              session_id: str) -> Dict[str, Any]:
        """Get user profile with PII protection"""
        
        request_data = {"user_id": user_id}
        
        # Intercept user lookup
        await self.intercept_request(
            method="GET",
            endpoint=f"/users/{user_id}",
            data=request_data,
            tenant_id=tenant_id,
            session_id=session_id
        )
        
        # Simulate user profile retrieval
        user_profile = {
            "user_id": user_id,
            "username": "jdoe",
            "full_name": "John Doe",
            "email": "john.doe@agency.gov",
            "phone": "555-123-4567",
            "ssn": "123-45-6789",
            "department": "IT Services",
            "clearance_level": "SECRET",
            "last_login": datetime.now().isoformat()
        }
        
        return await self._filter_response(user_profile, tenant_id, session_id)

# 🗄️ **DB2 ADAPTER**

class DB2Adapter(PKISystemAdapter):
    """Adapter for DB2 database operations"""
    
    def __init__(self, db_connection_string: str, engine: JiminiPolicyEngine):
        super().__init__(SystemType.DB2, db_connection_string, engine)
    
    async def execute_query(self, 
                           sql_query: str,
                           parameters: Dict[str, Any],
                           tenant_id: str,
                           session_id: str) -> Dict[str, Any]:
        """Execute database query with policy enforcement"""
        
        query_data = {
            "sql": sql_query,
            "parameters": parameters
        }
        
        # Intercept database query
        validated_data = await self.intercept_request(
            method="QUERY",
            endpoint="/db2/execute",
            data=query_data,
            tenant_id=tenant_id,
            session_id=session_id
        )
        
        # Simulate database query execution
        query_results = {
            "rows": [
                {
                    "employee_id": "E12345",
                    "name": "John Doe", 
                    "ssn": "123-45-6789",
                    "email": "john.doe@agency.gov",
                    "salary": 75000
                }
            ],
            "row_count": 1,
            "execution_time_ms": 45.2
        }
        
        return await self._filter_response(query_results, tenant_id, session_id)

# 🎟️ **SERVICENOW ADAPTER**

class ServiceNowAdapter(PKISystemAdapter):
    """Adapter for ServiceNow incident management"""
    
    def __init__(self, servicenow_instance: str, username: str, password: str, engine: JiminiPolicyEngine):
        super().__init__(SystemType.SERVICENOW, servicenow_instance, engine)
        self.auth = (username, password)
    
    async def create_incident(self, 
                            incident_data: Dict[str, Any],
                            tenant_id: str,
                            session_id: str) -> Dict[str, Any]:
        """Create ServiceNow incident with PII protection"""
        
        # Intercept incident creation
        validated_data = await self.intercept_request(
            method="POST",
            endpoint="/incidents",
            data=incident_data,
            tenant_id=tenant_id,
            session_id=session_id
        )
        
        # Simulate ServiceNow incident creation
        incident_response = {
            "sys_id": "inc_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
            "number": f"INC{datetime.now().strftime('%Y%m%d%H%M')}",
            "state": "New",
            "priority": validated_data.get("priority", "Medium"),
            "short_description": validated_data.get("short_description", ""),
            "description": validated_data.get("description", ""),
            "caller_id": validated_data.get("caller_id", ""),
            "created_on": datetime.now().isoformat()
        }
        
        return await self._filter_response(incident_response, tenant_id, session_id)
    
    async def search_incidents(self, 
                             search_criteria: Dict[str, Any],
                             tenant_id: str,
                             session_id: str) -> Dict[str, Any]:
        """Search ServiceNow incidents"""
        
        # Intercept search request
        await self.intercept_request(
            method="GET",
            endpoint="/incidents/search",
            data=search_criteria,
            tenant_id=tenant_id,
            session_id=session_id
        )
        
        # Simulate incident search
        search_results = {
            "incidents": [
                {
                    "sys_id": "inc_20241002_001",
                    "number": "INC202410020001",
                    "state": "In Progress",
                    "caller": {
                        "name": "John Doe",
                        "email": "john.doe@agency.gov",
                        "phone": "555-123-4567"
                    },
                    "description": "User unable to access system containing SSN: 123-45-6789"
                }
            ],
            "total_count": 1
        }
        
        return await self._filter_response(search_results, tenant_id, session_id)

# 🎯 **ADAPTER FACTORY**

class PKIAdapterFactory:
    """Factory for creating PKI system adapters"""
    
    def __init__(self, engine: JiminiPolicyEngine):
        self.engine = engine
        self.adapters: Dict[SystemType, PKISystemAdapter] = {}
    
    def create_ldap_adapter(self, server_url: str) -> LDAPAdapter:
        """Create LDAP adapter"""
        adapter = LDAPAdapter(server_url, self.engine)
        self.adapters[SystemType.LDAP] = adapter
        return adapter
    
    def create_entrust_adapter(self, api_url: str, api_key: str) -> EntrustIDGAdapter:
        """Create Entrust IDG adapter"""
        adapter = EntrustIDGAdapter(api_url, api_key, self.engine)
        self.adapters[SystemType.ENTRUST_IDG] = adapter
        return adapter
    
    def create_ums_adapter(self, api_url: str) -> UMSAdapter:
        """Create UMS adapter"""
        adapter = UMSAdapter(api_url, self.engine)
        self.adapters[SystemType.UMS] = adapter
        return adapter
    
    def create_db2_adapter(self, connection_string: str) -> DB2Adapter:
        """Create DB2 adapter"""
        adapter = DB2Adapter(connection_string, self.engine)
        self.adapters[SystemType.DB2] = adapter
        return adapter
    
    def create_servicenow_adapter(self, instance_url: str, username: str, password: str) -> ServiceNowAdapter:
        """Create ServiceNow adapter"""
        adapter = ServiceNowAdapter(instance_url, username, password, self.engine)
        self.adapters[SystemType.SERVICENOW] = adapter
        return adapter
    
    def get_adapter(self, system_type: SystemType) -> Optional[PKISystemAdapter]:
        """Get existing adapter by system type"""
        return self.adapters.get(system_type)

# 🌐 **HTTP REVERSE PROXY MIDDLEWARE**

class JiminiProxyMiddleware:
    """HTTP reverse proxy middleware for REST systems"""
    
    def __init__(self, engine: JiminiPolicyEngine, adapter_factory: PKIAdapterFactory):
        self.engine = engine
        self.adapter_factory = adapter_factory
        self.system_mappings = {
            "/servicenow/": SystemType.SERVICENOW,
            "/ums/": SystemType.UMS,
            "/entrust/": SystemType.ENTRUST_IDG,
            "/ldap/": SystemType.LDAP,
            "/db2/": SystemType.DB2
        }
    
    async def __call__(self, request, call_next):
        """Middleware to intercept HTTP requests"""
        
        # Determine target system from URL path
        target_system = None
        for path_prefix, system_type in self.system_mappings.items():
            if str(request.url.path).startswith(path_prefix):
                target_system = system_type
                break
        
        if target_system:
            # Extract tenant and session from headers
            tenant_id = request.headers.get("X-Tenant-Id", "default")
            session_id = request.headers.get("X-Session-Id", "session_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
            
            # Get request body
            body = await request.body()
            if body:
                try:
                    request_data = json.loads(body.decode())
                except json.JSONDecodeError:
                    request_data = {"raw_body": body.decode()}
            else:
                request_data = {}
            
            # Apply policy enforcement through appropriate adapter
            adapter = self.adapter_factory.get_adapter(target_system)
            if adapter:
                try:
                    # Intercept the request
                    await adapter.intercept_request(
                        method=request.method,
                        endpoint=str(request.url.path),
                        data=request_data,
                        tenant_id=tenant_id,
                        session_id=session_id
                    )
                except HTTPException:
                    # Request was blocked, re-raise the exception
                    raise
        
        # Continue with the request
        response = await call_next(request)
        return response

# Example usage and testing
if __name__ == "__main__":
    async def test_adapters():
        """Test PKI system adapters"""
        from jimini_gateway import JiminiPolicyEngine
        
        # Initialize engine and factory
        engine = JiminiPolicyEngine()
        factory = PKIAdapterFactory(engine)
        
        # Test LDAP adapter
        print("🗂️ Testing LDAP Adapter...")
        ldap_adapter = factory.create_ldap_adapter("ldap://ldap.agency.gov")
        
        async with ldap_adapter:
            result = await ldap_adapter.search(
                base_dn="ou=users,dc=agency,dc=gov",
                search_filter="(cn=john*)",
                attributes=["cn", "mail", "telephoneNumber"],
                tenant_id="gov-agency-a",
                session_id="test_session_001"
            )
            print(f"LDAP Result: {json.dumps(result, indent=2)}")
        
        # Test ServiceNow adapter
        print("\n🎟️ Testing ServiceNow Adapter...")
        snow_adapter = factory.create_servicenow_adapter(
            "https://agency.service-now.com",
            "admin",
            "password"
        )
        
        async with snow_adapter:
            incident = await snow_adapter.create_incident(
                {
                    "short_description": "System access issue",
                    "description": "User john.doe@agency.gov (SSN: 123-45-6789) cannot access system",
                    "priority": "High",
                    "caller_id": "john.doe"
                },
                tenant_id="gov-agency-a",
                session_id="test_session_002"
            )
            print(f"ServiceNow Result: {json.dumps(incident, indent=2)}")
    
    # Run tests
    asyncio.run(test_adapters())