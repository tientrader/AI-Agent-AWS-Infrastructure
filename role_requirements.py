from typing import Dict

ROLE_REQUIREMENTS: Dict[str, str] = {
    "ai_ml_engineer": """
        **Core Skills:**
        - Python, PyTorch, TensorFlow, JAX
        - Understanding of mathematical foundations (Linear Algebra, Probability, Statistics)
        - Machine Learning algorithms (Supervised, Unsupervised, Reinforcement Learning)
        - Deep Learning architectures (CNN, RNN, Transformer, GANs)
        - Data preprocessing and feature engineering
        - Model evaluation and hyperparameter tuning
        
        **MLOps & Deployment:**
        - Model training and evaluation pipelines
        - Model versioning and reproducibility (MLflow, DVC)
        - API deployment (FastAPI, Flask, gRPC)
        - Scalable model deployment (Docker, Kubernetes, AWS/GCP/Azure)
        - Monitoring and debugging ML models in production

        **Specialized Skills:**
        - RAG (Retrieval-Augmented Generation), LLM fine-tuning, and inference optimization
        - Vector databases (Pinecone, FAISS, Weaviate)
        - Prompt Engineering and tuning for large-scale AI models
        - Distributed computing for ML (Ray, Spark, Dask)
        - Edge AI and model quantization (ONNX, TensorRT, TFLite)

        **Tools & Tech Stack:**
        - Python, Jupyter, NumPy, Pandas, SciPy
        - PyTorch, TensorFlow, Hugging Face Transformers
        - SQL, NoSQL, Redis, Apache Kafka
        - AWS Sagemaker, GCP Vertex AI, Azure ML
        - Kubernetes, Docker, Terraform, Airflow
    """,

    "frontend_engineer": """
        **Core Skills:**
        - Strong understanding of JavaScript and TypeScript
        - Experience with modern frontend frameworks (React.js, Next.js, Vue.js, Angular)
        - Proficiency in HTML5, CSS3, TailwindCSS, SCSS
        - State management (Redux, Zustand, Vuex, Pinia, NgRx)
        - UI component libraries (Material UI, Ant Design, Chakra UI)
        - SSR (Server-Side Rendering) and CSR (Client-Side Rendering)

        **Performance & Optimization:**
        - Web performance optimization (Lighthouse, Core Web Vitals)
        - Code splitting, lazy loading, tree shaking
        - Caching strategies (Service Workers, IndexedDB, LocalStorage)
        - Accessibility (ARIA, WCAG compliance)
        - Progressive Web Apps (PWA)

        **Testing & CI/CD:**
        - Unit testing, integration testing (Jest, Testing Library, Cypress, Playwright)
        - Linting, formatting (ESLint, Prettier)
        - CI/CD pipelines for frontend deployment (GitHub Actions, Vercel, Netlify)

        **Tools & Tech Stack:**
        - JavaScript, TypeScript, HTML5, CSS3
        - React.js, Next.js, Vue.js, Angular
        - Redux, Zustand, React Query, Apollo Client
        - TailwindCSS, Material UI, Ant Design
        - Jest, Cypress, Playwright
        - Webpack, Vite, Rollup
    """,

    "backend_engineer": """
        **Core Skills:**
        - Strong proficiency in Java, JavaScript, Python or C++
        - Understanding of RESTful API
        - Software design patterns (Factory, Singleton, Observer, Strategy, etc.)
        - ACID, SOLID principles, Clean Architecture, Hexagonal Architecture
        - Algorithms, data structures, and system design

        **Scalability & Distributed Systems:**
        - Microservices architecture, CQRS, Event Sourcing
        - Message brokers (Kafka, RabbitMQ)
        - Caching strategies (Redis, Memcached)
        - Database scaling (Sharding, Replication, Partitioning)
        - High-throughput and low-latency services
        - API Gateway and service mesh (Spring Cloud Gateway, Istio)

        **Databases & Storage:**
        - Relational databases (PostgreSQL, MySQL, SQL Server)
        - NoSQL databases (MongoDB, Cassandra, DynamoDB)
        - Full-text search engines (Elasticsearch, OpenSearch)

        **Cloud & DevOps:**
        - Cloud platforms: AWS, GCP, Azure
        - Infrastructure as Code (Terraform, AWS CDK)
        - Containerization & orchestration (Docker, Kubernetes)
        - Observability (Prometheus, Grafana, OpenTelemetry, CloudWatch, ELK Stack)
        - Security best practices (OAuth2, JWT, mTLS)

        **Tools & Tech Stack:**
        - Java (Spring Boot), Python (FastAPI, Django)
        - Redis, Kafka, PostgreSQL, Elasticsearch
        - AWS Lambda, ECS, EKS, S3, CloudFront
        - Kubernetes, Terraform, Helm, CI/CD pipelines
    """
}