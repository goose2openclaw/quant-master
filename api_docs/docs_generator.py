"""
API文档生成器
"""
import json
from datetime import datetime

class APIEndpoint:
    def __init__(self, method, path, description, params=None, response=None):
        self.method = method
        self.path = path
        self.description = description
        self.params = params or []
        self.response = response or {}

class APIDocsGenerator:
    """
    API文档生成器
    支持: OpenAPI/Swagger, Postman, Markdown
    """
    def __init__(self, title='QuantMaster API'):
        self.title = title
        self.version = '1.0.0'
        self.endpoints = []
        self.base_url = 'http://localhost:8091'
    
    def add_endpoint(self, method, path, description, params=None, response=None):
        """添加端点"""
        self.endpoints.append(APIEndpoint(method, path, description, params, response))
    
    def generate_openapi(self):
        """生成OpenAPI 3.0规范"""
        paths = {}
        
        for ep in self.endpoints:
            if ep.path not in paths:
                paths[ep.path] = {}
            
            params = []
            for p in ep.params:
                params.append({
                    'name': p['name'],
                    'in': p.get('in', 'query'),
                    'required': p.get('required', False),
                    'schema': {'type': p.get('type', 'string')}
                })
            
            paths[ep.path][ep.method.lower()] = {
                'description': ep.description,
                'parameters': params,
                'responses': {
                    '200': {
                        'description': 'Success',
                        'content': {
                            'application/json': {
                                'schema': {'type': 'object'}
                            }
                        }
                    }
                }
            }
        
        return {
            'openapi': '3.0.0',
            'info': {
                'title': self.title,
                'version': self.version
            },
            'servers': [{'url': self.base_url}],
            'paths': paths
        }
    
    def generate_markdown(self):
        """生成Markdown文档"""
        md = f'''# {self.title}

**Version:** {self.version}  
**Base URL:** `{self.base_url}`

---

## Authentication

All API requests require authentication via `X-API-Key` header.

```
X-API-Key: your_api_key_here
```

---

## Endpoints

'''
        for ep in self.endpoints:
            md += f'''### {ep.method.upper()} {ep.path}

{ep.description}

**Parameters:**

| Name | Type | In | Required |
|------|------|-----|----------|
'''
            for p in ep.params:
                required = 'Yes' if p.get('required') else 'No'
                md += f"| {p['name']} | {p.get('type', 'string')} | {p.get('in', 'query')} | {required} |\n"
            
            md += '\n**Response:**\n```json\n' + json.dumps(ep.response, indent=2) + '\n```\n\n---\n'
        
        return md
    
    def generate_postman(self):
        """生成Postman Collection"""
        items = []
        
        for ep in self.endpoints:
            items.append({
                'name': ep.description,
                'request': {
                    'method': ep.method.upper(),
                    'url': {
                        'raw': f"{self.base_url}{ep.path}",
                        'path': ep.path.split('/')
                    },
                    'header': [
                        {'key': 'X-API-Key', 'value': '{{api_key}}'}
                    ]
                }
            })
        
        return {
            'info': {
                'name': self.title,
                'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'
            },
            'item': items
        }
    
    def save_openapi(self, filepath):
        """保存OpenAPI"""
        with open(filepath, 'w') as f:
            json.dump(self.generate_openapi(), f, indent=2)
    
    def save_markdown(self, filepath):
        """保存Markdown"""
        with open(filepath, 'w') as f:
            f.write(self.generate_markdown())
    
    def save_postman(self, filepath):
        """保存Postman"""
        with open(filepath, 'w') as f:
            json.dump(self.generate_postman(), f, indent=2)

# 注册默认端点
def get_default_docs():
    """获取默认API文档"""
    docs = APIDocsGenerator('QuantMaster API')
    
    docs.add_endpoint('GET', '/api/v1/status', '系统状态')
    docs.add_endpoint('GET', '/api/v1/positions', '获取持仓')
    docs.add_endpoint('POST', '/api/v1/orders', '下单', 
        params=[{'name': 'symbol', 'type': 'string', 'required': True},
                {'name': 'side', 'type': 'string', 'required': True},
                {'name': 'qty', 'type': 'number', 'required': True}])
    docs.add_endpoint('DELETE', '/api/v1/orders/{id}', '取消订单')
    docs.add_endpoint('POST', '/api/v1/backtest', '运行回测')
    docs.add_endpoint('GET', '/api/v1/performance', '绩效分析')
    docs.add_endpoint('GET', '/api/v1/risk/status', '风控状态')
    
    return docs
