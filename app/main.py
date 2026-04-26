"""
Health Coach FastAPI Server - Main Entry Point
==============================================

This file is the main entry point for the Health Coach application.
It starts the FastAPI application and exposes all endpoints.

PURPOSE:
- Comprehensive API system providing health coaching services
- Data fetching from real sources (USDA, FDA, DrugBank)
- Specialized health analysis with multi-agent system
- Knowledge graph queries with GraphRAG technology

REASON FOR CREATION:
- Analyze user health data
- Check drug-food interactions
- Create nutrition plans
- Monitor health safety
- Provide personalized health recommendations

TECHNOLOGIES USED:
- FastAPI: Modern web framework
- Uvicorn: ASGI server
- Real APIs: USDA, FDA, DrugBank, Nutritionix
- AI Agents: Profile, Nutrition, Medical, Recipe, Vision, etc.
- GraphRAG: Knowledge graph-based queries
"""

import os
from orchestrator import app  # FastAPI app

# Health Coach FastAPI Server
# Geliştirilmiş sağlık koçluğu uygulaması

# Hızlı başlatma komutları:
# 1) Windows: start_server.bat
# 2) Mac/Linux: python start_server.py
# 3) Manuel: uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Erişim adresleri:
# - Ana sayfa: http://127.0.0.1:8000
# - API dokümantasyonu: http://127.0.0.1:8000/docs
# - Alternatif dokümantasyon: http://127.0.0.1:8000/redoc

# Environment Variables (Opsiyonel):
# - GEMINI_API_KEY: Google AI API anahtarı
# - USDA_API_KEY: USDA Food Database API anahtarı  
# - NUTRITIONIX_APP_ID: Nutritionix uygulama ID'si
# - NUTRITIONIX_API_KEY: Nutritionix API anahtarı
# - POSTGRES_DSN: PostgreSQL veritabanı bağlantısı
# - REDIS_URL: Redis cache bağlantısı
# - MINIO_ENDPOINT: MinIO object storage endpoint'i
# - OBJECT_BUCKET: MinIO bucket adı

# Yeni özellikler:
# ✅ Gerçek veri kaynakları entegrasyonu (USDA, FDA, DrugBank)
# ✅ Gelişmiş beslenme analizi
# ✅ İlaç-gıda etkileşim kontrolü
# ✅ Gıda güvenlik monitöringi
# ✅ Kişiselleştirilmiş sağlık önerileri
# ✅ Kolay başlatma scriptleri
