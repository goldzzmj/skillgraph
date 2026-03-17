# SkillGraph 第4阶段：部署自动化详细规划

**阶段：** Phase 4 - Deployment Automation
**时间：** 2026-03-16 11:00
**状态：** 待开始
**优先级：** 高（生产就绪）

---

## 📊 第4阶段总览

### 目标
构建企业级部署自动化系统，支持：
1. FastAPI RESTful服务
2. 认证和授权系统
3. 批量处理能力
4. 云平台部署
5. 监控和日志系统

### 预期时间线
- 第4.1周：FastAPI服务实现
- 第4.2-3周：认证和授权系统
- 第4.4周：批量处理系统
- 第4.5周：云平台部署
- 第4.6周：监控和日志系统
- 第4.7-8周：集成和测试

**总开发时间：** 6-8周

---

## 🎯 第4.1周：FastAPI服务实现

### 任务1.1：FastAPI基础架构

**功能需求：**
- ✅ FastAPI应用结构
- ✅ 异步支持
- ✅ 请求/响应模型
- ✅ 中间件配置
- ✅ 错误处理

**技术栈：**
```python
# core dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
```

**核心代码结构：**
```
src/skillgraph/api/
├── __init__.py
├── main.py                 # FastAPI应用入口
├── models.py               # Pydantic数据模型
├── schemas.py              # API Schema
├── dependencies.py          # 依赖注入
├── routes/                  # 路由定义
│   ├── __init__.py
│   ├── scan.py              # skill扫描端点
│   ├── predict.py           # 风险预测端点
│   ├── health.py            # 健康检查端点
│   └── analysis.py          # 分析端点
└── middleware/              # 中间件
    ├── __init__.py
    ├── auth.py               # 认证中间件
    ├── rate_limit.py         # 限流中间件
    └── logging.py            # 日志中间件
```

**关键实现：**
```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# FastAPI应用
app = FastAPI(
    title="SkillGraph API",
    description="AI Agent Skills Security Detection API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查端点
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "database": "connected",
            "redis": "connected",
            "models": "loaded"
        }
    }

# API信息端点
@app.get("/")
async def api_info():
    return {
        "name": "SkillGraph API",
        "version": "1.0.0",
        "endpoints": {
            "scan": "/api/v1/scan",
            "predict": "/api/v1/predict",
            "batch": "/api/v1/batch",
            "health": "/health"
        }
    }
```

### 任务1.2：Skill扫描端点

**API端点：** `POST /api/v1/scan`

**请求模型：**
```python
from pydantic import BaseModel, Field
from typing import Optional

class SkillScanRequest(BaseModel):
    """Skill扫描请求模型"""
    skill_content: str = Field(..., description="Skill内容（Markdown格式）")
    skill_type: Optional[str] = Field(None, description="Skill类型")
    scan_options: Optional[SkillScanOptions] = Field(None, description="扫描选项")

class SkillScanOptions(BaseModel):
    """扫描选项"""
    use_graphrag: bool = Field(True, description="是否使用GraphRAG")
    use_llm_extraction: bool = Field(True, description="是否使用LLM增强提取")
    use_gat_risk_model: bool = Field(True, description="是否使用GAT风险模型")
    include_community_detection: bool = Field(True, description="是否包含社区检测")
    include_embeddings: bool = Field(False, description="是否包含嵌入结果")
    output_format: str = Field("json", description="输出格式（json/html）")
```

**响应模型：**
```python
from pydantic import BaseModel
from typing import List, Dict, Any

class EntityResult(BaseModel):
    """实体结果"""
    entity_id: str
    entity_name: str
    entity_type: str
    risk_score: float
    confidence: float
    risk_level: str

class RiskFinding(BaseModel):
    """风险发现"""
    id: str
    type: str
    description: str
    severity: str
    confidence: float
    affected_entities: List[str]

class SkillScanResponse(BaseModel):
    """Skill扫描响应"""
    scan_id: str
    skill_name: Optional[str]
    scan_status: str  # pending, completed, failed
    processing_time: float
    risk_summary: Dict[str, Any]
    entities: List[EntityResult]
    relationships: List[Dict[str, Any]]
    communities: List[Dict[str, Any]]
    risk_findings: List[RiskFinding]
    recommendations: List[str]
```

**实现逻辑：**
```python
from fastapi import APIRouter, BackgroundTasks, Depends
from ..parser import SkillParser
from ..graphrag import EntityExtractor, CommunityDetector, GATRiskTrainer

router = APIRouter(prefix="/api/v1", tags=["scan"])

@router.post("/scan", response_model=SkillScanResponse)
async def scan_skill(
    request: SkillScanRequest,
    background_tasks: BackgroundTasks
    current_user = Depends(get_current_user)
):
    """
    扫描skill并返回风险分析结果
    """
    try:
        # 生成扫描ID
        scan_id = str(uuid.uuid4())

        # 解析skill
        parser = SkillParser()
        skill = parser.parse_content(request.skill_content)

        # 异步执行扫描
        if request.scan_options.use_graphrag:
            background_tasks.add_task(
                scan_with_graphrag,
                scan_id,
                skill,
                request.scan_options,
                current_user.user_id
            )

        # 返回扫描状态（立即返回）
        return SkillScanResponse(
            scan_id=scan_id,
            skill_name=skill.name,
            scan_status="pending",
            processing_time=0.0,
            risk_summary={},
            entities=[],
            relationships=[],
            communities=[],
            risk_findings=[],
            recommendations=[]
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scan failed: {str(e)}"
        )

@router.get("/scan/{scan_id}", response_model=SkillScanResponse)
async def get_scan_results(scan_id: str):
    """
    获取扫描结果
    """
    # 从Redis/数据库获取扫描结果
    scan_result = get_scan_result_from_storage(scan_id)

    return scan_result
```

### 任务1.3：风险预测端点

**API端点：** `POST /api/v1/predict`

**请求模型：**
```python
class RiskPredictionRequest(BaseModel):
    """风险预测请求模型"""
    entities: List[Dict[str, Any]] = Field(..., description="实体列表")
    relationships: List[Dict[str, Any]] = Field(..., description="关系列表")
    prediction_options: Optional[PredictionOptions] = Field(None, description="预测选项")

class PredictionOptions(BaseModel):
    """预测选项"""
    use_gat_model: bool = Field(True, description="是否使用GAT模型")
    use_ensemble: bool = Field(False, description="是否使用集成方法")
    return_attention_weights: bool = Field(True, description="是否返回注意力权重")
    confidence_threshold: float = Field(0.5, description="置信度阈值")
```

**响应模型：**
```python
class RiskPredictionResponse(BaseModel):
    """风险预测响应"""
    prediction_id: str
    status: str
    predictions: List[EntityResult]
    attention_weights: Optional[Dict[str, float]]
    confidence_metrics: Dict[str, float]
    processing_time: float
```

**实现逻辑：**
```python
from fastapi import APIRouter
from ..graphrag.gat_risk_model import GATRiskTrainer

router = APIRouter(prefix="/api/v1", tags=["predict"])

@router.post("/predict", response_model=RiskPredictionResponse)
async def predict_risk(
    request: RiskPredictionRequest,
    background_tasks: BackgroundTasks
):
    """
    使用GAT模型预测实体风险
    """
    try:
        # 生成预测ID
        prediction_id = str(uuid.uuid4())

        # 异步执行预测
        if request.prediction_options.use_gat_model:
            background_tasks.add_task(
                predict_with_gat_model,
                prediction_id,
                request.entities,
                request.relationships,
                request.prediction_options
            )

        return RiskPredictionResponse(
            prediction_id=prediction_id,
            status="pending",
            predictions=[],
            attention_weights={},
            confidence_metrics={},
            processing_time=0.0
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )
```

### 任务1.4：批量处理端点

**API端点：** `POST /api/v1/batch`

**请求模型：**
```python
class BatchScanRequest(BaseModel):
    """批量扫描请求"""
    skills: List[SkillScanRequest] = Field(..., description="Skill列表")
    batch_options: Optional[BatchOptions] = Field(None, description="批量处理选项")

class BatchOptions(BaseModel):
    """批量处理选项"""
    parallelism: int = Field(1, description="并行度")
    max_concurrent_scans: int = Field(5, description="最大并发扫描数")
    priority_order: str = Field("queue", description="优先级顺序（queue/priority）")
```

**响应模型：**
```python
class BatchScanResponse(BaseModel):
    """批量扫描响应"""
    batch_id: str
    status: str
    total_skills: int
    completed_skills: int
    failed_skills: int
    results: List[SkillScanResponse]
    summary: Dict[str, Any]
    errors: List[str]
```

---

## 🔒 第4.2-3周：认证和授权系统

### 任务2.1：JWT认证实现

**技术栈：**
```python
# dependencies
fastapi==0.104.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
redis==4.5.5
```

**JWT认证中间件：**
```python
from jose import JWTError, jwt
from fastapi import Security, HTTPException, status
from datetime import datetime, timedelta
from typing import Optional

# JWT配置
JWT_SECRET = "your-secret-key-here"
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7

class AuthHandler:
    """认证处理器"""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(self, data: dict) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> dict:
        """解码令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

# 认证依赖
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    """获取当前用户"""
    auth_handler = AuthHandler(JWT_SECRET)
    try:
        payload = auth_handler.decode_token(token)
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
```

**用户认证端点：**
```python
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext

class UserLogin(BaseModel):
    """用户登录请求"""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """用户响应"""
    user_id: str
    email: str
    access_token: str
    refresh_token: str
    token_type: str

@router.post("/auth/login", response_model=UserResponse)
async def login(user_credentials: UserLogin):
    """用户登录"""
    auth_handler = AuthHandler(JWT_SECRET)

    # 验证用户凭证
    user = authenticate_user(user_credentials.email, user_credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # 创建令牌
    access_token = auth_handler.create_access_token({
        "sub": user.user_id,
        "email": user.email,
        "role": user.role
    })

    refresh_token = auth_handler.create_refresh_token({
        "sub": user.user_id,
        "email": user.email
    })

    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer"
    )

@router.post("/auth/refresh", response_model=UserResponse)
async def refresh_token(refresh_token: str = Body(..., embed=True)):
    """刷新访问令牌"""
    auth_handler = AuthHandler(JWT_SECRET)

    try:
        payload = auth_handler.decode_token(refresh_token)
        user_id = payload.get("sub")

        # 获取用户信息
        user = get_user_by_id(user_id)

        # 创建新的访问令牌
        access_token = auth_handler.create_access_token({
            "sub": user.user_id,
            "email": user.email,
            "role": user.role
        })

        return UserResponse(
            user_id=user.user_id,
            email=user.email,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
```

### 任务2.2：API密钥认证

**实现：**
```python
from fastapi import Header, HTTPException, status

API_KEY_HEADER = "X-API-Key"

async def verify_api_key(api_key: str = Header(None, alias=API_KEY_HEADER)):
    """验证API密钥"""
    valid_api_keys = get_valid_api_keys_from_database()

    if api_key not in valid_api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return api_key

# 受保护的端点
@router.post("/api/v1/scan", dependencies=[Depends(verify_api_key)])
async def protected_scan(request: SkillScanRequest):
    """受保护的扫描端点"""
    # 只有拥有有效API密钥才能访问
    pass
```

### 任务2.3：权限控制和角色管理

**角色定义：**
```python
class UserRole(str, Enum):
    """用户角色"""
    ADMIN = "admin"
    USER = "user"
    ANALYST = "analyst"
    VIEWER = "viewer"

class Permission(str, Enum):
    """权限"""
    SCAN_SKILLS = "scan:skills"
    VIEW_RESULTS = "view:results"
    MANAGE_USERS = "manage:users"
    VIEW_ANALYTICS = "view:analytics"
    ADMIN_SETTINGS = "admin:settings"
```

**权限检查装饰器：**
```python
from functools import wraps
from fastapi import Depends, HTTPException, status

def check_permission(required_permission: Permission):
    """权限检查装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user=Depends(get_current_user), **kwargs):
            if user['role'] != UserRole.ADMIN:
                # 检查用户是否有所需权限
                user_permissions = get_user_permissions(user['user_id'])
                if required_permission.value not in user_permissions:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission {required_permission.value} required"
                    )
            return await func(*args, user=user, **kwargs)
        return wrapper
    return decorator

# 使用示例
@router.post("/admin/users", dependencies=[Depends(get_current_user)])
@check_permission(Permission.MANAGE_USERS)
async def manage_users(user_data: UserCreate):
    """管理用户 - 需要管理权限"""
    pass
```

---

## 🚀 第4.4周：批量处理系统

### 任务3.1：队列管理系统

**技术栈：**
```python
# dependencies
celery==5.3.4
redis==4.5.5
sqlalchemy==2.0.23
```

**队列配置：**
```python
# config/queue.py
from celery import Celery
from config.settings import REDIS_URL

# Celery应用
celery_app = Celery(
    'skillgraph',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['skillgraph.tasks']
)

# 任务队列配置
celery_app.conf.task_routes = {
    'skillgraph.tasks.scan_skill': {
        'queue': 'scan',
        'routing_key': 'scan',
    },
    'skillgraph.tasks.predict_risk': {
        'queue': 'predict',
        'routing_key': 'predict',
    },
    'skillgraph.tasks.batch_process': {
        'queue': 'batch',
        'routing_key': 'batch',
    }
}

# 任务优先级
celery_app.conf.task_queues = {
    'high': {
        'exchange': 'skillgraph',
        'routing_key': 'high',
        'queue_arguments': {'x-max-priority': 10},
    },
    'default': {
        'exchange': 'skillgraph',
        'routing_key': 'default',
        'queue_arguments': {'x-max-priority': 5},
    },
    'low': {
        'exchange': 'skillgraph',
        'routing_key': 'low',
        'queue_arguments': {'x-max-priority': 1},
    },
}
```

**异步任务定义：**
```python
# tasks/scan_tasks.py
from celery import Task

@celery_app.task(bind=True, name='skillgraph.tasks.scan_skill')
def scan_skill_task(self, scan_id: str, skill_content: str, options: dict):
    """异步扫描skill"""
    try:
        # 解析skill
        parser = SkillParser()
        skill = parser.parse_content(skill_content)

        # 执行扫描
        result = perform_scan(skill, options)

        # 保存结果
        save_scan_result(scan_id, result)

        # 更新任务状态
        self.update_state(
            state='PROCESSED',
            meta={'scan_id': scan_id, 'result': result}
        )

        return {'status': 'completed', 'scan_id': scan_id}

    except Exception as e:
        self.update_state(
            state='FAILED',
            meta={'scan_id': scan_id, 'error': str(e)}
        )

        return {'status': 'failed', 'scan_id': scan_id, 'error': str(e)}

@celery_app.task(bind=True, name='skillgraph.tasks.batch_process')
def batch_process_task(self, batch_id: str, skills: list):
    """批量处理skills"""
    try:
        total = len(skills)
        completed = 0
        failed = 0

        for i, skill in enumerate(skills):
            try:
                # 处理单个skill
                result = process_single_skill(skill)

                # 更新进度
                completed += 1
                progress = (completed / total) * 100

                self.update_state(
                    state='PROCESSED',
                    meta={'batch_id': batch_id, 'progress': progress}
                )

            except Exception as e:
                failed += 1
                continue

        # 保存批量结果
        save_batch_result(batch_id, total, completed, failed)

        return {
            'status': 'completed',
            'batch_id': batch_id,
            'total': total,
            'completed': completed,
            'failed': failed
        }

    except Exception as e:
        self.update_state(
            state='FAILED',
            meta={'batch_id': batch_id, 'error': str(e)}
        )

        return {
            'status': 'failed',
            'batch_id': batch_id,
            'error': str(e)
        }
```

### 任务3.2：任务状态管理

**实现：**
```python
# api/routes/task_status.py
from fastapi import APIRouter
from sqlalchemy.orm import Session
from ..models.database import Task, get_db

router = APIRouter(prefix="/api/v1", tags=["tasks"])

@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """获取任务状态"""
    # 从数据库获取任务
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return {
        "task_id": task.id,
        "status": task.status,
        "progress": task.progress,
        "result": task.result,
        "error": task.error,
        "created_at": task.created_at,
        "updated_at": task.updated_at
    }

@router.get("/tasks/batch/{batch_id}/progress")
async def get_batch_progress(batch_id: str, db: Session = Depends(get_db)):
    """获取批量任务进度"""
    # 获取批量任务的所有子任务
    tasks = db.query(Task).filter(Task.batch_id == batch_id).all()

    total = len(tasks)
    completed = len([t for t in tasks if t.status == 'COMPLETED'])
    failed = len([t for t in tasks if t.status == 'FAILED'])
    in_progress = total - completed - failed

    return {
        "batch_id": batch_id,
        "total": total,
        "completed": completed,
        "failed": failed,
        "in_progress": in_progress,
        "progress_percentage": (completed / total * 100) if total > 0 else 0
    }
```

---

## ☁️ 第4.5周：云平台部署

### 任务4.1：Docker容器化

**Dockerfile:**
```dockerfile
FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src
COPY config/ ./config
COPY models/ ./models

# 设置环境变量
ENV PYTHONPATH=/app/src
ENV SKILLGRAPH_ENV=production

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "skillgraph.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  api:
    build: .
    container_name: skillgraph-api
    ports:
      - "8000:8000"
    environment:
      - SKILLGRAPH_ENV=production
      - DATABASE_URL=postgresql://user:password@postgres:5432/skillgraph
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=${JWT_SECRET}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    container_name: skillgraph-postgres
    environment:
      - POSTGRES_DB=skillgraph
      - POSTGRES_USER=skillgraph
      - POSTGRES_PASSWORD=skillgraph_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./config/init.sql:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    container_name: skillgraph-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  celery_worker:
    build: .
    container_name: skillgraph-celery-worker
    environment:
      - SKILLGRAPH_ENV=production
      - DATABASE_URL=postgresql://user:password@postgres:5432/skillgraph
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
    command: celery -A skillgraph.tasks worker --loglevel=info

  celery_beat:
    build: .
    container_name: skillgraph-celery-beat
    environment:
      - SKILLGRAPH_ENV=production
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./logs:/app/logs
    depends_on:
      - redis
    command: celery -A skillgraph beat --loglevel=info

  prometheus:
    image: prom/prometheus
    container_name: skillgraph-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/
    depends_on:
      - api

  grafana:
    image: grafana/grafana
    container_name: skillgraph-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - ./config/grafana:/etc/grafana/provisioning
    depends_on:
      - prometheus

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
```

### 任务4.2：Kubernetes部署配置

**k8s-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: skillgraph-api
  labels:
    app: skillgraph
spec:
  replicas: 3
  selector:
    matchLabels:
      app: skillgraph
  template:
    metadata:
      labels:
        app: skillgraph
    spec:
      containers:
      - name: skillgraph-api
        image: skillgraph:latest
        ports:
        - containerPort: 8000
        env:
        - name: SKILLGRAPH_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: skillgraph-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: skillgraph-secrets
              key: redis-url
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: skillgraph-secrets
              key: jwt-secret
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: skillgraph-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: skillgraph-api-service
spec:
  selector:
    app: skillgraph
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
  selector:
    app: skillgraph
```

**k8s-horizontal-pod-autoscaler.yaml:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: skillgraph-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: skillgraph-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
    resource:
      name: cpu
    target:
        type: Utilization
        averageUtilization: 0.7
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: 1000
```

### 任务4.3：CI/CD流程

**GitHub Actions配置：**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Kubernetes

on:
  push:
    branches: [main]

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Log in to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: skillgraph:latest, skillgraph:${{ github.sha }}

  deploy-to-k8s:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Kubernetes
        uses: azure/k8s-deploy@v4
        with:
          manifests: |
            k8s/deployment.yaml
            k8s/service.yaml
          kubeconfig: ${{ secrets.KUBE_CONFIG }}
          images: |
            skillgraph:latest
```

---

## 📊 第4.6周：监控和日志系统

### 任务5.1：Prometheus监控

**prometheus.yml配置：**
```yaml
# config/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'skillgraph-api'
    scrape_interval: 5s
    static_configs:
      - targets: ['api:8000']
    metrics_path: /metrics
    relabel_configs:
      - source_labels: ['job']
      - target_label: '__address__'
      - regex: 'api:(.*)'
      - replacement: 'api-${1}'
```

**监控指标：**
```python
# api/routes/metrics.py
from prometheus_client import Counter, Histogram, Gauge
from fastapi import APIRouter

# Prometheus指标
router = APIRouter(prefix="/metrics", tags=["monitoring"])

# 计数器
scan_requests_total = Counter('skillgraph_scan_requests_total', 'Skill scan requests')
scan_requests_completed = Counter('skillgraph_scan_requests_completed', 'Skill scan completed')
scan_requests_failed = Counter('skillgraph_scan_requests_failed', 'Skill scan failed')

# 直方图
scan_duration_seconds = Histogram('skillgraph_scan_duration_seconds', 'Skill scan duration', buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0])
prediction_confidence = Histogram('skillgraph_prediction_confidence', 'Prediction confidence', buckets=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0])

# 仪表板
active_scans = Gauge('skillgraph_active_scans', 'Active skill scans')
failed_scans_last_hour = Gauge('skillgraph_failed_scans_last_hour', 'Failed scans last hour')

@router.get("/metrics")
async def get_metrics():
    """Prometheus指标端点"""
    return {
        "scan_requests_total": scan_requests_total._value.get(),
        "scan_requests_completed": scan_requests_completed._value.get(),
        "scan_requests_failed": scan_requests_failed._value.get(),
        "active_scans": active_scans._value.get(),
        "failed_scans_last_hour": failed_scans_last_hour._value.get()
    }
```

### 任务5.2：错误追踪

**Sentry集成：**
```python
# config/monitoring.py
import sentry_sdk
from fastapi import FastAPI

# Sentry初始化
sentry_sdk.init(
    dsn="${SENTRY_DSN}",
    traces_sample_rate=1.0,
    environment="production"
    integrations=[
        fastapi.FastApiIntegration(),
    celery.CeleryIntegration(),
    redis.RedisIntegration()
    ],
    release="skillgraph@1.0.0"
)

# FastAPI应用
app = FastAPI(
    title="SkillGraph API",
    version="1.0.0",
)

# Sentry集成
sentry_sdk.init_app(
    app,
    traces_sample_rate=1.0,
)
```

**错误处理：**
```python
# api/middleware/error_handler.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
import sentry_sdk
import logging

logger = logging.getLogger(__name__)

async def log_error_to_sentry(request: Request, exc: Exception):
    """记录错误到Sentry"""
    # 发送错误到Sentry
    sentry_sdk.capture_exception(exc)

# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # 记录错误
    logger.error(f"Unhandled exception: {exc}")

    # 发送到Sentry
    await log_error_to_sentry(request, exc)

    # 返回用户友好的错误响应
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "request_id": str(uuid.uuid4()),
            "message": "An unexpected error occurred"
        }
    )
```

### 任务5.3：日志聚合

**日志配置：**
```python
# config/logging_config.py
import structlog

# Structlog配置
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_thread_id,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

# 使用日志
logger.info("API started", environment="production")
logger.error("Scan failed", scan_id="12345", error="Database timeout")
```

**日志发送器：**
```python
# api/middleware/logging.py
import logging
import structlog
from fastapi import Request
from prometheus_client import Counter

# 日志计数器
log_counter = Counter('skillgraph_log_events_total', 'Log events')

async def log_request(request: Request, event: str, extra_data: dict = None):
    """记录请求日志"""
    logger.info(
        event=event,
        request_id=request.state.request_id,
        user_id=request.state.user_id,
        extra_data=extra_data or {}
    )

    # 更新计数器
    log_counter.labels(event=event).inc()
```

---

## 🎯 最终集成和测试

### 集成测试计划

**第4.7周：集成和测试**
1. FastAPI服务测试
2. 认证系统测试
3. 批量处理测试
4. 部署到测试环境
5. 端到端测试
6. 性能测试
7. 安全测试
8. 文档完善

### 性能基准

**目标性能指标：**
- API响应时间：<100ms（P95）
- 并发请求处理：100+ QPS
- 批量处理：100+ skills/分钟
- 内存使用：<2GB（100请求）
- 错误率：<0.1%

### 安全测试

**安全检查清单：**
1. ✅ SQL注入防护
2. ✅ XSS防护
3. ✅ CSRF防护
4. ✅ 认证安全
5. ✅ 授权验证
6. ✅ 速率限制
7. ✅ 输入验证
8. ✅ 错误信息不泄露

---

## 📦 文件结构

### 最终文件列表

**核心文件：**
- `src/skillgraph/api/` - FastAPI服务
- `src/skillgraph/tasks/` - 异步任务
- `src/skillgraph/middleware/` - 中间件
- `config/` - 配置文件
- `tests/` - 测试文件

**部署文件：**
- `Dockerfile` - Docker配置
- `docker-compose.yml` - Docker Compose配置
- `k8s/` - Kubernetes配置
- `.github/workflows/` - CI/CD配置

**监控文件：**
- `config/prometheus.yml` - Prometheus配置
- `config/grafana/` - Grafana配置
- `config/monitoring.py` - 监控配置

---

## 📊 预期效果

### 部署后性能

| 指标 | 预期值 |
|------|--------|
| API响应时间 | <100ms |
| 并发处理 | 100+ QPS |
| 批量处理 | 100+ skills/分钟 |
| 内存使用 | <2GB (100并发) |
| 错误率 | <0.1% |
| 可用性 | 99.9% |

### 企业级特性

1. ✅ 完整的RESTful API
2. ✅ JWT认证和授权
3. ✅ 异步批量处理
4. ✅ Docker和K8s部署
5. ✅ Prometheus监控
6. ✅ Sentry错误追踪
7. ✅ 结构化日志
8. ✅ 99.9%可用性
9. ✅ 安全防护
10. ✅ 横向扩展

---

**Phase 4版本：** v1.0.0  
**发布时间：** 预计2026-05-01  
**总开发时间：** 6-8周

---

**下一步：** 联网搜索相关技术最佳实践
