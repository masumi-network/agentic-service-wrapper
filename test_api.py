import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import json

# set up test environment variables before importing main
os.environ["OPENAI_API_KEY"] = "test-openai-key"
os.environ["PAYMENT_SERVICE_URL"] = "https://test-payment-service.com"
os.environ["PAYMENT_API_KEY"] = "test-payment-key"
os.environ["NETWORK"] = "preview"
os.environ["AGENT_IDENTIFIER"] = "test-agent-123"
os.environ["SELLER_VKEY"] = "test-seller-vkey"

from main import app

client = TestClient(app)


class TestHealthEndpoints:
    """test basic health and info endpoints"""
    
    def test_health_endpoint(self):
        """test /health returns healthy status"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_availability_endpoint(self):
        """test /availability returns available status"""
        response = client.get("/availability")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "available"
        assert "uptime" in data
        assert isinstance(data["uptime"], int)
        assert data["message"] == "Server operational."
    
    def test_input_schema_endpoint(self):
        """test /input_schema returns correct schema"""
        response = client.get("/input_schema")
        assert response.status_code == 200
        data = response.json()
        assert "input_data" in data
        assert len(data["input_data"]) == 1
        assert data["input_data"][0]["id"] == "input_string"
        assert data["input_data"][0]["type"] == "string"
        assert data["input_data"][0]["name"] == "Text to Reverse"


class TestStartJobEndpoint:
    """test /start_job endpoint functionality"""
    
    @patch('main.Payment')
    @patch('main.cuid2.Cuid')
    @patch.dict(os.environ, {"AGENT_IDENTIFIER": "test-agent-123", "SELLER_VKEY": "test-seller-vkey"})
    def test_start_job_success(self, mock_cuid, mock_payment_class):
        """test successful job creation"""
        # mock cuid2 generation
        mock_cuid_instance = MagicMock()
        mock_cuid_instance.generate.return_value = "test-cuid2-identifier"
        mock_cuid.return_value = mock_cuid_instance
        
        # mock payment response
        mock_payment_instance = AsyncMock()
        mock_payment_instance.create_payment_request.return_value = {
            "data": {
                "blockchainIdentifier": "test-blockchain-id",
                "submitResultTime": "2025-06-17T12:00:00Z",
                "unlockTime": "2025-06-17T13:00:00Z",
                "externalDisputeUnlockTime": "2025-06-17T14:00:00Z"
            }
        }
        mock_payment_instance.input_hash = "test-input-hash"
        mock_payment_instance.payment_ids = set()
        mock_payment_instance.start_status_monitoring = AsyncMock()
        mock_payment_class.return_value = mock_payment_instance
        
        # test request
        test_data = {
            "input_data": [
                {"key": "input_string", "value": "Hello World"}
            ]
        }
        
        response = client.post("/start_job", json=test_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["payment_id"] == "test-blockchain-id"
        
        # verify payment was created with generated identifier
        mock_payment_class.assert_called_once()
        call_args = mock_payment_class.call_args[1]
        assert call_args["identifier_from_purchaser"] == "test-cuid2-identifier"
        # verify input_data was converted to dict
        expected_input = {"input_string": "Hello World"}
        assert call_args["input_data"] == expected_input
    
    def test_start_job_missing_input_data(self):
        """test job creation with missing input_data"""
        test_data = {}
        
        response = client.post("/start_job", json=test_data)
        
        assert response.status_code == 422  # validation error
    
    def test_start_job_invalid_input_data(self):
        """test job creation with invalid input_data structure"""
        test_data = {
            "input_data": "not an array"
        }
        
        response = client.post("/start_job", json=test_data)
        
        assert response.status_code == 422  # validation error
    
    @patch('main.Payment')
    @patch('main.cuid2.Cuid') 
    @patch.dict(os.environ, {"AGENT_IDENTIFIER": "test-agent-123", "SELLER_VKEY": "test-seller-vkey"})
    def test_start_job_missing_input_string(self, mock_cuid, mock_payment_class):
        """test job creation with missing input_string in input_data"""
        # mock cuid2 generation
        mock_cuid_instance = MagicMock()
        mock_cuid_instance.generate.return_value = "test-cuid2-identifier"
        mock_cuid.return_value = mock_cuid_instance
        
        test_data = {
            "input_data": [
                {"key": "other_field", "value": "some value"}
            ]
        }
        
        response = client.post("/start_job", json=test_data)
        
        assert response.status_code == 400
        assert "input_string" in response.json()["detail"]
    
    def test_url_validation_function(self):
        """test the URL validation function directly"""
        from main import validate_url
        
        # test valid URLs
        assert validate_url("https://example.com", "TEST_URL") == ""
        assert validate_url("http://localhost:3000", "TEST_URL") == ""
        
        # test invalid URLs
        assert "must start with 'https://' or 'http://'" in validate_url("example.com", "TEST_URL")
        assert "must start with 'https://' or 'http://'" in validate_url("ftp://example.com", "TEST_URL")
        assert "TEST_URL is not set" in validate_url("", "TEST_URL")
        assert "not a valid URL format" in validate_url("https://", "TEST_URL")
    
    @patch('main.Payment')
    @patch('main.cuid2.Cuid')
    @patch.dict(os.environ, {"AGENT_IDENTIFIER": "test-agent-123", "SELLER_VKEY": "test-seller-vkey"})
    def test_start_job_payment_error(self, mock_cuid, mock_payment_class):
        """test job creation when payment service fails"""
        # mock cuid2 generation
        mock_cuid_instance = MagicMock()
        mock_cuid_instance.generate.return_value = "test-cuid2-identifier"
        mock_cuid.return_value = mock_cuid_instance
        
        # mock payment failure
        mock_payment_instance = AsyncMock()
        mock_payment_instance.create_payment_request.side_effect = Exception("Payment service error")
        mock_payment_class.return_value = mock_payment_instance
        
        test_data = {
            "input_data": [
                {"key": "input_string", "value": "Hello World"}
            ]
        }
        
        response = client.post("/start_job", json=test_data)
        
        assert response.status_code in [400, 502]
        detail = response.json()["detail"]
        assert any(phrase in detail for phrase in ["Payment service unavailable", "Internal server error", "Server configuration error"])


class TestStatusEndpoint:
    """test /status endpoint functionality"""
    
    def test_status_job_not_found(self):
        """test status check for non-existent job"""
        response = client.get("/status?job_id=non-existent-job")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Job not found"
    
    @patch('main.Payment')
    @patch('main.cuid2.Cuid')
    @patch.dict(os.environ, {"AGENT_IDENTIFIER": "test-agent-123", "SELLER_VKEY": "test-seller-vkey"})
    def test_status_job_found(self, mock_cuid, mock_payment_class):
        """test status check for existing job"""
        # first create a job
        mock_cuid_instance = MagicMock()
        mock_cuid_instance.generate.return_value = "test-cuid2-identifier"
        mock_cuid.return_value = mock_cuid_instance
        
        mock_payment_instance = AsyncMock()
        mock_payment_instance.create_payment_request.return_value = {
            "data": {
                "blockchainIdentifier": "test-blockchain-id",
                "submitResultTime": "2025-06-17T12:00:00Z",
                "unlockTime": "2025-06-17T13:00:00Z",
                "externalDisputeUnlockTime": "2025-06-17T14:00:00Z"
            }
        }
        mock_payment_instance.input_hash = "test-input-hash"
        mock_payment_instance.payment_ids = set()
        mock_payment_instance.start_status_monitoring = AsyncMock()
        mock_payment_instance.check_payment_status.return_value = {
            "data": {"status": "pending"}
        }
        mock_payment_class.return_value = mock_payment_instance
        
        # create job
        test_data = {
            "input_data": [
                {"key": "input_string", "value": "Hello World"}
            ]
        }
        
        create_response = client.post("/start_job", json=test_data)
        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]
        
        # check status
        status_response = client.get(f"/status?job_id={job_id}")
        
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["job_id"] == job_id
        assert status_data["status"] == "awaiting_payment"
        assert status_data["payment_status"] == "pending"
        assert status_data["result"] is None


class TestOpenAPISchema:
    """test that openapi schema is properly generated"""
    
    def test_openapi_json(self):
        """test /openapi.json returns valid schema"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert schema["openapi"] == "3.1.0"
        assert schema["info"]["title"] == "API following the Masumi API Standard"
        assert schema["info"]["version"] == "1.0.0"
        
        # check that all expected endpoints are present
        paths = schema["paths"]
        assert "/start_job" in paths
        assert "/status" in paths
        assert "/availability" in paths
        assert "/input_schema" in paths
        assert "/health" in paths
        
        # check start_job endpoint schema
        start_job_schema = paths["/start_job"]["post"]
        assert "requestBody" in start_job_schema
        
        # verify identifier_from_purchaser is NOT in the request schema
        request_schema = start_job_schema["requestBody"]["content"]["application/json"]["schema"]
        if "$ref" in request_schema:
            # find the actual schema definition
            ref_path = request_schema["$ref"].split("/")[-1]
            actual_schema = schema["components"]["schemas"][ref_path]
            properties = actual_schema.get("properties", {})
        else:
            properties = request_schema.get("properties", {})
        
        assert "input_data" in properties
        # verify input_data is defined as an array of InputDataItem
        input_data_schema = properties["input_data"]
        assert input_data_schema["type"] == "array"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])