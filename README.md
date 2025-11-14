# ☁Cloud Storage - Full Stack Storage Solution


## Configuration


### Database Schema

**Tables:**
- `users` - User accounts and subscriptions
- `files` - File metadata
- `transactions` - Payment history
- `usage_history` - Daily storage tracking
- `pricing_plans` - Subscription tiers

## 🔐 API Endpoints

### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - User login

### Files
- `POST /api/upload` - Upload file
- `GET /api/files` - List user files
- `GET /api/download/<file_id>` - Download file
- `DELETE /api/delete/<file_id>` - Delete file

### User & Billing
- `GET /api/user/info` - Get user info
- `GET /api/pricing` - List pricing plans
- `POST /api/upgrade` - Upgrade subscription
- `GET /api/transactions` - Transaction history
- `GET /api/usage/history` - Usage analytics

### Admin
- `GET /api/admin/stats` - System statistics

