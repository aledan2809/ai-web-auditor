"""
API Tester - Tests REST/GraphQL API endpoints
"""

import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime
import json


@dataclass
class EndpointResult:
    method: str
    path: str
    status_code: int
    response_time_ms: float
    success: bool
    error: Optional[str]
    response_size: int
    headers: Dict[str, str]


@dataclass
class APITestResults:
    base_url: str
    total_tests: int
    passed: int
    failed: int
    avg_response_time: float
    endpoints: List[EndpointResult]


class APITester:
    """Tests API endpoints for functionality and performance"""

    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.default_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if auth_token:
            self.default_headers['Authorization'] = f'Bearer {auth_token}'

    async def test_endpoints(self, endpoints: List[Dict[str, Any]]) -> APITestResults:
        """Test multiple API endpoints"""
        results = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for endpoint in endpoints:
                result = await self._test_endpoint(client, endpoint)
                results.append(result)

        # Calculate statistics
        passed = sum(1 for r in results if r.success)
        failed = len(results) - passed
        avg_time = sum(r.response_time_ms for r in results) / len(results) if results else 0

        return APITestResults(
            base_url=self.base_url,
            total_tests=len(results),
            passed=passed,
            failed=failed,
            avg_response_time=avg_time,
            endpoints=results
        )

    async def _test_endpoint(
        self,
        client: httpx.AsyncClient,
        endpoint: Dict[str, Any]
    ) -> EndpointResult:
        """Test a single endpoint"""
        method = endpoint.get('method', 'GET').upper()
        path = endpoint.get('path', '/')
        headers = {**self.default_headers, **endpoint.get('headers', {})}
        body = endpoint.get('body')
        expected_status = endpoint.get('expected_status', [200, 201, 204])

        if isinstance(expected_status, int):
            expected_status = [expected_status]

        url = f"{self.base_url}{path}"

        try:
            start = datetime.now()

            if method == 'GET':
                response = await client.get(url, headers=headers)
            elif method == 'POST':
                response = await client.post(url, headers=headers, json=body)
            elif method == 'PUT':
                response = await client.put(url, headers=headers, json=body)
            elif method == 'PATCH':
                response = await client.patch(url, headers=headers, json=body)
            elif method == 'DELETE':
                response = await client.delete(url, headers=headers)
            else:
                return EndpointResult(
                    method=method,
                    path=path,
                    status_code=0,
                    response_time_ms=0,
                    success=False,
                    error=f"Unsupported method: {method}",
                    response_size=0,
                    headers={}
                )

            end = datetime.now()
            response_time = (end - start).total_seconds() * 1000

            success = response.status_code in expected_status
            error = None if success else f"Expected {expected_status}, got {response.status_code}"

            return EndpointResult(
                method=method,
                path=path,
                status_code=response.status_code,
                response_time_ms=response_time,
                success=success,
                error=error,
                response_size=len(response.content),
                headers=dict(response.headers)
            )

        except httpx.TimeoutException:
            return EndpointResult(
                method=method,
                path=path,
                status_code=0,
                response_time_ms=30000,
                success=False,
                error="Request timeout",
                response_size=0,
                headers={}
            )
        except Exception as e:
            return EndpointResult(
                method=method,
                path=path,
                status_code=0,
                response_time_ms=0,
                success=False,
                error=str(e),
                response_size=0,
                headers={}
            )

    async def discover_endpoints(self, common_paths: bool = True) -> List[Dict[str, Any]]:
        """Discover available API endpoints"""
        discovered = []

        if common_paths:
            # Test common API paths
            common = [
                '/api', '/api/v1', '/api/v2',
                '/health', '/status', '/ping',
                '/users', '/products', '/items',
                '/auth/login', '/auth/register',
                '/docs', '/openapi.json', '/swagger.json'
            ]

            async with httpx.AsyncClient(timeout=10.0) as client:
                for path in common:
                    try:
                        response = await client.get(
                            f"{self.base_url}{path}",
                            headers=self.default_headers
                        )
                        if response.status_code < 500:
                            discovered.append({
                                'method': 'GET',
                                'path': path,
                                'status': response.status_code
                            })
                    except Exception:
                        pass

        return discovered

    async def test_authentication(
        self,
        login_path: str = '/auth/login',
        credentials: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Test authentication endpoint"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}{login_path}",
                    headers=self.default_headers,
                    json=credentials or {}
                )

                return {
                    'success': response.status_code in [200, 201],
                    'status_code': response.status_code,
                    'has_token': 'token' in response.text.lower() or 'jwt' in response.text.lower()
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }

    async def test_rate_limiting(
        self,
        path: str = '/',
        requests_count: int = 50
    ) -> Dict[str, Any]:
        """Test API rate limiting"""
        results = []

        async with httpx.AsyncClient(timeout=10.0) as client:
            for _ in range(requests_count):
                try:
                    start = datetime.now()
                    response = await client.get(
                        f"{self.base_url}{path}",
                        headers=self.default_headers
                    )
                    end = datetime.now()

                    results.append({
                        'status': response.status_code,
                        'time': (end - start).total_seconds() * 1000,
                        'rate_limited': response.status_code == 429
                    })

                    if response.status_code == 429:
                        break
                except Exception:
                    break

        rate_limited = any(r['rate_limited'] for r in results)

        return {
            'total_requests': len(results),
            'rate_limited': rate_limited,
            'requests_until_limit': next(
                (i for i, r in enumerate(results) if r['rate_limited']),
                len(results)
            ),
            'avg_response_time': sum(r['time'] for r in results) / len(results) if results else 0
        }
