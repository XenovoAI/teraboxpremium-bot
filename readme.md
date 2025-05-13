# Terabox Premium Bot

A Telegram bot system that provides premium Terabox download services with subscription plans.

## Features

- Extract and process Terabox download links
- Free tier with limited daily usage
- Premium subscription plans (monthly, quarterly, yearly)
- Secure payment processing with RazorPay
- Firebase integration for user management and data storage

## Project Structure
├── .env                    # Environment variables
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── README.md              # Project documentation
├── firebase/              # Firebase integration
│   ├── config.py          # Firebase configuration
│   ├── user.py            # User data operations
│   └── functions/         # Cloud Functions
│       └── reset.py       # Daily usage reset function
├── main_bot/              # Main Telegram bot
│   ├── bot.py             # Main bot implementation
│   ├── download.py        # Terabox download handling
│   ├── premium.py         # Premium features management
│   └── url_detector.py    # Terabox URL detection
├── payment_bot/           # Payment Telegram bot
│   ├── bot.py             # Payment bot implementation
│   ├── plans.py           # Premium plan definitions
│   └── razorpay_handlers.py # RazorPay integration
└── utils/                 # Utility modules
├── constants.py       # Application constants
└── security.py        # Security utilities
