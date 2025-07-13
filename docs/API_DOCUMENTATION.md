# Grocery Genie API Documentation

## 🎯 **Overview**

The Grocery Genie API provides endpoints for receipt matching, health monitoring, and system status. The API is built with Flask and designed for both human and programmatic access.

**Base URL**: `https://api.grocery-genie.com`  
**Staging URL**: `https://staging.api.grocery-genie.com`

---

## 🔗 **API Endpoints**

### **Health Check**
```http
GET /health
```

**Description**: Check system health and availability

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-07-13T12:00:00Z",
  "database": "connected",
  "version": "1.0.0"
}
```

**Status Codes**:
- `200 OK` - System is healthy
- `503 Service Unavailable` - System is unhealthy

---

### **Receipt Matching**
```http
POST /match
```

**Description**: Trigger receipt matching and analysis

**Request Body**:
```json
{
  "receipt_data": "base64_encoded_receipt_image",
  "store": "costco|walmart|cvs|publix|other",
  "date": "2025-07-13",
  "amount": 123.45
}
```

**Response**:
```json
{
  "match_id": "uuid-string",
  "status": "processing|completed|failed",
  "confidence": 0.95,
  "matched_items": [
    {
      "item_name": "Organic Bananas",
      "quantity": 2,
      "price": 3.99,
      "category": "produce"
    }
  ],
  "total_amount": 123.45,
  "store_matched": "costco"
}
```

**Status Codes**:
- `200 OK` - Receipt processed successfully
- `400 Bad Request` - Invalid request data
- `422 Unprocessable Entity` - Receipt could not be processed

---

### **System Status**
```http
GET /status
```

**Description**: Get detailed system status and last run information

**Response**:
```json
{
  "last_run": {
    "timestamp": "2025-07-13T23:30:00Z",
    "status": "success",
    "records_processed": 156,
    "errors": 0
  },
  "data_loaders": {
    "cvs": "healthy",
    "costco": "healthy", 
    "walmart": "healthy",
    "publix": "healthy",
    "other": "healthy"
  },
  "database": {
    "status": "connected",
    "total_records": 8282,
    "last_update": "2025-07-13T23:50:00Z"
  }
}
```

---

## 🔧 **Authentication**

Currently, the API does not require authentication for basic endpoints. Future versions may implement API key authentication for production use.

---

## 📊 **Rate Limiting**

- **Health Check**: No rate limiting
- **Receipt Matching**: 10 requests per minute per IP
- **Status**: 60 requests per minute per IP

---

## 🐛 **Error Handling**

All API endpoints return consistent error responses:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request body is missing required fields",
    "details": {
      "missing_fields": ["receipt_data", "store"]
    }
  },
  "timestamp": "2025-07-13T12:00:00Z"
}
```

**Common Error Codes**:
- `INVALID_REQUEST` - Malformed request
- `PROCESSING_ERROR` - Internal processing failure
- `DATABASE_ERROR` - Database connectivity issues
- `RATE_LIMIT_EXCEEDED` - Too many requests

---

## 🧪 **Testing the API**

### **Using cURL**

```bash
# Health check
curl -X GET https://api.grocery-genie.com/health

# System status
curl -X GET https://api.grocery-genie.com/status

# Receipt matching (example)
curl -X POST https://api.grocery-genie.com/match \
  -H "Content-Type: application/json" \
  -d '{
    "receipt_data": "base64_encoded_data",
    "store": "costco",
    "date": "2025-07-13",
    "amount": 123.45
  }'
```

### **Using Python**

```python
import requests
import json

# Health check
response = requests.get('https://api.grocery-genie.com/health')
print(response.json())

# Receipt matching
receipt_data = {
    "receipt_data": "base64_encoded_data",
    "store": "costco", 
    "date": "2025-07-13",
    "amount": 123.45
}

response = requests.post(
    'https://api.grocery-genie.com/match',
    headers={'Content-Type': 'application/json'},
    data=json.dumps(receipt_data)
)
print(response.json())
```

---

## 🚀 **Local Development**

### **Starting the API Server**

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=grocery_genie
export DB_USER=your_username
export DB_PASSWORD=your_password

# Start the server
python src/api/receipt_matcher_api.py
```

The API will be available at `http://localhost:8080`

### **Docker Development**

```bash
# Build container
docker build -t grocery-genie-api .

# Run container
docker run -d \
  --name grocery-genie-api \
  -p 8080:8080 \
  -e DB_HOST=your_db_host \
  -e DB_USER=your_db_user \
  -e DB_PASSWORD=your_db_password \
  grocery-genie-api

# Test health endpoint
curl http://localhost:8080/health
```

---

## 📈 **Monitoring**

### **Health Monitoring**

The `/health` endpoint is designed for load balancer health checks and monitoring systems:

```bash
# Kubernetes health check
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10

# Docker health check  
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1
```

### **Metrics Collection**

Future versions will include metrics endpoints for Prometheus integration:

- `/metrics` - Prometheus metrics
- `/stats` - Detailed system statistics
- `/logs` - Recent log entries (admin only)

---

## 🔮 **Future Enhancements**

- **Authentication**: API key and OAuth2 support
- **Webhooks**: Real-time notifications for receipt processing
- **Batch Processing**: Multiple receipt upload endpoint
- **Analytics**: Spending analysis and reporting endpoints
- **Mobile SDK**: Native mobile app integration
- **GraphQL**: Alternative query interface

---

## 📞 **Support**

- **API Issues**: [GitHub Issues](https://github.com/tuolden/grocery-genie/issues)
- **Documentation**: [Project Overview](PROJECT_OVERVIEW.md)
- **Email**: tuolden@gmail.com

---

**The Grocery Genie API is designed to be simple, reliable, and easy to integrate with existing systems.**
