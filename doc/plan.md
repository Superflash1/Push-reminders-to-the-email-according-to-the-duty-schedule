# 值班表邮件提醒系统开发计划（FastAPI + SQLite + Vue）

## 1. 目标与范围

### 1.1 项目目标
构建一个基于 Python 全栈的值班邮件提醒系统，支持：

- 从 Excel 导入值班表（核心列：日期、星期、值班人）
- 前端维护值班人员邮箱并保存到数据库
- 前端配置多个提醒时间点（支持“当天/前一天 + 具体时间”，可通过“+”新增多条）
- 到点自动发送提醒邮件
- 当值班人无可用邮箱时：记录日志并发送管理员兜底提醒
- 前端维护两套可编辑邮件模板（正常提醒模板 + 管理员兜底模板）

### 1.2 已确认规则

- 技术栈：`FastAPI + SQLite + Vue3`
- 每天仅 1 个值班人
- 提醒策略采用 **方案 B（实时计算）**
- 不做“提前 N 天”通用偏移，改为多条明确提醒点
- 每条提醒点：`当天/前一天` + `HH:mm`
- 无可用邮箱时：`记录日志 + 发管理员`

---

## 2. 总体架构

- 后端：`FastAPI`
  - REST API（值班表、人员邮箱、提醒规则、模板、日志）
  - 定时调度（每分钟轮询一次）
  - 模板渲染与邮件发送
- 数据库：`SQLite`
- 前端：`Vue3 + Element Plus`
  - 维护数据、配置规则、模板编辑、日志查看
- Excel 导入：`pandas + openpyxl`
- 调度：`APScheduler`

---

## 3. 数据库设计

### 3.1 duty_schedule（值班表）
- `id` INTEGER PK
- `duty_date` DATE UNIQUE NOT NULL
- `weekday_text` TEXT
- `duty_person_name` TEXT NOT NULL
- `source_sheet` TEXT
- `created_at` DATETIME
- `updated_at` DATETIME

### 3.2 person_contacts（人员通讯录）
- `id` INTEGER PK
- `person_name` TEXT UNIQUE NOT NULL
- `email` TEXT
- `enabled` BOOLEAN DEFAULT 1
- `remark` TEXT
- `created_at` DATETIME
- `updated_at` DATETIME

### 3.3 reminder_rules（提醒规则，多条）
- `id` INTEGER PK
- `offset_day` INTEGER NOT NULL  
  - `0=当天`
  - `-1=前一天`
- `trigger_time` TEXT NOT NULL  
  - 格式 `HH:mm`
- `enabled` BOOLEAN DEFAULT 1
- `sort_order` INTEGER DEFAULT 0
- `created_at` DATETIME
- `updated_at` DATETIME

### 3.4 mail_templates（邮件模板）
- `id` INTEGER PK
- `template_type` TEXT UNIQUE NOT NULL  
  - `DUTY_REMINDER`
  - `ADMIN_FALLBACK`
- `subject_template` TEXT NOT NULL
- `body_template` TEXT NOT NULL
- `enabled` BOOLEAN DEFAULT 1
- `updated_at` DATETIME

### 3.5 system_settings（系统配置）
- `id` INTEGER PK
- `admin_emails` TEXT NOT NULL（逗号分隔或 JSON）
- `timezone` TEXT DEFAULT 'Asia/Shanghai'
- `mail_host` TEXT
- `mail_port` INTEGER
- `mail_user` TEXT
- `mail_password` TEXT
- `mail_from` TEXT
- `updated_at` DATETIME

### 3.6 send_logs（发送日志）
- `id` INTEGER PK
- `biz_date` DATE NOT NULL
- `rule_id` INTEGER NOT NULL
- `target_type` TEXT NOT NULL  
  - `DUTY` / `ADMIN`
- `to_email` TEXT
- `subject` TEXT
- `rendered_body` TEXT
- `status` TEXT NOT NULL  
  - `SUCCESS` / `FAILED` / `SKIPPED`
- `error_message` TEXT
- `dedupe_key` TEXT UNIQUE NOT NULL
- `created_at` DATETIME

---

## 4. 模板变量规范

前端模板编辑器需展示可用变量说明，后端统一渲染：

- `{{duty_date}}` 值班日期（YYYY-MM-DD）
- `{{weekday}}` 星期（如 周四）
- `{{duty_person_name}}` 值班人姓名
- `{{duty_person_email}}` 值班人邮箱（可能为空）
- `{{rule_day_label}}` 当天/前一天
- `{{rule_time}}` 触发时间（HH:mm）
- `{{now}}` 当前发送时间
- `{{admin_emails}}` 管理员邮箱列表
- `{{missing_reason}}` 缺失原因（如“未配置邮箱”）

建议渲染引擎：`Jinja2`（受控变量上下文，不允许执行任意代码）。

---

## 5. 实时提醒计算逻辑（方案B）

调度任务每分钟执行一次：

1. 获取当前时间（按 `timezone`）
2. 读取启用的 `reminder_rules`
3. 对每条规则计算目标业务日期：
   - 规则为“当天 HH:mm”：当前日期即 `biz_date`
   - 规则为“前一天 HH:mm”：`biz_date = 当前日期 + 1 天`
4. 仅当当前分钟命中规则时间（`HH:mm`）时继续
5. 查询 `duty_schedule` 获取 `biz_date` 对应值班人
6. 查询 `person_contacts` 获取值班人邮箱且 `enabled=1`
7. 防重复：生成 `dedupe_key`（建议：`biz_date|rule_id|target_type|to_email`）
8. 分支处理：
   - 有值班人有效邮箱：
     - 渲染 `DUTY_REMINDER` 模板并发送
     - 记录 `send_logs`
   - 无有效邮箱：
     - 先记录值班邮件失败/跳过日志（可选记录为 `SKIPPED`）
     - 渲染 `ADMIN_FALLBACK` 模板发管理员
     - 记录管理员发送日志

> 注意：定时器可能重复触发，必须依赖 `dedupe_key` 唯一约束实现幂等。

---

## 6. 后端 API 设计（FastAPI）

### 6.1 值班表
- `POST /api/schedule/import`：上传 Excel 并导入
- `GET /api/schedule`：分页查询
- `PUT /api/schedule/{id}`：编辑单条
- `DELETE /api/schedule/{id}`：删除单条

### 6.2 人员邮箱
- `GET /api/contacts`
- `POST /api/contacts`
- `PUT /api/contacts/{id}`
- `DELETE /api/contacts/{id}`

### 6.3 提醒规则
- `GET /api/reminder-rules`
- `POST /api/reminder-rules`
- `PUT /api/reminder-rules/{id}`
- `DELETE /api/reminder-rules/{id}`

### 6.4 模板管理
- `GET /api/mail-templates`（返回两套模板）
- `PUT /api/mail-templates/{template_type}`
- `POST /api/mail-templates/preview`（传变量做预览）

### 6.5 系统设置
- `GET /api/settings`
- `PUT /api/settings`
- `POST /api/settings/test-mail`（测试 SMTP）

### 6.6 日志
- `GET /api/send-logs`

### 6.7 运维与调试
- `POST /api/reminders/run-once`（手动触发一次调度，便于联调）

---

## 7. 前端页面规划（Vue3 + Element Plus）

1. **值班表管理页**
   - Excel 上传导入
   - 列表查看/编辑

2. **人员邮箱页**
   - 姓名、邮箱、启用状态维护

3. **提醒规则页**
   - 多条规则列表
   - “+新增提醒”按钮
   - 每条规则配置：`当天/前一天` + `时间(HH:mm)` + 启用开关

4. **邮件模板页**
   - 两个 Tab：`正常提醒模板`、`管理员兜底模板`
   - 标题模板 + 正文模板编辑
   - 变量帮助面板（可点击插入变量）
   - 预览按钮

5. **系统设置页**
   - SMTP 参数
   - 管理员邮箱（多个）
   - 时区
   - 测试发送

6. **发送日志页**
   - 发送结果、时间、对象、错误信息筛选查询

---

## 8. 目录结构建议

```text
project/
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ core/
│  │  │  ├─ config.py
│  │  │  ├─ database.py
│  │  │  └─ scheduler.py
│  │  ├─ models/
│  │  ├─ schemas/
│  │  ├─ routers/
│  │  ├─ services/
│  │  │  ├─ excel_import_service.py
│  │  │  ├─ reminder_service.py
│  │  │  ├─ template_service.py
│  │  │  └─ mail_service.py
│  │  └─ utils/
│  ├─ requirements.txt
│  └─ .env.example
├─ frontend/
│  ├─ src/
│  │  ├─ api/
│  │  ├─ views/
│  │  ├─ components/
│  │  └─ router/
│  └─ package.json
└─ plan.md
```

---

## 9. 开发里程碑

### M1：后端基础（1天）
- FastAPI 项目初始化
- SQLite + ORM（SQLAlchemy）
- 数据表迁移（Alembic 可选）
- 基础配置加载（`.env`）

### M2：核心业务 API（1-2天）
- 值班表导入与 CRUD
- 人员邮箱 CRUD
- 提醒规则 CRUD
- 模板 CRUD 与预览
- 系统设置 CRUD

### M3：提醒引擎与发送日志（1天）
- APScheduler 每分钟任务
- 实时计算命中规则
- 邮件发送与异常处理
- 幂等防重复（`dedupe_key`）
- 日志查询

### M4：前端页面（2天）
- 6 个页面搭建
- 规则“+”交互
- 模板编辑器与变量插入
- 联调与错误提示

### M5：联调与验收（1天）
- 用真实 Excel 验证
- 无邮箱场景验证（管理员兜底）
- 重复触发幂等验证
- 打包与运行说明

---

## 10. 验收标准

1. 可导入 Excel（日期/星期/值班人）并落库
2. 前端可维护人员邮箱，值班姓名可匹配到邮箱
3. 可新增多条提醒规则（当天/前一天 + 时间）
4. 命中时间后系统自动发送邮件
5. 值班邮箱缺失时：日志可见 + 管理员收到兜底邮件
6. 两套模板可编辑且变量可渲染
7. 日志完整记录发送成功/失败/跳过信息
8. 同一提醒点不会重复发送（幂等有效）

---

## 11. 风险与处理

- **姓名匹配不一致（空格/别名）**  
  处理：导入时做 `trim`；后续可加“别名映射表”。

- **定时任务漂移或重启导致重复发送**  
  处理：以 `dedupe_key` + 唯一索引兜底。

- **SMTP 不稳定**  
  处理：失败日志保留，可提供“手动补发”接口（后续版本）。

---

## 12. 下一步（立即执行）

1. 初始化后端项目骨架与依赖
2. 建立数据库模型与建表
3. 实现 Excel 导入接口
4. 实现人员、规则、模板、设置 API
5. 实现调度与发送逻辑
6. 初始化 Vue 前端并完成管理页联调
