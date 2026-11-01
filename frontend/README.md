
## API Documentation

EconoCausal provides a REST API built using FastAPI.
The API exposes customer-level recommendations, causal
model evaluation metrics, and discount optimization results.

### Available Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Project information |
| GET | `/health` | API health status |
| GET | `/api/metrics` | Causal model evaluation metrics |
| GET | `/api/customers` | Customer recommendations |
| GET | `/api/discount-distribution` | Discount distribution |

### Running the Backend

Run the following command from the project root:

```bash
python -m uvicorn backend.api:app --reload
```

Open the interactive API documentation:

`http://127.0.0.1:8000/docs`

### Customer API Example

Request:

`GET /api/customers?limit=10&offset=0`

The endpoint supports pagination using the limit and offset
query parameters. It can also filter customers by their
recommended discount when supported by the API.

# EconoCausal Frontend

React-based analytics dashboard for EconoCausal.

## Technologies
- React
- Vite
- Recharts
- Lucide React

## Installation

```bash
npm install