# 🏋️ Bodybuilding Website API 📦

Welcome to the **Bodybuilding Website API** — a full-stack Django REST API for managing users, posts, comments, articles, workout programs, and more. This project is built with **Django 5**, **Django Rest Framework (DRF)**, **Djoser + SimpleJWT** for authentication, and **Swagger (drf-yasg)** for live API documentation.

## 🚀 Features

* 🔐 **core**: User Authentication & Management (sign up, login, profiles, roles)
* 💪 **workouts**: Workout Plans & Exercises (predefined plans, custom logs)
* 🥗 **nutrition**: Meal Plans & Recipes (calorie & macro tracking)
* 📈 **progress**: Progress Tracking & Analytics (body measurements, weight logs, milestones)
* 💬 **community**: Forum & Social Features (posts, comments, likes, challenges)
* 📚 **content**: Educational Resources & Blog (articles, videos, calculators)
* 🛒 **store**: E-commerce (products, carts, orders, payments)
* 📝 **API Documentation**: Swagger UI & ReDoc (drf-yasg)
* 🛡️ **Secure & Scalable**: `.env` configuration, HTTPS, JWT rotation, role-based permissions
* ✅ **Unit & Integration Tests**: Django’s built-in test framework

## 📌 Technologies Used

* **Backend**: Django 5, Django REST Framework (DRF)
* **Authentication**: Djoser + SimpleJWT (JWT-based), extendable for social logins
* **API Documentation**: Swagger & ReDoc (drf-yasg)
* **Database**: MySQL (via mysqlclient), switchable to PostgreSQL or SQLite
* **Security**: python-decouple for env management, HTTPS settings, secure cookies
* **Testing**: Django test framework, extensible with pytest

## 🏗️ Apps Overview

1. **core** (Authentication & User Management)

   * **Purpose:** Handles user signup, login, profiles, roles.
   * **Models:** `CustomUser`, `UserProfile`.
   * **Endpoints:**

     ```
     POST   /auth/users/            — register
     POST   /auth/jwt/create/       — login (JWT tokens)
     POST   /auth/jwt/refresh/      — refresh token
     GET    /auth/users/me/         — get profile
     PATCH  /auth/users/me/         — update profile
     ```

2. **workouts** (Workout Plans & Exercises)

   * **Purpose:** Manage workout plans, exercises, and logs.
   * **Models:** `WorkoutPlan`, `Exercise`, `WorkoutLog`.
   * **Endpoints:**

     ```
     GET    /workouts/plans/        — list plans
     POST   /workouts/plans/        — create plan (admin)
     GET    /workouts/plans/{id}/   — plan detail
     GET    /workouts/exercises/    — list exercises
     POST   /workouts/logs/         — log a workout
     GET    /workouts/logs/?user=me — view logs
     ```

3. **nutrition** (Nutrition & Meal Plans)

   * **Purpose:** Meal plans, recipes, calorie & macro tracking.
   * **Models:** `MealPlan`, `Recipe`, `NutritionLog`.
   * **Endpoints:**

     ```
     GET    /nutrition/mealplans/   — list plans
     POST   /nutrition/mealplans/   — create plan (admin)
     GET    /nutrition/recipes/     — list recipes
     POST   /nutrition/logs/        — log meals
     GET    /nutrition/logs/?date=  — fetch logs by date
     ```

4. **progress** (Progress Tracking & Analytics)

   * **Purpose:** Body measurements, weight logs, milestones.
   * **Models:** `BodyMeasurement`, `WeightLog`, `Milestone`, `ProgressLog`.
   * **Endpoints:**

     ```
     GET    /progress/measurements/   — list measurements
     POST   /progress/measurements/   — add measurement
     GET    /progress/weightlogs/      — list weight entries
     POST   /progress/weightlogs/      — add weight log
     GET    /progress/milestones/      — list goals
     POST   /progress/milestones/      — create milestone
     ```

5. **community** (Forum & Social Features)

   * **Purpose:** Posts, comments, likes, follows, challenges.
   * **Models:** `ForumPost`, `Comment`, `Like`, `Follow`, `Challenge`, `Leaderboard`.
   * **Endpoints:**

     ```
     GET    /community/posts/               — list posts
     POST   /community/posts/               — create post
     GET    /community/posts/{id}/          — post detail
     PUT    /community/posts/{id}/          — update post
     DELETE /community/posts/{id}/          — delete post
     POST   /community/posts/{id}/like/     — like/unlike
     GET    /community/comments/?post={id}  — comments for post
     POST   /community/comments/            — add comment
     POST   /community/follows/             — follow user
     GET    /community/challenges/          — list challenges
     POST   /community/challenges/          — create challenge
     GET    /community/leaderboards/        — leaderboard data
     ```

6. **content** (Educational Resources & Blog)

   * **Purpose:** Articles, videos, guides, calculators.
   * **Models:** `Article`, `Video`, `ExerciseGuide`, `Calculator`.
   * **Endpoints:**

     ```
     GET    /content/articles/              — list articles
     GET    /content/articles/{slug}/       — article detail
     GET    /content/videos/                — list videos
     GET    /content/calculators/bmi/       — BMI calculator
     ```

7. **store** (E-commerce)

   * **Purpose:** Manage products, customers, carts, orders, payments, and product comments.
   * **Models:** `Category`, `Discount`, `Product`, `Customer`, `Order`, `OrderItem`, `Address`, `Comment`, `Cart`, `CartItem`.
   * **Endpoints:**

     ```
     GET    /store/categories/                  — list categories
     POST   /store/categories/                  — create category (admin)
     GET    /store/categories/{id}/             — category detail
     GET    /store/discounts/                   — list discounts
     POST   /store/discounts/                   — create discount (admin)
     GET    /store/products/                    — list products
     POST   /store/products/                    — create product (admin)
     GET    /store/products/{id}/               — product detail
     GET    /store/products/{id}/comments/      — list comments for product
     POST   /store/products/{id}/comments/      — add comment (customer)
     GET    /store/customers/me/                — get customer profile (authenticated)
     POST   /store/customers/                   — create customer profile
     GET    /store/orders/                      — list orders (admin or customer)
     POST   /store/orders/                      — place a new order (customer)
     GET    /store/orders/{id}/                 — order detail
     PATCH  /store/orders/{id}/                 — update order status (admin)
     DELETE /store/orders/{id}/                 — cancel order (customer)
     GET    /store/carts/{cart_id}/items/       — list cart items
     POST   /store/carts/{cart_id}/items/       — add item to cart
     PATCH  /store/carts/{cart_id}/items/{id}/  — update cart item quantity
     DELETE /store/carts/{cart_id}/items/{id}/  — remove item from cart
     GET    /store/customers/{customer_id}/address/ — get shipping address
     PUT    /store/customers/{customer_id}/address/ — set/update address
     ```

## 🛠 Installation & Setup & Setup

1. **Clone & Enter**

   ```sh
   git clone https://github.com/hatef97/bodybuilding-website.git
   cd bodybuilding-website
   ```
2. **VirtualEnv**

   ```sh
   python -m venv venv
   source venv/bin/activate
   ```
3. **Deps**

   ```sh
   pip install -r requirements.txt
   ```
4. **Env**

   ```sh
   cp .env.example .env
   # configure SECRET_KEY, DB, EMAIL
   ```
5. **Migrations**

   ```sh
   python manage.py migrate
   ```
6. **Superuser**

   ```sh
   python manage.py createsuperuser
   ```
7. **Run**

   ```sh
   python manage.py runserver
   ```

## 🌐 API Docs

* Swagger UI: `/swagger/`
* ReDoc: `/redoc/`
* JSON: `/swagger.json`

## ✅ Tests

```sh
python manage.py test
```

## 🛡 Security

* `DEBUG=False`, `ALLOWED_HOSTS` enforced
* HTTPS & secure cookies
* JWT rotation & blacklist
* `.env` via python-decouple

## 🐳 Docker / Deployment

* Dockerfile & docker-compose (planned)
* Nginx + Gunicorn configs (planned)

## 📜 License

MIT License — see LICENSE

## 💌 Contact

Email: [hatef.barin97@gmail.com](mailto:hatef.barin97@gmail.com)
GitHub: [https://github.com/hatef97/bodybuilding-website](https://github.com/hatef97/bodybuilding-website)
