# 值班表邮箱提醒系统

基于 `FastAPI + SQLite + Vue3 + Element Plus` 的值班邮件提醒系统。

## 已实现功能

- Excel 导入值班表（列：日期、星期、值班人）
- 值班表管理（列表、编辑、删除）
- 人员邮箱维护（增删改查）
- 多提醒点规则（当天/前一天 + 时间，可“+”新增）
- 邮件模板管理（正常提醒模板、管理员兜底模板）
- 模板变量预览
- 系统设置（管理员邮箱、SMTP）
- 手动触发提醒执行
- 发送日志查看
- 实时提醒计算（方案B）+ 发送幂等防重复

## 项目结构

- `code/backend` 后端服务
- `code/frontend` 前端服务
- `plan.md` 开发计划

## 后端启动（开发模式）

1. 进入目录：`code/backend`
2. 安装依赖：
   - `pip install -r requirements.txt`
3. 复制环境变量文件：
   - `.env.example` -> `.env`
4. 启动：
   - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## 前端启动（开发模式）

1. 进入目录：`code/frontend`
2. 安装依赖：
   - `npm install`
3. 启动：
   - `npm run dev`

默认前端通过 Vite 代理把 `/api` 转发到 `http://127.0.0.1:8000`。

## 模板变量

- `{{duty_date}}`
- `{{weekday}}`
- `{{duty_person_name}}`
- `{{duty_person_email}}`
- `{{rule_day_label}}`
- `{{rule_time}}`
- `{{now}}`
- `{{admin_emails}}`
- `{{missing_reason}}`

## 说明

- 定时任务每分钟运行一次，按规则命中当前分钟发送提醒。
- 当值班人没有可用邮箱时，系统会给管理员发送兜底邮件，并记录日志。
- 同一业务日期+规则+目标邮箱的提醒通过 `dedupe_key` 唯一约束避免重复发送。