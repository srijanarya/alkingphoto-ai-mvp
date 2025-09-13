# TalkingPhoto MVP - Stripe Payment Integration Guide

## Overview

This guide provides comprehensive instructions for implementing Stripe payment processing in your TalkingPhoto MVP. The integration includes subscription management, one-time payments, international support, and advanced security features.

## Prerequisites

- Stripe Account (Test and Live modes)
- Python 3.8+
- Streamlit
- Required Python packages (see requirements below)

## 1. Stripe Account Setup

### Create Stripe Products and Prices

```bash
# Install Stripe CLI
curl -s https://packages.stripe.com/api/security/keypair/stripe-cli-gpg/public | gpg --dearmor | sudo tee /usr/share/keyrings/stripe.gpg
echo "deb [signed-by=/usr/share/keyrings/stripe.gpg] https://packages.stripe.com/stripe-cli-debian-local stable main" | sudo tee -a /etc/apt/sources.list.d/stripe.list
sudo apt update
sudo apt install stripe

# Login to Stripe
stripe login

# Create products and prices
stripe products create --name="TalkingPhoto Starter" --description="30 video generations per month"
stripe prices create --product=prod_xxx --unit-amount=1999 --currency=usd --recurring=interval:month
stripe prices create --product=prod_xxx --unit-amount=19999 --currency=usd --recurring=interval:year

stripe products create --name="TalkingPhoto Pro" --description="100 video generations per month"
stripe prices create --product=prod_yyy --unit-amount=4999 --currency=usd --recurring=interval:month
stripe prices create --product=prod_yyy --unit-amount=49999 --currency=usd --recurring=interval:year
```

### Configure Webhooks

1. Go to Stripe Dashboard > Developers > Webhooks
2. Add endpoint: `https://your-domain.com/webhook/stripe`
3. Select events:
   - `checkout.session.completed`
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`

## 2. Environment Configuration

Create `.env` file:

```env
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Price IDs (replace with your actual IDs)
STRIPE_STARTER_MONTHLY_PRICE_ID=price_...
STRIPE_STARTER_YEARLY_PRICE_ID=price_...
STRIPE_PRO_MONTHLY_PRICE_ID=price_...
STRIPE_PRO_YEARLY_PRICE_ID=price_...
STRIPE_ENTERPRISE_MONTHLY_PRICE_ID=price_...
STRIPE_ENTERPRISE_YEARLY_PRICE_ID=price_...

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/talkingphoto_mvp

# Optional: External Services
REDIS_URL=redis://localhost:6379/0
```

## 3. Installation

```bash
# Install required packages
pip install -r requirements-payment.txt

# Create requirements-payment.txt
cat << EOF > requirements-payment.txt
streamlit>=1.28.0
stripe>=7.0.0
cryptography>=41.0.0
bcrypt>=4.0.1
PyJWT>=2.8.0
pandas>=2.1.1
plotly>=5.17.0
requests>=2.31.0
python-dotenv>=1.0.0
qrcode>=7.4.2
Pillow>=10.0.0
ipaddress>=1.0.23
EOF
```

## 4. Database Setup

```bash
# Initialize databases
python -c "
from services.payment_service import payment_service
from services.auth_service import auth_service  
from services.security_service import security_service
from services.retry_service import retry_service
from services.payment_analytics import analytics_service
from services.international_payments import international_payment_service

print('Initializing databases...')
# Databases are auto-initialized when services are imported
print('Database setup complete!')
"
```

## 5. Webhook Server Setup

### Option A: Standalone Webhook Server

```bash
# Run webhook server
python -m services.webhook_service
```

### Option B: Integrated with Streamlit (Development)

Add to your Streamlit app:

```python
import threading
from services.webhook_service import create_webhook_app

# Start webhook server in background thread (development only)
def start_webhook_server():
    app = create_webhook_app()
    app.run(host='0.0.0.0', port=5001, debug=False)

if __name__ == "__main__":
    # Start webhook server
    webhook_thread = threading.Thread(target=start_webhook_server, daemon=True)
    webhook_thread.start()
    
    # Run Streamlit app
    # streamlit run app_with_payments.py
```

### Option C: Production Deployment (Recommended)

Use a proper WSGI server like Gunicorn:

```bash
# Install Gunicorn
pip install gunicorn

# Create webhook app file
cat << EOF > webhook_app.py
from services.webhook_service import create_webhook_app
app = create_webhook_app()

if __name__ == "__main__":
    app.run()
EOF

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 webhook_app:app
```

## 6. Streamlit App Integration

Replace your main app file with the enhanced version:

```bash
# Backup original app
cp app.py app_original.py

# Use the new app with payments
cp app_with_payments.py app.py

# Run the app
streamlit run app.py
```

## 7. Testing

### Test Credit Card Numbers (Stripe Test Mode)

```python
# Successful payments
VISA_SUCCESS = "4242424242424242"
VISA_DEBIT = "4000056655665556"
MASTERCARD = "5555555555554444"

# Failed payments (for testing error handling)
CARD_DECLINED = "4000000000000002"
INSUFFICIENT_FUNDS = "4000000000009995"
EXPIRED_CARD = "4000000000000069"
INVALID_CVC = "4000000000000127"

# International cards
VISA_BR = "4000000760000002"  # Brazil
VISA_IN = "4000000356000002"  # India
VISA_DE = "4000000276000002"  # Germany
```

### Test Scenarios

```python
# Test basic payment flow
def test_payment_flow():
    # 1. Create customer
    # 2. Create subscription
    # 3. Verify webhook processing
    # 4. Check credit allocation
    pass

# Test failed payment handling
def test_failed_payments():
    # 1. Use declined card
    # 2. Verify retry logic
    # 3. Check dunning emails
    pass

# Test international payments
def test_international():
    # 1. Test different countries
    # 2. Verify tax calculations
    # 3. Check currency conversion
    pass
```

## 8. Security Checklist

### PCI DSS Compliance

- ✅ Never store card data
- ✅ Use Stripe.js for card collection
- ✅ Validate webhook signatures
- ✅ Encrypt sensitive data at rest
- ✅ Use HTTPS for all communications
- ✅ Implement proper access controls
- ✅ Log security events

### Implementation Verification

```python
# Check PCI compliance
from services.security_service import security_service

# Validate no card data storage
compliance_check = security_service.validate_pci_compliance(
    operation="payment_processing",
    data_fields=["amount", "currency", "customer_email"],
    user_id=1
)

print(f"PCI Compliant: {compliance_check['compliant']}")
```

## 9. Monitoring and Analytics

### Enable Analytics Tracking

```python
from services.payment_analytics import analytics_service

# Track payment events
analytics_service.track_payment_event("payment_success", {
    "amount": 49.99,
    "currency": "usd",
    "tier": "pro",
    "customer_email": "user@example.com"
})

# Generate reports
revenue_data = analytics_service.get_revenue_analytics(
    start_date=datetime.date(2025, 1, 1),
    end_date=datetime.date(2025, 1, 31)
)
```

### Dashboard Integration

```python
# Add to Streamlit app
import plotly.graph_objects as go
from services.payment_analytics import analytics_service

# Revenue chart
fig = analytics_service.generate_revenue_chart(
    start_date=datetime.date.today() - timedelta(days=30),
    end_date=datetime.date.today()
)
st.plotly_chart(fig)
```

## 10. Production Deployment

### Environment Variables (Production)

```env
# Production Stripe keys
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Production URLs
STRIPE_SUCCESS_URL=https://your-domain.com/success
STRIPE_CANCEL_URL=https://your-domain.com/cancel

# Security
SECRET_KEY=generate-strong-production-key
JWT_SECRET_KEY=generate-strong-jwt-key

# Database (Production)
DATABASE_URL=postgresql://user:password@production-db:5432/talkingphoto_prod
REDIS_URL=redis://production-redis:6379/0
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements-payment.txt .
RUN pip install -r requirements-payment.txt

COPY . .

# Expose ports
EXPOSE 8501 5001

# Start both Streamlit and webhook server
CMD ["sh", "-c", "gunicorn -w 4 -b 0.0.0.0:5001 webhook_app:app & streamlit run app.py --server.port=8501 --server.address=0.0.0.0"]
```

### Load Balancer Configuration

```nginx
# nginx.conf
upstream streamlit {
    server app1:8501;
    server app2:8501;
}

upstream webhooks {
    server app1:5001;
    server app2:5001;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    location / {
        proxy_pass http://streamlit;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /webhook/ {
        proxy_pass http://webhooks;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 11. Troubleshooting

### Common Issues

1. **Webhook not receiving events**
   - Check webhook URL is accessible
   - Verify endpoint signature validation
   - Check Stripe dashboard webhook logs

2. **Payment failures**
   - Review Stripe dashboard payment logs
   - Check error handling in retry service
   - Verify customer payment methods

3. **Tax calculation errors**
   - Validate customer address
   - Check regional tax configurations
   - Verify tax ID formats

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test webhook locally
stripe listen --forward-to localhost:5001/webhook/stripe
```

## 12. Support and Maintenance

### Regular Tasks

1. **Monthly**: Review failed payments and retry success rates
2. **Quarterly**: Audit PCI compliance and security logs
3. **Yearly**: Update tax rates and regional configurations

### Monitoring Alerts

Set up alerts for:
- High payment failure rates
- Webhook processing errors
- Security events
- Unusual payment patterns

### Backup Strategy

```bash
# Backup payment data (excluding sensitive information)
pg_dump -h localhost -U user -d talkingphoto_mvp \
  --exclude-table=payment_methods \
  --exclude-table=card_details \
  -f backup_$(date +%Y%m%d).sql
```

## Support

For additional support:
- Stripe Documentation: https://stripe.com/docs
- Stripe Support: https://support.stripe.com
- PCI DSS Guidelines: https://www.pcisecuritystandards.org

## License

This payment integration is part of the TalkingPhoto MVP project and follows the same licensing terms.