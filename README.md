# TaskGenie

TaskGenie 现已整理为单仓库（monorepo）结构，包含移动端前端和 FastAPI 后端。

## 目录结构

```text
TaskGenie/
├─ frontend/   # React Native 前端
└─ backend/    # FastAPI 后端
```

## 技术栈

- `frontend/`: React Native 0.79、React 19
- `backend/`: FastAPI、Uvicorn、SQLAlchemy、OpenAI SDK

## 本地启动

### 1. 启动后端

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

后端默认运行在 `http://localhost:8000`。

### 2. 启动前端

```bash
cd frontend
npm install
npm start
```

另开一个终端运行：

```bash
cd frontend
npm run android
```

或：

```bash
cd frontend
npm run ios
```

## 前后端联调

前端当前接口地址定义在 `frontend/src/context/TaskContext.js`：

- Android 模拟器：`http://10.0.2.2:8000`
- iOS 模拟器：`http://localhost:8000`

如果你之后部署到真机或服务器，需要把这里改成对应的 API 地址。

## 历史保留

这个单仓库保留了原前端仓库和原后端仓库的 Git 提交历史，适合作为后续统一维护的主仓库。
