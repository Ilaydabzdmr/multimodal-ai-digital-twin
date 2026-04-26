"""
Digital Twin Simulation Module
==============================

This module simulates user health data to predict future changes.
It models the effects of nutrition plans, medications, and lifestyle changes.

PURPOSE:
- Simulate health changes
- Predict effects of nutrition plans
- Model medication effects
- Make short-term health projections

REASON FOR CREATION:
- Provide motivation to users
- Show effects of nutrition plans
- Visualize health goals
- Provide educational simulations

TECHNOLOGIES USED:
- Digital Twin: Digital twin technology
- Health Simulation: Health simulation
- Predictive Modeling: Predictive modeling
- Calorie Balance: Calorie balance calculation

FEATURES:
- Weight change simulation
- Laboratory values prediction
- Medication effect modeling
- Daily tracking charts
"""

# === Digital Twin Simulation ===
from typing import Dict, Any, List, Optional  # Type hints


def digital_twin_agent(
	profile: Dict[str, Any],
	plan: Dict[str, Any],
	*,
	meds: Optional[List[str]] = None,
	baseline_labs: Optional[Dict[str, float]] = None,
	days: int = 14,
) -> Dict[str, Any]:
	"""
	Simulates short-term (default 14 days) health changes.
	Models effects of nutrition plans, medications and lifestyle changes.
	
	Args:
		profile: User profile data
		plan: Nutrition plan
		meds: List of medications used
		baseline_labs: Baseline laboratory values
		days: Number of simulation days
		
	Returns:
		Simulation results and projections
	"""
	
	# User's current weight
	weight = float(profile.get("weight_kg", 70))
	# Daily calorie intake
	calories = int(plan.get("calories_per_day", 2000))
	# Macronutrients: protein, carbs, fat
	macros = plan.get("macros", {"protein_g": 0, "carb_g": 0, "fat_g": 0})
	# Activity level: taken from plan or profile, default is moderate
	activity = (plan.get("activity") or profile.get("activity") or "moderate").lower()
	# Activity factor mapping
	activity_factor = {"low": 1.2, "moderate": 1.5, "high": 1.8}.get(activity, 1.5)
	# Maintenance calories: 24 * weight * activity factor
	maintenance = int(24 * weight * activity_factor)

	# Daily deficit (negative -> weight loss)
	deficit_per_day = calories - maintenance
	# Weight change over period: 7700 kcal ~ 1 kg
	weekly_delta_kg = round(deficit_per_day * 7 / 7700.0, 3)
	total_delta_kg = round(deficit_per_day * days / 7700.0, 3)
	# Estimated weight
	projected_weight_kg = round(weight + total_delta_kg, 2)

	# Build a trajectory per day
	trajectory = []
	current_weight = weight
	for d in range(1, days + 1):
		current_weight = round(current_weight + (deficit_per_day / 7700.0), 3)
		# Weight record is added for each day
		trajectory.append({"day": d, "weight_kg": round(current_weight, 2)})

	# Lab trends (toy):
	labs = dict(baseline_labs or {})
	trends: Dict[str, float] = {}
	if labs:
		protein_g = float(macros.get("protein_g", 0))
		fat_g = float(macros.get("fat_g", 0))
		carb_g = float(macros.get("carb_g", 0))
		# Normalized effect of calorie deficit: -0.5 to 0.5
		calorie_factor = max(-0.5, min(0.5, deficit_per_day / 1000.0))
		for marker, value in labs.items():
			new_v = float(value)
			if marker == "LDL":
				# Calorie deficit and lower fat intake can reduce LDL slightly
				new_v += calorie_factor * -2.0
				if fat_g < 60:
					new_v -= 1.0 * (days / 14)
				# Statin effect (if any)
				if any("statin" in (m or "").lower() for m in (meds or [])):
					new_v -= 5.0 * (days / 14)
			elif marker == "HDL":
				# Protein emphasis can nudge HDL mildly
				new_v += 0.3 * (protein_g / 150.0) * (days / 14)
			elif marker == "HbA1c":
				# Small reduction with deficit and lower carbs
				new_v += calorie_factor * -0.05 * (days / 14)
				if carb_g < 200:
					new_v -= 0.03 * (days / 14)
			elif marker == "FastingGlucose":
				new_v += calorie_factor * -2.0
				if carb_g < 200:
					new_v -= 1.0 * (days / 14)
			trends[marker] = round(new_v, 2)

	# Confidence: higher when inputs are richer
	inputs_present = 0
	inputs_present += 1 if baseline_labs else 0
	inputs_present += 1 if meds else 0
	inputs_present += 1 if macros and calories else 0
	confidence = 0.4 + 0.2 * inputs_present
	confidence = min(0.9, confidence)


# Function output
	return {
		"maintenance_kcal": maintenance,
		"calorie_deficit_per_day": deficit_per_day,
		"weekly_delta_kg": weekly_delta_kg,
		"total_delta_kg": total_delta_kg,
		"projected_weight_kg": projected_weight_kg,
		"weight_trajectory": trajectory,
		"simulated_lab_trends": trends,
		"confidence": round(confidence, 2),
	}
