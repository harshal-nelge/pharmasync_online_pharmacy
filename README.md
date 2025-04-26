# PharmaSync - Online Pharmacy Management System

## Overview
PharmaSync is a comprehensive online pharmacy platform built with Django that allows users to browse, purchase medications, and manage their prescriptions online. The system provides a secure and user-friendly interface for both customers and administrators.

![PharmaSync Screenshot]([https://i.postimg.cc/bYkr1n31/Screenshot-2025-04-26-at-1-48-51-PM.png])

## Live Demo
Access the live demo: [https://medical-pharmacy.onrender.com/](https://medical-pharmacy.onrender.com/)

## Features

### User Management
- User registration and authentication
- Personal profiles with order history
- Secure password management

### Product Catalog
- Browse medications by categories
- Detailed product information with images
- Prescription type indicators (OTC vs RX)
- Product search functionality

### Shopping Experience
- Intuitive cart management
- Real-time cart updates
- Quantity adjustment
- Stock availability checks

### Checkout System
- Multiple payment options:
  - PayPal integration
  - Razorpay integration
- Shipping information collection
- Order confirmation emails

### Discount Management
- Coupon code application
- Percentage-based discounts
- Time-limited promotional offers

### Admin Dashboard
- Comprehensive administration panel
- Product and inventory management
- Order processing workflow
- Customer management
- Sales analytics
- Discount code creation and management

## Technologies Used
- **Backend**: Django
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **Database**: SQLite (Development), PostgreSQL (Production)
- **Payment Processing**: PayPal API, Razorpay API
- **Image Handling**: Pillow
- **Form Management**: django-crispy-forms
- **Deployment**: Render with Whitenoise for static files

## Installation and Setup

### Prerequisites
- Python 3.8+
- pip

### Local Development Setup
1. Clone the repository:
```bash
git clone https://github.com/yourusername/pharmasync.git
cd pharmasync
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables for payment gateways:
   - Create a `.env` file and add your PayPal and Razorpay credentials
   - See `.env.example` for required variables

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Start the development server:
```bash
python manage.py runserver
```

8. Access the application at http://127.0.0.1:8000/

### Payment Gateway Setup
- PayPal: Set up a developer account at [developer.paypal.com](https://developer.paypal.com)
- Razorpay: Register at [razorpay.com](https://razorpay.com) for API credentials

## Usage Guide

### Customer Journey
1. Register or log in to your account
2. Browse medications by category or search for specific products
3. Add products to your cart
4. Apply discount codes if available
5. Proceed to checkout
6. Enter shipping information
7. Select payment method and complete payment
8. Receive order confirmation

### Admin Operations
1. Log in to the admin panel at `/admin`
2. Manage product inventory, categories, and images
3. Process and update order statuses
4. Create and manage discount promotions
5. View customer information and order history

