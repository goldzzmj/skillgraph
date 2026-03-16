# 🚀 生产环境部署指南

## 📋 部署概述

本文档提供SkillGraph v1.0.0的详细部署指南，包括Docker、Docker Compose和Kubernetes部署方案。

**部署选项：**
1. Docker容器化部署（单机）
2. Docker Compose部署（单机多服务）
3. Kubernetes部署（生产级集群）

**推荐部署：** Kubernetes（生产环境）

---

## 🔧 前置条件

### 系统要求

**操作系统：**
- Linux（推荐Ubuntu 20.04+）
- macOS 10.15+
- Windows 10+（支持Docker）

**硬件要求：**
- CPU：4核+
- 内存：8GB+
- 磁盘：100GB+（SSD推荐）

**软件要求：**
- Docker 24.0+
- Docker Compose 2.0+
- Kubernetes 1.27+（集群部署）
- kubectl 1.27+（集群管理）
- Python 3.9+（开发环境）

---

## 🐳 Docker部署

### 1. 拉取Docker镜像

```bash
# 拉取最新版本
docker pull skillgraph-api:latest

# 拉取v1.0.0版本
docker pull skillgraph-api:v1.0.0
```

### 2. 配置环境变量

```bash
# 创建环境变量文件
cat > .env <<EOF
SKILLGRAPH_ENV=production
DATABASE_URL=postgresql://user:password@host:5432/skillgraph
REDIS_URL=redis://host:6379
JWT_SECRET=your-secret-key-change-in-production
OPENAI_API_KEY=sk-...
CORS_ALLOW_ORIGINS=*
EOF
```

### 3. 运行Docker容器

```bash
# 运行容器（前台）
docker run --env-file .env -p 8000:8000 skillgraph-api:v1.0.0

# 运行容器（后台）
docker run -d --name skillgraph-api --env-file .env -p 8000:8000 skillgraph-api:v1.0.0

# 查看日志
docker logs -f skillgraph-api

# 停止容器
docker stop skillgraph-api

# 删除容器
docker rm skillgraph-api
```

### 4. 访问API

```
http://localhost:8000/docs
http://localhost:8000/health
```

---

## 🐳 Docker Compose部署

### 1. 克隆仓库

```bash
git clone https://github.com/goldzzmj/skillgraph.git
cd skillgraph
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vi .env
```

**.env文件内容：**
```bash
# 应用配置
SKILLGRAPH_ENV=production
PORT=8000

# 数据库配置
POSTGRES_USER=skillgraph
POSTGRES_PASSWORD=skillgraph_password
POSTGRES_DB=skillgraph
POSTGRES_PORT=5432

# Redis配置
REDIS_PASSWORD=skillgraph_redis_password
REDIS_PORT=6379

# JWT配置
JWT_SECRET=your-secret-key-change-in-production

# OpenAI配置
OPENAI_API_KEY=sk-...

# CORS配置
CORS_ALLOW_ORIGINS=*

# 日志配置
LOG_LEVEL=info
```

### 3. 启动服务

```bash
# 启动所有服务（后台）
docker-compose up -d

# 启动所有服务（前台，查看日志）
docker-compose up
```

**启动的服务：**
1. api - FastAPI应用（端口：8000）
2. postgres - PostgreSQL数据库（端口：5432）
3. redis - Redis缓存（端口：6379）
4. celery_worker - Celery Worker（后台任务）
5. celery_beat - Celery Beat（定时调度）
6. prometheus - Prometheus监控（端口：9090）
7. grafana - Grafana可视化（端口：3000）

### 4. 查看日志

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs -f api

# 查看最后100行日志
docker-compose logs --tail=100 api
```

### 5. 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止所有服务并删除卷
docker-compose down -v
```

### 6. 扩展服务

```bash
# 扩展API服务到3个实例
docker-compose up -d --scale api=3

# 扩展Celery Worker到2个实例
docker-compose up -d --scale celery_worker=2
```

### 7. 访问服务

```
API: http://localhost:8000/docs
Prometheus: http://localhost:9090
Grafana: http://localhost:3000
```

---

## ☸️ Kubernetes部署

### 1. 克隆仓库

```bash
git clone https://github.com/goldzzmj/skillgraph.git
cd skillgraph
```

### 2. 配置kubectl

```bash
# 下载kubectl
curl -LO "https://dl.k8s.io/release/v1.27.0/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# 验证kubectl
kubectl version --client
```

### 3. 配置kubeconfig

```bash
# 创建kubeconfig目录
mkdir -p ~/.kube

# 复制kubeconfig文件
cp /path/to/kubeconfig ~/.kube/config

# 验证连接
kubectl cluster-info
kubectl get nodes
```

### 4. 创建Secrets

```bash
# 创建数据库连接Secret
kubectl create secret generic skillgraph-secrets \
  --from-literal=database-url="postgresql://user:password@postgres:5432/skillgraph" \
  --from-literal=redis-url="redis://redis:6379" \
  --from-literal=jwt-secret="your-secret-key-change-in-production" \
  --from-literal=openai-api-key="sk-..."
```

### 5. 应用Kubernetes清单

```bash
# 应用所有清单
kubectl apply -f k8s/

# 应用特定清单
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/celery-deployment.yaml
kubectl apply -f k8s/prometheus-deployment.yaml
kubectl apply -f k8s/grafana-deployment.yaml
```

### 6. 检查部署

```bash
# 查看所有Pods
kubectl get pods -l app=skillgraph

# 查看所有Services
kubectl get svc -l app=skillgraph

# 查看Deployment状态
kubectl get deployment skillgraph-api

# 查看HorizontalPodAutoscaler
kubectl get hpa skillgraph-api-hpa
```

### 7. 扩展部署

```bash
# 扩展到5个副本
kubectl scale deployment skillgraph-api --replicas=5

# 查看扩容状态
kubectl get pods -l app=skillgraph
kubectl rollout status deployment/skillgraph-api
```

### 8. 查看日志

```bash
# 查看Pod日志
kubectl logs -l app=skillgraph -f

# 查看特定Pod日志
kubectl logs <pod-name>

# 查看容器日志
kubectl logs <pod-name> -c skillgraph-api

# 查看最近的日志
kubectl logs <pod-name> --tail=100
```

### 9. 端口转发

```bash
# 端口转发到本地
kubectl port-forward svc/skillgraph-api-service 8000:8000

# 后台运行
kubectl port-forward svc/skillgraph-api-service 8000:8000 &
```

### 10. 访问服务

```
本地访问：http://localhost:8000/docs
集群访问：http://<service-ip>:8000/docs
```

---

## 📊 监控和日志

### Prometheus配置

**访问Prometheus：**
```
http://localhost:9090
```

**Prometheus配置文件：** `config/prometheus.yml`

**关键指标：**
- `skillgraph_api_requests_total` - 总请求数
- `skillgraph_api_request_duration_seconds` - 请求延迟
- `skillgraph_api_errors_total` - 错误数
- `skillgraph_api_active_connections` - 活跃连接数

### Grafana配置

**访问Grafana：**
```
http://localhost:3000
```

**默认登录：**
- 用户名：admin
- 密码：admin

**配置数据源：**
1. 登录Grafana
2. Configuration → Data Sources
3. Add data source → Prometheus
4. URL: `http://prometheus:9090`

**导入仪表板：**
1. Dashboard → Import
2. 上传配置文件

---

## 🔒 安全配置

### 1. Secrets管理

**Docker Secrets：**
```bash
# 创建Docker Secret
docker secret create skillgraph-secrets \
  jwt-secret \
  openai-api-key
```

**Kubernetes Secrets：**
```bash
# 创建Kubernetes Secret
kubectl create secret generic skillgraph-secrets \
  --from-literal=jwt-secret="your-secret-key" \
  --from-literal=openai-api-key="sk-..."
```

### 2. RBAC配置

**Kubernetes RBAC：**
```yaml
# 创建ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: skillgraph-api
```

### 3. 网络策略

**Kubernetes NetworkPolicy：**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: skillgraph-network-policy
spec:
  podSelector:
    matchLabels:
      app: skillgraph
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: skillgraph
```

---

## 🚀 生产环境优化

### 1. 资源限制

**Deployment资源限制：**
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### 2. 水平扩展

**HPA配置：**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: skillgraph-api-hpa
spec:
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 0.7
```

### 3. Pod中断预算

**PDB配置：**
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: skillgraph-api-pdb
spec:
  minAvailable: 2
  maxUnavailable: 1
```

---

## 📚 故障排查

### 1. Docker问题

**容器无法启动：**
```bash
# 查看容器日志
docker logs <container-id>

# 检查容器状态
docker inspect <container-id>

# 重新启动容器
docker restart <container-id>
```

**网络问题：**
```bash
# 检查网络连接
docker network ls
docker network inspect bridge
```

### 2. Docker Compose问题

**服务启动失败：**
```bash
# 查看服务日志
docker-compose logs <service>

# 检查服务状态
docker-compose ps

# 重启服务
docker-compose restart <service>
```

**端口冲突：**
```bash
# 修改端口映射
vi docker-compose.yml

# 重新启动服务
docker-compose up -d
```

### 3. Kubernetes问题

**Pod无法启动：**
```bash
# 查看Pod日志
kubectl logs <pod-name>

# 查看Pod事件
kubectl describe pod <pod-name>

# 查看Pod状态
kubectl get pods <pod-name> -o yaml
```

**服务无法访问：**
```bash
# 查看Service状态
kubectl get svc skillgraph-api-service -o yaml

# 端口转发
kubectl port-forward svc/skillgraph-api-service 8000:8000
```

**扩展失败：**
```bash
# 查看HPA事件
kubectl describe hpa skillgraph-api-hpa

# 手动扩展
kubectl scale deployment skillgraph-api --replicas=5
```

---

## 📊 性能调优

### 1. 数据库优化

**连接池配置：**
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

**查询优化：**
```sql
-- 添加索引
CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_entities_risk_score ON entities(risk_score DESC);
```

### 2. 缓存优化

**Redis缓存配置：**
```python
redis_client = await redis.from_url(
    REDIS_URL,
    encoding="utf-8",
    max_connections=50
)
```

**缓存策略：**
```python
# 使用缓存
@lru_cache(maxsize=1024)
async def get_entity(entity_id: str):
    # 从缓存获取
    pass
```

### 3. API优化

**异步处理：**
```python
@app.post("/api/v1/scan")
async def scan_skill(request: Request):
    # 异步处理
    result = await scan_skill_async(request)
    return result
```

---

## 🎯 部署检查清单

### Docker部署检查

- [ ] Docker镜像已拉取
- [ ] 环境变量已配置
- [ ] 容器已启动
- [ ] 健康检查通过
- [ ] API可访问

### Docker Compose部署检查

- [ ] 所有服务已启动
- [ ] 数据库已连接
- [ ] Redis已连接
- [ ] API可访问
- [ ] Prometheus可访问
- [ ] Grafana可访问

### Kubernetes部署检查

- [ ] kubectl已配置
- [ ] Secrets已创建
- [ ] Deployment已应用
- [ ] Service已暴露
- [ ] HPA已配置
- [ ] Pods正在运行
- [ ] 健康检查通过

---

## 📞 支持和帮助

### 获取帮助

- **GitHub Issues:** https://github.com/goldzzmj/skillgraph/issues
- **GitHub Discussions:** https://github.com/goldzzmj/skillgraph/discussions

### 文档

- [README](README.md) - 项目说明
- [API文档](http://localhost:8000/docs) - API文档
- [部署指南](#) - 本文档

---

## 🎉 总结

**生产环境部署选项：**
1. **Docker**：单机部署，快速开始
2. **Docker Compose**：单机多服务，适合开发/测试
3. **Kubernetes**：生产级集群，高可用性

**推荐部署：** Kubernetes（生产环境）

**预期性能：**
- API响应时间：<100ms
- 并发请求：100+ QPS
- 可用性：99.9%
- 自动扩展：3-10个副本

---

**开始部署SkillGraph v1.0.0！**
