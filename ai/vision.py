"""
Image Analysis and Recognition Module
====================================

This module analyzes images to detect food and health-related tags.
It performs intelligent image analysis using Google Gemini Vision AI.

PURPOSE:
- Recognize food items in images
- Detect health-related objects
- Provide visual data for nutrition analysis
- Perform automatic labeling

REASON FOR CREATION:
- Provide visual nutrition tracking
- Improve user experience
- Reduce manual labeling needs
- Offer AI-powered image analysis

TECHNOLOGIES USED:
- Google Gemini Vision AI: Advanced image analysis
- Computer Vision: Image processing algorithms
- Machine Learning: Food recognition models
- Fallback Heuristics: Backup recognition system

FEATURES:
- Multi-food type recognition
- Health object detection
- Automatic tag generation
- Fallback system for error cases
"""

# === Image Analysis ===
from typing import List  # Type hints
import os               # File operations
import io               # Byte stream operations

# === Google Gemini AI ===
# Google Gemini Vision AI integration
try:
	import google.generativeai as genai
except Exception:
	genai = None

# === Environment Variables ===
# API key and model configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", "gemini-1.5-flash")

# === Model Initialization ===
# Configure Gemini Vision model
if GEMINI_API_KEY and genai:
	try:
		genai.configure(api_key=GEMINI_API_KEY)
		vision_model = genai.GenerativeModel(GEMINI_VISION_MODEL)
	except Exception:
		vision_model = None
else:
	vision_model = None


def vision_agent(image_path: str) -> List[str]:
	"""
	Analyze an image and return a list of detected health/food-related tags.
	Uses Gemini Vision when available; otherwise returns a heuristic fallback.
	"""
	if not image_path:
		return []
	if vision_model:
		try:
			with open(image_path, "rb") as f:
				image_bytes = f.read()
			resp = vision_model.generate_content([{"mime_type": "image/jpeg", "data": image_bytes}, "List 5 concise tags for the food items/utensils in this image."])
			text = (resp.text or "").strip()
			if text:
				# split on commas or newlines
				parts = [p.strip("- *\n ") for p in (text.replace("\n", ",").split(","))]
				return [p for p in parts if p]
		except Exception:
			pass
	# Fallback: filename heuristic
	name = os.path.basename(image_path).lower()
	tags: List[str] = []
	for k in ["salmon", "chicken", "broccoli", "rice", "pan", "bowl", "tomato", "spinach"]:
		if k in name:
			tags.append(k)
	return tags[:5]
