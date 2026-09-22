# from typing import Dict, List, Any, Tuple
# from collections import defaultdict

# class MLDomainClassifier:
#     def __init__(self):
#         self.domains = ['machine_learning_ai', 'data_science', 'web_api_interface',
#                        'algorithms', 'devops', 'data_engineering', 'automation']
        
#     def classify_domain(self, analysis: Dict[str, Any]) -> Tuple[List[Tuple[str, float]], str]:
#         domain_scores = self._calculate_domain_scores(analysis)
#         significant_domains = [(k, v) for k, v in domain_scores.items() if v > 0.05]
#         significant_domains.sort(key=lambda x: x[1], reverse=True)
#         summary = self._generate_project_summary(analysis, significant_domains)
#         return significant_domains, summary
    
#     def _calculate_domain_scores(self, analysis: Dict[str, Any]) -> Dict[str, float]:
#         scores = defaultdict(float)
        
#         all_imports = []
#         for file in analysis.get('files', []):
#             all_imports.extend(file.get('imports', []))
#         imports_str = ' '.join(all_imports).lower()
        
#         # ML/AI - CRITICAL: Add missing libraries!
#         ml_weights = {
#             'sentence_transformers': 12, 'sentence-transformers': 12, 'transformers': 12,
#             'faiss': 12, 'pinecone': 10, 'chromadb': 10, 'weaviate': 10,
#             'langchain': 12, 'llamaindex': 12, 'openai': 10, 'anthropic': 10, 'groq': 10,
#             'sklearn': 10, 'tensorflow': 10, 'torch': 10, 'keras': 10, 'xgboost': 8
#         }
#         for lib, weight in ml_weights.items():
#             if lib in imports_str:
#                 scores['machine_learning_ai'] += weight
        
#         # Data Science
#         ds_weights = {'pandas': 8, 'numpy': 6, 'scipy': 6, 'matplotlib': 5, 'seaborn': 5}
#         for lib, weight in ds_weights.items():
#             if lib in imports_str:
#                 scores['data_science'] += weight
        
#         # Web/API (lower weight - it's just interface)
#         web_weights = {'fastapi': 5, 'flask': 5, 'django': 5, 'starlette': 4}
#         for lib, weight in web_weights.items():
#             if lib in imports_str:
#                 scores['web_api_interface'] += weight
        
#         # Check function names for ML patterns
#         all_functions = []
#         for file in analysis.get('files', []):
#             all_functions.extend([f['name'] for f in file.get('functions', [])])
#         func_str = ' '.join(all_functions).lower()
        
#         ml_patterns = ['embed', 'encode', 'predict', 'train', 'retrieve', 'search', 'query', 'generate']
#         ml_func_score = sum(3 for pattern in ml_patterns if pattern in func_str)
#         scores['machine_learning_ai'] += ml_func_score
        
#         # Normalize to percentages
#         total = sum(scores.values())
#         if total > 0:
#             scores = {k: v/total for k, v in scores.items()}
#         return dict(scores)
    
#     def _generate_project_summary(self, analysis: Dict[str, Any], domains: List[Tuple[str, float]]) -> str:
#         if not domains:
#             return "A general-purpose software project."
        
#         # Get advanced project context
#         project_context = analysis.get('project_context', {})
#         purpose = project_context.get('purpose', 'unknown')
#         business_domain = project_context.get('business_domain', 'general')
#         detected_features = project_context.get('detected_features', [])
        
#         all_imports = []
#         for file in analysis.get('files', []):
#             all_imports.extend(file.get('imports', []))
#         imports_str = ' '.join(all_imports).lower()
        
#         summary = ""
        
#         # RAG Document QA System
#         if purpose == 'rag_document_qa':
#             summary = "A Retrieval-Augmented Generation (RAG) system for intelligent document question-answering. "
            
#             if business_domain == 'insurance':
#                 summary += "Designed for insurance policy analysis. "
#             elif business_domain == 'healthcare':
#                 summary += "Designed for healthcare document analysis. "
#             elif business_domain == 'legal':
#                 summary += "Designed for legal document analysis. "
            
#             # Add features
#             if detected_features:
#                 summary += f"Features include: {', '.join(detected_features[:5])}."
        
#         # ML Inference/Prediction
#         elif purpose == 'ml_inference':
#             if business_domain == 'healthcare_prediction':
#                 summary = "A healthcare prediction application that uses machine learning to assess medical risks. "
#             elif business_domain == 'fraud_detection':
#                 summary = "A fraud detection system that identifies suspicious transactions using ML. "
#             elif business_domain == 'price_prediction':
#                 summary = "A price forecasting application that predicts values using ML models. "
#             elif business_domain == 'sentiment_analysis':
#                 summary = "A sentiment analysis tool that classifies text emotions using ML. "
#             else:
#                 summary = "A machine learning prediction application. "
            
#             # Add features
#             if detected_features:
#                 summary += f"Features: {', '.join(detected_features[:6])}."
        
#         # Chatbot
#         elif purpose == 'chatbot':
#             summary = "An AI-powered chatbot application. "
#             if detected_features:
#                 summary += f"Features: {', '.join(detected_features[:5])}."
        
#         # ML Training
#         elif purpose == 'ml_training':
#             summary = "A machine learning training pipeline. "
#             if detected_features:
#                 summary += f"Features: {', '.join(detected_features[:5])}."
        
#         # Data Pipeline
#         elif purpose == 'data_pipeline':
#             summary = "A data engineering pipeline. "
#             if detected_features:
#                 summary += f"Features: {', '.join(detected_features[:5])}."
        
#         # Search Engine
#         elif purpose == 'search_engine':
#             summary = "A search engine application. "
#             if detected_features:
#                 summary += f"Features: {', '.join(detected_features[:5])}."
        
#         # Web API
#         elif purpose == 'web_api':
#             summary = "A RESTful API service. "
#             if detected_features:
#                 summary += f"Endpoints: {', '.join([f for f in detected_features if 'API endpoint' in f][:3])}."
        
#         # Generic ML/AI
#         elif domains and domains[0][0] == 'machine_learning_ai':
#             summary = "An AI/ML application. "
#             if detected_features:
#                 summary += f"Features: {', '.join(detected_features[:5])}."
        
#         # Generic
#         else:
#             primary_domain = domains[0][0].replace('_', ' ').title() if domains else 'Software'
#             summary = f"A {primary_domain} project. "
#             if detected_features:
#                 summary += f"Features: {', '.join(detected_features[:5])}."
        
#         return summary.strip()
    
#     def assess_complexity_level(self, analysis: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
#         metrics = analysis.get('complexity_metrics', {})
#         patterns = analysis.get('semantic_patterns', {})
#         files = analysis.get('files', [])
        
#         score = 0
#         reasons = []
        
#         avg_complexity = metrics.get('avg_complexity', 0)
#         if avg_complexity > 10:
#             score += 3
#             reasons.append(f"High cyclomatic complexity ({avg_complexity:.1f})")
#         elif avg_complexity > 5:
#             score += 2
#             reasons.append(f"Moderate complexity ({avg_complexity:.1f})")
#         else:
#             score += 1
        
#         total_nloc = metrics.get('total_nloc', 0)
#         if total_nloc > 5000:
#             score += 3
#             reasons.append(f"Large codebase ({total_nloc} lines)")
#         elif total_nloc > 1000:
#             score += 2
#         else:
#             score += 1
        
#         # Check for advanced ML frameworks
#         all_imports = []
#         for file in files:
#             all_imports.extend(file.get('imports', []))
#         imports_str = ' '.join(all_imports).lower()
        
#         advanced_ml = ['sentence_transformers', 'faiss', 'langchain', 'transformers', 'tensorflow', 'torch']
#         ml_count = sum(1 for lib in advanced_ml if lib in imports_str)
        
#         if ml_count >= 3:
#             score += 4
#             reasons.append(f"Uses {ml_count} advanced ML/AI frameworks")
#         elif ml_count > 0:
#             score += 2
#             reasons.append(f"Uses {ml_count} ML frameworks")
        
#         if patterns.get('uses_async'):
#             score += 2
#             reasons.append("Implements asynchronous programming")
        
#         level = "Advanced" if score >= 12 else "Intermediate" if score >= 6 else "Beginner"
#         return level, {'score': score, 'reasons': reasons}
    
#     def generate_project_name(self, analysis: Dict[str, Any], domains: List[Tuple[str, float]]) -> str:
#         if not domains:
#             return "Software-Project"
        
#         primary_domain = domains[0][0]
#         domain_prefixes = {
#             'machine_learning_ai': 'AI',
#             'data_science': 'DataAnalytics',
#             'web_api_interface': 'API',
#             'algorithms': 'AlgoLib'
#         }
        
#         prefix = domain_prefixes.get(primary_domain, 'Project')
        
#         # Check for RAG
#         all_imports = []
#         for file in analysis.get('files', []):
#             all_imports.extend(file.get('imports', []))
#         imports_str = ' '.join(all_imports).lower()
        
#         if 'faiss' in imports_str and 'langchain' in imports_str:
#             return "AI-RAG-System"
        
#         # Extract meaningful terms
#         terms = []
#         for file in analysis.get('files', []):
#             for cls in file.get('classes', []):
#                 terms.append(cls['name'])
        
#         meaningful_terms = [t for t in terms if len(t) > 3 and not t.startswith('_') 
#                            and t.lower() not in ['main', 'test', 'app']]
        
#         if meaningful_terms:
#             return f"{prefix}-{meaningful_terms[0].replace('_', '').title()}"
        
#         return f"{prefix}-System"

import os
from dotenv import load_dotenv
from groq import Groq

# ✅ Load environment variables
load_dotenv()

# ✅ Initialize client AFTER loading .env
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class MLDomainClassifier:

    def classify_domain(self, analysis, clusters):
        context = analysis.get('project_context', {})
        has_python = bool(context.get('imports') or context.get('function_names'))

        prompt = f"""
        You are an expert software architect. Analyse the following signals extracted from a GitHub repository and determine exactly what the project does.

        File names in repo: {context.get('filenames')}
        Detected tech/frameworks: {context.get('tech_signals')}
        Dependencies/packages: {context.get('dependencies')}
        Imports used: {context.get('imports')}
        Function names: {context.get('function_names')}
        Class names: {context.get('class_names')}
        API endpoints: {context.get('api_endpoints')}
        Code patterns: {context.get('code_patterns')}
        File clusters: {clusters}

        Instructions:
        - Use tech_signals and dependencies as the strongest signals for non-Python projects
        - Use imports and function names as strongest signals for Python projects
        - File names and folder structure reveal the architecture (frontend/backend/mobile etc.)
        - Always give a confident, specific answer — never say insufficient data
        - Identify the primary language/framework from the signals above
        - Give a precise one-paragraph summary of what this project does

        Return STRICT JSON:
        {{
            "domains": [{{"name": "...", "percentage": 0.0}}],
            "summary": "..."
        }}
        """

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        import json

        try:
            raw = response.choices[0].message.content
            result = json.loads(raw)
        except Exception as e:
            print(f"⚠️ LLM returned invalid JSON: {e}")
            return [("unknown", 1.0)], "Could not parse project summary."

        domains = [(d["name"], d["percentage"]) for d in result["domains"]]
        summary = result["summary"]

        return domains, summary

    def assess_complexity_level(self, analysis):
        total_files = len(analysis.get("files", []))
        loc = analysis.get("complexity_metrics", {}).get("total_nloc", 0)

        score = total_files + (loc // 500)

        if score > 40:
            return "Advanced", {"score": score}
        elif score > 15:
            return "Intermediate", {"score": score}
        else:
            return "Beginner", {"score": score}

    def generate_project_name(self, summary):
        prompt = f"Generate a short professional project name (2-4 words, no quotes, no explanation, just the name) for:\n{summary}"

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content.strip()