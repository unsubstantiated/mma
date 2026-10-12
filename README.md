# MMA - MONEY MANAGER APP

used for organising expenses, fees or anything that is money-related;
helps the distribution of money among friends after holidays;
nice and sexy diagrams



## Running with Docker

```sh
cp .env.example .env   # set JWT_SECRET (DATABASE_URL is derived by compose)
docker compose up --build
```

- Frontend: http://localhost:5173
- API: http://localhost:8000
- Postgres data persists in the `pgdata` volume (`docker compose down -v` wipes it)
