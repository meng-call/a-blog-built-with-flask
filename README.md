# Flasky - Flask 博客应用

一个基于 Flask 的全功能博客应用，支持用户认证、文章发布、评论系统、关注功能等。

## 功能特性

- ✅ 用户注册、登录、登出
- ✅ 邮箱确认机制
- ✅ 文章 CRUD 操作（创建、读取、更新、删除）
- ✅ Markdown 支持（使用 Flask-PageDown）
- ✅ 评论系统（支持审核）
- ✅ 用户关注/取消关注
- ✅ 粉丝/关注列表
- ✅ 个人资料编辑
- ✅ 管理员后台
- ✅ RESTful API（带 Token 认证）
- ✅ 头像支持（Cravatar/Gravatar）
- ✅ 分页支持

## 技术栈

### 后端
- **Flask 3.1.2** - Web 框架
- **Flask-SQLAlchemy** - ORM
- **Flask-Login** - 用户会话管理
- **Flask-WTF** - 表单处理
- **Flask-Migrate** - 数据库迁移
- **Flask-Mail** - 邮件发送
- **Flask-HTTPAuth** - API 认证
- **Flask-PageDown** - Markdown 支持
- **Flask-Moment** - 时间格式化

### 前端
- **Bootstrap 3.3.7** - UI 框架
- **jQuery 1.12.4** - JavaScript 库
- **Moment.js** - 时间处理

### 其他
- **SQLite** - 数据库（开发环境）
- **Faker** - 测试数据生成
- **Blinker** - 信号支持

## 安装与运行

### 1. 克隆项目

