# CVS Data Collection Guide

Simple guide for collecting CVS order data using their retail API.

## 🚀 **Quick Start**

### **Step 1: Log into CVS**

1. Go to [cvs.com](https://cvs.com)
2. Sign in to your account
3. Navigate to **"Account" → "Order History"**

### **Step 2: Extract Tokens**

1. **Open Developer Tools** (F12)
2. **Go to Network tab**
3. **Look for OAuth2 token call** to `/oauth2/v1/token`
4. **Copy the ACCESS_TOKEN** from the response (e.g., `YOUR_ACCESS_TOKEN_HERE`)

### **Step 3: Extract API Call Data**

1. **Look for API calls** to `/api/retail/orders/v1/list`
2. **Copy the WHOLE COOKIE string** from the request headers
3. **Copy the ecCardNo and memberId** from the request payload

### **Step 4: Update Script**

Edit `cvs_scraper.py` and update these values:

```python
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN_HERE"  # From OAuth2 response
COOKIES = "YOUR_COOKIES_HERE"  # Full cookie string from API call
EC_CARD_NO = "539742276"  # From API payload
MEMBER_IDS = ["abc123...", "def456..."]  # From API payload
```

### **Step 5: Run the Scraper**

```bash
python cvs_scraper.py
```

## 📊 **Expected Output**

The scraper will create YAML files in `data/cvs/` with your order data:

```yaml
number: "7019-13-6385-20250629"
type: ["STORE"]
date: "2025-06-29T15:05:00Z"
totalCost: "68.79"
status: ["Purchased"]
items:
  rx: {}
  fs:
    total: 2
    name: "ALTDS SPEARMINT    1.76"
```

## ⚠️ **Notes**

- **Tokens expire** - Re-extract if you get 401 errors
- **OAuth2 token** from `/oauth2/v1/token` works best
- **Full cookie string** from API calls is required
