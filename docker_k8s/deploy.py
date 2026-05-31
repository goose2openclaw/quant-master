"""
Docker/K8s Deploy - 容器化部署
"""
import os, json

class DockerGenerator:
    """Docker文件生成"""
    def __init__(self, project_name='quantmaster'):
        self.project_name = project_name
    
    def generate_dockerfile(self, base_image='python:3.11-slim', port=8091):
        """生成Dockerfile"""
        return f'''
FROM {base_image}

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE {port}

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV PORT={port}

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{port}/health || exit 1

# 启动命令
CMD ["python", "-m", "quant_master"]
'''
    
    def generate_docker_compose(self, services=None):
        """生成docker-compose.yml"""
        if services is None:
            services = {
                'app': {'ports': ['8091:8091'], 'depends_on': ['redis', 'postgres']},
                'redis': {'image': 'redis:7-alpine', 'ports': ['6379:6379']},
                'postgres': {'image': 'postgres:15', 'ports': ['5432:5432'], 'environment': ['POSTGRES_PASSWORD=secret']}
            }
        
        compose = {
            'version': '3.8',
            'services': services
        }
        
        return json.dumps(compose, indent=2)
    
    def generate_requirements(self):
        """生成requirements.txt"""
        return '''
flask>=2.3.0
flask-socketio>=5.3.0
requests>=2.31.0
numpy>=1.24.0
pandas>=2.0.0
scipy>=1.10.0
sqlalchemy>=2.0.0
redis>=4.5.0
python-socketio>=5.9.0
gevent>=23.0.0
websocket-client>=1.6.0
python-dotenv>=1.0.0
APScheduler>=3.10.0
'''

class KubernetesGenerator:
    """K8s配置生成"""
    def __init__(self, project_name='quantmaster'):
        self.project_name = project_name
    
    def generate_deployment(self, replicas=2, port=8091):
        """生成Deployment"""
        return {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': self.project_name,
                'labels': {'app': self.project_name}
            },
            'spec': {
                'replicas': replicas,
                'selector': {'matchLabels': {'app': self.project_name}},
                'template': {
                    'metadata': {'labels': {'app': self.project_name}},
                    'spec': {
                        'containers': [{
                            'name': self.project_name,
                            'image': f'{self.project_name}:latest',
                            'ports': [{'containerPort': port}],
                            'resources': {
                                'requests': {'memory': '256Mi', 'cpu': '100m'},
                                'limits': {'memory': '2Gi', 'cpu': '1000m'}
                            },
                            'livenessProbe': {
                                'httpGet': {'path': '/health', 'port': port},
                                'initialDelaySeconds': 10,
                                'periodSeconds': 30
                            },
                            'readinessProbe': {
                                'httpGet': {'path': '/ready', 'port': port},
                                'initialDelaySeconds': 5
                            }
                        }]
                    }
                }
            }
        }
    
    def generate_service(self, port=8091):
        """生成Service"""
        return {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {'name': self.project_name},
            'spec': {
                'type': 'LoadBalancer',
                'selector': {'app': self.project_name},
                'ports': [{'port': port, 'targetPort': port}]
            }
        }
    
    def generate_hpa(self, min_replicas=1, max_replicas=5):
        """生成HPA"""
        return {
            'apiVersion': 'autoscaling/v2',
            'kind': 'HorizontalPodAutoscaler',
            'metadata': {'name': self.project_name},
            'spec': {
                'scaleTargetRef': {'apiVersion': 'apps/v1', 'kind': 'Deployment', 'name': self.project_name},
                'minReplicas': min_replicas,
                'maxReplicas': max_replicas,
                'metrics': [
                    {'type': 'Resource', 'resource': {'name': 'cpu', 'target': {'type': 'Utilization', 'averageUtilization': 70}}}
                ]
            }
        }
    
    def generate_configmap(self, config):
        """生成ConfigMap"""
        return {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {'name': f'{self.project_name}-config'},
            'data': config
        }
    
    def generate_ingress(self, host='quantmaster.local'):
        """生成Ingress"""
        return {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'Ingress',
            'metadata': {'name': f'{self.project_name}-ingress'},
            'spec': {
                'rules': [{
                    'host': host,
                    'http': {
                        'paths': [{
                            'path': '/',
                            'pathType': 'Prefix',
                            'backend': {'service': {'name': self.project_name, 'port': {'number': 8091}}}
                        }]
                    }
                }]
            }
        }
    
    def save_yaml_files(self, output_dir='/tmp/k8s'):
        """保存所有K8s配置"""
        os.makedirs(output_dir, exist_ok=True)
        
        files = {
            'deployment.yaml': self.generate_deployment(),
            'service.yaml': self.generate_service(),
            'hpa.yaml': self.generate_hpa(),
            'ingress.yaml': self.generate_ingress()
        }
        
        for filename, content in files.items():
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w') as f:
                json.dump(content, f, indent=2)
        
        return list(files.keys())
