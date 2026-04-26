"""
Knowledge Graph and GraphRAG Module
===================================

This module organizes health data as a knowledge graph and performs GraphRAG queries.
It models relationships between ingredients, nutrients, recipes, and health conditions.

PURPOSE:
- Organize health data in graph structure
- Model ingredient-nutrient-recipe relationships
- Perform intelligent search with GraphRAG queries
- Provide contextual recommendations

REASON FOR CREATION:
- Structure complex health data
- Provide relational search and analysis
- Offer AI-powered recommendations
- Optimize information access

TECHNOLOGIES USED:
- NetworkX: Graph data structures
- GraphRAG: Retrieval-Augmented Generation
- Knowledge Graph: Knowledge graph
- Contextual Search: Contextual search

FEATURES:
- Ingredient-nutrient matching
- Recipe recommendations
- Health goals connection
- Intelligent search algorithms
"""

# === GraphRAG and Knowledge Graph ===
# Forward reference support for Python 3.7+
from __future__ import annotations

# NetworkX: Popular Python graph library
import networkx as nx
from typing import Dict, Any, List  # Type hints

class GraphRAG:
	"""
	A lightweight GraphRAG using networkx. We store a small knowledge graph of
	recipes, ingredients, nutrients, and conditions. Query performs simple keyword
	match and returns traversed context to act as augmentation for agents.
	"""

	def __init__(self) -> None:
		# GraphRAG constructor
		self.graph = nx.Graph()
		# Populate the graph with seed data
		self._seed()

	# Function to fill the chart with initial data
	def _seed(self) -> None:
		g = self.graph
		# Ingredients
		# Node ID = "ing:ingredient_name", kind = ingredient, name = ing
		for ing in ["chicken", "rice", "broccoli", "salmon", "quinoa", "spinach", "tomato", "olive oil"]:
			g.add_node(f"ing:{ing}", kind="ingredient", name=ing)
		# Nutrients
		# Node ID = "nut:nutrient_name", kind = nutrient, name = nut
		for nut in ["protein", "carb", "fat", "fiber", "vitamin c", "omega-3"]:
			g.add_node(f"nut:{nut}", kind="nutrient", name=nut)
		# Conditions / goals
		# Node ID = "cond:condition_name", kind = condition, name = cond
		for cond in ["weight loss", "muscle gain", "heart health", "diabetes"]:
			g.add_node(f"cond:{cond}", kind="condition", name=cond)
		# Recipes
		recipes = {
			"simple chicken rice": ["chicken", "rice", "olive oil", "tomato"],
			"salmon quinoa bowl": ["salmon", "quinoa", "spinach", "olive oil"],
			"broccoli stir fry": ["broccoli", "rice", "olive oil", "tomato"],
		}
		for rname, ings in recipes.items():
			g.add_node(f"rec:{rname}", kind="recipe", name=rname)
			for ing in ings:
				# Adds edges between recipe and ingredients
				g.add_edge(f"rec:{rname}", f"ing:{ing}")
		# Links ingredient -> nutrient (toy mapping)
		links = {
			"chicken": ["protein"],
			"salmon": ["protein", "omega-3"],
			"quinoa": ["protein", "carb", "fiber"],
			"rice": ["carb"],
			"broccoli": ["fiber", "vitamin c"],
			"spinach": ["fiber", "vitamin c"],
		}
		for ing, nuts in links.items():
			for n in nuts:
				# Adds edges between ingredient and nutrient
				g.add_edge(f"ing:{ing}", f"nut:{n}")
		# Goals to nutrients
		# Connects health goals to relevant nutrients
		g.add_edge("cond:weight loss", "nut:protein")
		g.add_edge("cond:weight loss", "nut:fiber")
		g.add_edge("cond:heart health", "nut:omega-3")

	# Simple keyword match query
	def query(self, text: str) -> Dict[str, Any]:
		text_l = text.lower()
		hits: List[str] = []
		for node, data in self.graph.nodes(data=True):
			name = str(data.get("name", "")).lower()
			if name and name in text_l:
				hits.append(node)
		# If no hits, suggest common ingredients
		if not hits:
			suggested = [n for n, d in self.graph.nodes(data=True) if d.get("kind") == "ingredient"][:4]
			return {"hits": [], "suggested_ingredients": [self.graph.nodes[s]["name"] for s in suggested]}
		# Collect neighborhood context
		context_nodes = set(hits)
		for h in hits:
			context_nodes.update(self.graph.neighbors(h))
		# Add neighboring nodes of hit nodes to context	
		# Returns id, kind, name for context
		context = [{"id": n, "kind": self.graph.nodes[n].get("kind"), "name": self.graph.nodes[n].get("name")} for n in context_nodes]
		# Collect ingredients from context
		ingredients = [c["name"] for c in context if c.get("kind") == "ingredient"]
		# Return up to 5 suggested ingredients
		return {"hits": hits, "context": context, "suggested_ingredients": ingredients[:5]}
