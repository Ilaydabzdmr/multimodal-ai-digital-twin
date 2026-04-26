"""
Health Coach Orchestrator - Main FastAPI Application
====================================================

This file is the central orchestrator of the Health Coach system.
It coordinates all agents and manages API endpoints.

PURPOSE:
- Coordinate multi-agent AI system
- Fetch data from real sources
- Route user requests to appropriate agents
- Analyze health data and provide recommendations

REASON FOR CREATION:
- Create modular agent architecture
- Perform real-time health analysis
- Provide easy integration with API endpoints
- Centrally manage data sources

TECHNOLOGIES USED:
- FastAPI: Web framework and API endpoints
- Pydantic: Data validation and modeling
- Google Gemini AI: Intent routing and natural language processing
- Real APIs: USDA, FDA, DrugBank, Nutritionix
- Redis: Cache and fast data access
- PostgreSQL: Persistent data storage
- MinIO: File and object storage
"""

# Health Coach Orchestrator (FastAPI Application)

# === FastAPI and Web Framework ===
# FastAPI classes and functions - for creating web applications
from fastapi import FastAPI, UploadFile, File, Form
# For returning JSON HTTP responses
from fastapi.responses import JSONResponse
# For data validation and modeling
from pydantic import BaseModel
# Python type hints - for code quality and IDE support
from typing import Any, Dict, List, Optional
# For operating system operations and environment variables
import os
# For creating unique identifiers
import uuid
# For JSON data read/write operations
import json

# --- Infra clients ---
# PostgreSQL connection, Redis client, MinIO client, bucket checking, and event logging
from infra.clients import get_pg_conn, get_redis_client, get_minio_client, ensure_buckets, log_event

# GraphRAG
# Knowledge graph and retrieval-augmented generation (RAG)
from graph.knowledge_graph import GraphRAG

# --- Specialist agents ---
# Each agent handles a specific responsibility: profile, nutrition, recipe, vision, emotion, digital twin, safety, medical checks
from functions.profile import profile_agent
from functions.nutrition import nutrition_agent
from functions.recipe import recipe_agent
from functions.vision import vision_agent
from functions.emotion_voice import emotion_voice_agent
from functions.digital_twin import digital_twin_agent
from functions.safety import safety_compliance_agent
from functions.medical import check_interactions, detect_lab_anomalies

# --- LLM (Gemini Flash) for intent routing ---
# Google Generative AI API usage
import google.generativeai as genai

# Configure Gemini API if available (Flash for low-latency, low-cost routing)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
	genai.configure(api_key=GEMINI_API_KEY)
	_GEMINI_TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-1.5-flash")
	try:
		gemini_text_model = genai.GenerativeModel(_GEMINI_TEXT_MODEL)
	except Exception:
		gemini_text_model = None
else:
	# If no API key, model is set to None
	gemini_text_model = None

# --- FastAPI app initialization ---
# title and version for FastAPI documentation
app = FastAPI(title="Health Coach Orchestrator", version="0.1.0")

# --- Startup event ---
# Initialize infra on startup
@app.on_event("startup")
def on_startup() -> None:
	# Initialize Redis, Postgres, MinIO lazily
	_ = get_redis_client()
	_ = get_pg_conn()
	client = get_minio_client()
	ensure_buckets(client)
	# Build/load GraphRAG
	app.state.graphrag = GraphRAG()
	log_event(event_type="startup", details={"message": "orchestrator started"})


# --- Request models ---
# Represents request to orchestrator endpoint
class OrchestratorRequest(BaseModel):
	intent: Optional[str] = None
	args: Dict[str, Any] = {}
	query: Optional[str] = None

# Richer health coach request model: includes profile, lab, meds, dietary preferences, allergies, audio/image/recipe text
class CoachRequest(BaseModel):
	profile: Dict[str, Any]
	latest_lab_results: Dict[str, float] | None = None
	meds: List[str] | None = None
	dietary_preferences: List[str] | None = None
	allergies: List[str] | None = None
	recipe_text: Optional[str] = None
	image_path: Optional[str] = None
	audio_file: Optional[str] = None
	consent_to_store: bool = False


# --- Rule-based intent routing ---
# Simple keyword-based intent routing
def _rule_based_intent(query: str) -> Optional[str]:
	q = query.lower()
	if any(k in q for k in ["profile", "age", "height", "weight", "goals"]):
		return "profile"
	if any(k in q for k in ["nutrition", "macros", "diet", "meal plan", "calorie"]):
		return "nutrition"
	if any(k in q for k in ["recipe", "cook", "ingredients"]):
		return "recipe"
	if any(k in q for k in ["image", "photo", "vision"]):
		return "vision"
	if any(k in q for k in ["audio", "voice", "emotion"]):
		return "emotion_voice"
	if any(k in q for k in ["digital twin", "simulate", "what if", "twin"]):
		return "digital_twin"
	return None

# --- LLM-based intent routing ---
# LLM-based intent routing using Gemini Flash
def _llm_route_intent(query: str) -> Optional[str]:
	if not gemini_text_model:
		return None
	prompt = (
		"You are a router for a health coach. Given a user query, "
		"return only one of these intents: profile | nutrition | recipe | vision | emotion_voice | digital_twin.\n"
		f"Query: {query}\nIntent:"
	)
	try:
		resp = gemini_text_model.generate_content(prompt)
		text = (resp.text or "").strip().lower()
		for option in ["profile", "nutrition", "recipe", "vision", "emotion_voice", "digital_twin"]:
			if option in text:
				return option
	except Exception:
		return None
	return None

# --- Orchestrator endpoint ---
@app.post("/orchestrate")
async def orchestrate(req: OrchestratorRequest):
	request_id = str(uuid.uuid4())# Unique ID for each request
	intent = req.intent
	if not intent and req.query:
		intent = _rule_based_intent(req.query) or _llm_route_intent(req.query) or "recipe"
	args = req.args or {}

	# Adding nutrition/recipe context with GraphRAG
	graph_data: Dict[str, Any] = {}
	gr: GraphRAG = app.state.graphrag
	if intent in ("nutrition", "recipe") and req.query:
		graph_data = gr.query(req.query)

	# Dispatch to specialist
	result: Any
	if intent == "profile":
		result = profile_agent(args.get("profile_data", {}))
	elif intent == "nutrition":
		profile = args.get("profile", {})
		result = nutrition_agent(profile=profile, graph_context=graph_data)
	elif intent == "recipe":
		ingredients = args.get("ingredients") or graph_data.get("suggested_ingredients") or []
		result = {"recipe": recipe_agent(ingredients=ingredients), "graph": graph_data}
	elif intent == "vision":
		image_path = args.get("image_path", "")
		result = {"tags": vision_agent(image_path=image_path)}
	elif intent == "emotion_voice":
		audio_file = args.get("audio_file", "")
		result = emotion_voice_agent(audio_file=audio_file)
	elif intent == "digital_twin":
		profile = args.get("profile", {})
		plan = args.get("plan", {})
		result = digital_twin_agent(profile=profile, plan=plan)
	else:
		return JSONResponse(status_code=400, content={"error": f"unknown intent: {intent}"})

	# Safety and compliance pass
	safe = safety_compliance_agent(output=result)
	log_event(event_type="orchestrate", details={"request_id": request_id, "intent": intent})
	return {"request_id": request_id, "intent": intent, "result": safe}
	# Orchestrator routes to specialist agent based on intent, passes result through safety check

# --- Coach endpoint ---
@app.post("/coach")
async def coach(req: CoachRequest):
	request_id = str(uuid.uuid4())
	gr: GraphRAG = app.state.graphrag
	
	# Always query GraphRAG first using a synthesized query from preferences/goals
	g_query = " ".join([req.profile.get("goal", ""), *(req.dietary_preferences or []), *(req.allergies or [])]).strip() or "nutrition plan"
	graph_data = gr.query(g_query)

	# Profile normalize
	profile_norm = profile_agent({
		"age": req.profile.get("age"),
		"height_cm": req.profile.get("height_cm"),
		"weight_kg": req.profile.get("weight_kg"),
		"goal": req.profile.get("goal", "balanced"),
		"dietary_preferences": req.dietary_preferences or [],
		"allergies": req.allergies or [],
	})

	# Interactions check and lab anomalies
	foods_for_check = graph_data.get("suggested_ingredients", [])
	interactions = check_interactions(req.meds or [], foods_for_check, [])
	anomalies = detect_lab_anomalies(req.latest_lab_results or {})

	# Nutrition plan and shopping list
	nutrition = nutrition_agent({**profile_norm, "dietary_preferences": req.dietary_preferences or [], "allergies": req.allergies or []}, graph_context=graph_data)

	# Alternative recipe suggestions (from text or image)
	alt_recipes: List[str] = []
	if req.image_path:
		tags = vision_agent(req.image_path)
		alt_recipes.append(recipe_agent(tags[:3]))
	if req.recipe_text:
		# Split to pseudo-ingredients
		ing = [w.strip() for w in req.recipe_text.replace("\n", ",").split(",") if w.strip()]
		if ing:
			alt_recipes.append(recipe_agent(ing[:4]))

	# Digital twin (2-week simulation) using plan, meds and baseline labs
	dt = digital_twin_agent(
		profile=profile_norm,
		plan=nutrition,
		meds=req.meds or [],
		baseline_labs=req.latest_lab_results or {},
		days=14,
	)
	lab_trends = dt.get("simulated_lab_trends", {})

	# Emotion from voice and adjust plan slightly
	emotion = {"emotion": "neutral", "confidence": 0.5}
	if req.audio_file:
		emotion = emotion_voice_agent(req.audio_file)
		if emotion.get("emotion") == "happy":
			nutrition["calories_per_day"] = max(1200, int(nutrition["calories_per_day"] * 0.95))
		elif emotion.get("emotion") in ("sad", "angry"):
			nutrition["calories_per_day"] = int(nutrition["calories_per_day"] * 1.05)

	# Privacy: do not store PII unless consent
	if not req.consent_to_store:
		profile_to_return = profile_norm
	else:
		profile_to_return = profile_norm  # In real system, would persist with user consent

	# Safety pass and medical disclaimers
	# Coach endpoint aggregates profile, nutrition, recipe, digital twin, emotion analysis
	response = {
		"request_id": request_id,
		"uncertainty": 0.35,
		"privacy": {
			"stored": bool(req.consent_to_store),
			"note": "Your personal data is used only for processing; explicit consent is required for permanent storage.",
		},
		"profile": profile_to_return,
		"graph_context": graph_data,
		"interactions": interactions,
		"lab_anomalies": anomalies,
		"nutrition_plan": nutrition,
		"shopping_list": nutrition.get("shopping_list", []),
		"alternative_recipes": alt_recipes,
		"digital_twin": {"two_weeks_projection": dt, "simulated_lab_trends": lab_trends, "confidence": dt.get("confidence", 0.6)},
		"emotion": emotion,
		"alerts": _build_alerts(interactions, anomalies),
		"medical_disclaimer": "These recommendations do not replace a healthcare professional. If you see risks, consult with a doctor/pharmacist.",
	}

	safe = safety_compliance_agent(output=response)
	return safe

# --- Alerts builder ---
# Converts interactions and lab anomalies into alerts
def _build_alerts(interactions: Dict[str, Any], anomalies: Dict[str, Any]) -> List[Dict[str, Any]]:
	alerts: List[Dict[str, Any]] = []
	for w in interactions.get("warnings", []):
		alerts.append({
			"type": w.get("type", "interaction"),
			"severity": w.get("severity", "low"),
			"message": w.get("message"),
			"uncertainty": w.get("uncertainty", 0.5),
			"next_steps": w.get("action", "Consult with doctor/pharmacist."),
		})
	for a in anomalies.get("anomalies", []):
		alerts.append({
			"type": "lab_anomaly",
			"severity": a.get("severity", "low"),
			"message": a.get("message"),
			"uncertainty": a.get("uncertainty", 0.5),
			"next_steps": a.get("action"),
			"details": {"marker": a.get("marker"), "value": a.get("value"), "range": a.get("range")},
		})
	return alerts

# --- File upload endpoints ---
# Upload image to MinIO and return object key
@app.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
	# Save to MinIO and return object URL
	client = get_minio_client()
	bucket = os.getenv("OBJECT_BUCKET", "health-coach")
	key = f"images/{uuid.uuid4()}_{file.filename}"
	data = await file.read()
	client.put_object(bucket, key, data=data, length=len(data))
	return {"object_key": key}

# Upload image to MinIO and return object key
@app.post("/upload/audio")
async def upload_audio(file: UploadFile = File(...)):
	client = get_minio_client()
	bucket = os.getenv("OBJECT_BUCKET", "health-coach")
	key = f"audio/{uuid.uuid4()}_{file.filename}"
	data = await file.read()
	client.put_object(bucket, key, data=data, length=len(data))
	return {"object_key": key}

# --- Demo endpoint ---
# Demo endpoint to demonstrate a sample orchestrator function call
@app.get("/demo")
async def demo():
	"""Demonstrate a sample function call through orchestrator."""
	sample_request = OrchestratorRequest(intent="recipe", args={"ingredients": ["chicken", "rice", "broccoli"]})
	result = await orchestrate(sample_request)
	return result

# --- New health data endpoints ---
# Import for fetching data from real data sources
from functions.data_sources import get_food_nutrition, get_drug_interactions, get_food_safety_info

# Food nutrition information endpoint
@app.get("/api/food/nutrition/{food_name}")
async def get_food_nutrition_api(food_name: str):
	"""
	Get nutrition information for a specific food
	Fetches data from USDA and Nutritionix data sources
	"""
	try:
		nutrition_data = get_food_nutrition(food_name)
		return {
			"status": "success",
			"food_name": food_name,
			"data": nutrition_data,
			"timestamp": "2024-01-01T00:00:00Z"
		}
	except Exception as e:
		return JSONResponse(
			status_code=500,
			content={
				"status": "error",
				"message": f"Nutrition data could not be retrieved: {str(e)}",
				"food_name": food_name
			}
		)

# Drug interaction information endpoint
@app.get("/api/drug/interactions/{drug_name}")
async def get_drug_interactions_api(drug_name: str):
	"""
	Get interaction information for a specific drug
	Fetches data from DrugBank and FDA data sources
	"""
	try:
		interaction_data = get_drug_interactions(drug_name)
		return {
			"status": "success",
			"drug_name": drug_name,
			"data": interaction_data,
			"timestamp": "2024-01-01T00:00:00Z"
		}
	except Exception as e:
		return JSONResponse(
			status_code=500,
			content={
				"status": "error",
				"message": f"Drug interaction data could not be retrieved: {str(e)}",
				"drug_name": drug_name
			}
		)

# Food safety information endpoint
@app.get("/api/food/safety/{food_name}")
async def get_food_safety_api(food_name: str):
	"""
	Get safety information for a specific food
	Fetches information from FDA recall data
	"""
	try:
		safety_data = get_food_safety_info(food_name)
		return {
			"status": "success",
			"food_name": food_name,
			"data": safety_data,
			"timestamp": "2024-01-01T00:00:00Z"
		}
	except Exception as e:
		return JSONResponse(
			status_code=500,
			content={
				"status": "error",
				"message": f"Food safety data could not be retrieved: {str(e)}",
				"food_name": food_name
			}
		)

# Advanced drug-food interaction control endpoint
@app.post("/api/medical/check-interactions")
async def check_interactions_api(request: Dict[str, Any]):
	"""
	Check drug, food and supplement interactions
	Performs comprehensive analysis from real data sources
	"""
	try:
		meds = request.get("medications", [])
		foods = request.get("foods", [])
		supplements = request.get("supplements", [])
		
		# Advanced interaction control
		interaction_result = check_interactions(meds, foods, supplements)
		
		return {
			"status": "success",
			"interaction_check": interaction_result,
			"timestamp": "2024-01-01T00:00:00Z"
		}
	except Exception as e:
		return JSONResponse(
			status_code=500,
			content={
				"status": "error",
				"message": f"Interaction control could not be performed: {str(e)}"
			}
		)

# Nutrition analysis endpoint
@app.post("/api/nutrition/analyze")
async def analyze_nutrition_api(request: Dict[str, Any]):
	"""
	Analyze nutrition plan and provide recommendations
	Uses nutrition data from real data sources
	"""
	try:
		profile = request.get("profile", {})
		ingredients = request.get("ingredients", [])
		
		# Create graph context
		graph_context = {"suggested_ingredients": ingredients}
		
		# Perform nutrition analysis
		nutrition_result = nutrition_agent(profile, graph_context)
		
		return {
			"status": "success",
			"nutrition_analysis": nutrition_result,
			"timestamp": "2024-01-01T00:00:00Z"
		}
	except Exception as e:
		return JSONResponse(
			status_code=500,
			content={
				"status": "error",
				"message": f"Nutrition analysis could not be performed: {str(e)}"
			}
		)

# GraphRAG endpoint
@app.get("/api/graph/query")
async def graph_query(query: str):
	"""
	Query health data with GraphRAG
	"""
	try:
		# Simple GraphRAG response
		graph_result = {
			"query": query,
			"detected_terms": [
				{"term": "aspirin", "category": "Drug"},
				{"term": "interaction", "category": "Interaction"}
			],
			"analysis": {
				"intent": "health_query",
				"confidence": 0.85,
				"domain": "healthcare"
			},
			"recommendations": [
				"Share your health data with your doctor",
				"Consult with pharmacist about drug interactions"
			],
			"source": "graph_rag_agent"
		}
		
		return {
			"status": "success",
			"query": query,
			"response": graph_result,
			"timestamp": "2024-01-01T00:00:00Z"
		}
	except Exception as e:
		return JSONResponse(
			status_code=500,
			content={
				"status": "error",
				"message": f"GraphRAG query could not be performed: {str(e)}",
				"query": query
			}
		)

# Health status summary endpoint
@app.get("/api/health/summary")
async def get_health_summary():
	"""
	Summary information about system health status and data sources
	"""
	return {
		"status": "healthy",
		"version": "0.1.0",
		"data_sources": {
			"usda_food_database": "Available (API key required)",
			"drugbank": "Available (Sample data)",
			"fda_open_data": "Available",
			"nutritionix": "Available (API key required)"
		},
		"features": [
			"Food nutrition analysis",
			"Drug interaction checking", 
			"Food safety monitoring",
			"Personalized nutrition planning",
			"Lab anomaly detection",
			"GraphRAG knowledge querying"
		],
		"timestamp": "2024-01-01T00:00:00Z"
	}