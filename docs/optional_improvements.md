# Optional Improvements

Implemented option groups for stronger scoring:

1. Group A:
   - Automatic transaction categorization by keyword rules
   - Expense forecasting from historical monthly expenses
   - Saving-rate recommendation in report forecast
   - Investment risk analysis with volatility and stock concentration

2. Group B:
   - Statement import endpoint with `xlsx` and `ofx` format validation
   - Broker account connect endpoint for portfolio sync simulation

3. Group C:
   - Report result caching
   - Async FX rates refresh task through Celery

Not implemented in this baseline:

- Real bank Open API integration credentials
- OCR receipt scanner
- Voice input and AR widgets
