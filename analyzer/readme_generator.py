# from typing import Dict, Any, List, Tuple

# class ReadmeGenerator:
#     def generate_readme(self, analysis: Dict[str, Any], project_name: str, 
#                        domains: List[Tuple[str, float]], summary: str,
#                        complexity_level: str, complexity_details: Dict[str, Any]) -> str:
        
#         readme = f"# {project_name}\n\n"
#         readme += self._generate_overview(analysis, domains, summary, complexity_level)
#         readme += self._generate_domain_breakdown(domains)
#         readme += self._generate_project_description(analysis, summary)
#         readme += self._generate_technical_stack(analysis)
#         readme += self._generate_architecture_section(analysis)
#         readme += self._generate_complexity_analysis(complexity_details)
#         readme += self._generate_key_capabilities(analysis)
        
#         return readme
    
#     def _generate_overview(self, analysis: Dict[str, Any], 
#                           domains: List[Tuple[str, float]], 
#                           summary: str, level: str) -> str:
#         section = "## 🎯 Project Overview\n\n"
#         section += f"{summary}\n\n"
#         section += f"**Complexity Level**: {level}\n\n"
        
#         metrics = analysis.get('complexity_metrics', {})
#         section += f"**Codebase Size**: {metrics.get('total_nloc', 0)} lines of code\n\n"
#         return section
    
#     def _generate_domain_breakdown(self, domains: List[Tuple[str, float]]) -> str:
#         section = "## 📊 Domain Analysis\n\n"
#         section += "This project involves multiple domains:\n\n"
        
#         for domain, percentage in domains:
#             domain_name = domain.replace('_', ' ').title()
#             bar_length = int(percentage * 20)
#             bar = "█" * bar_length + "░" * (20 - bar_length)
#             section += f"- **{domain_name}**: {percentage*100:.1f}% {bar}\n"
        
#         section += "\n"
        
#         if domains:
#             primary = domains[0][0].replace('_', ' ').title()
#             section += f"**Primary Focus**: {primary}\n\n"
            
#             if len(domains) > 1:
#                 secondary = ", ".join([d[0].replace('_', ' ').title() for d in domains[1:3]])
#                 section += f"**Supporting Domains**: {secondary}\n\n"
        
#         return section
    
#     def _generate_project_description(self, analysis: Dict[str, Any], summary: str) -> str:
#         section = "## 📝 What This Project Does\n\n"
        
#         # Get project context
#         project_context = analysis.get('project_context', {})
#         purpose = project_context.get('purpose', 'unknown')
#         main_functionality = project_context.get('main_functionality', [])
#         data_flow = project_context.get('data_flow', [])
        
#         # Add summary
#         section += f"{summary}\n\n"
        
#         # Add detailed functionality
#         if main_functionality:
#             section += "### Core Functionality\n\n"
#             for i, func in enumerate(main_functionality, 1):
#                 section += f"{i}. **{func}**\n"
#             section += "\n"
        
#         # Add data flow
#         if data_flow:
#             section += "### Data Flow\n\n"
#             for i, flow in enumerate(data_flow, 1):
#                 section += f"{i}. {flow}\n"
#             section += "\n"
        
#         return section
    
#     def _generate_technical_stack(self, analysis: Dict[str, Any]) -> str:
#         section = "## 🛠️ Technical Stack\n\n"
        
#         all_imports = []
#         for file in analysis.get('files', []):
#             all_imports.extend(file.get('imports', []))
        
#         categories = {
#             'ML/AI Frameworks': ['sentence_transformers', 'sentence-transformers', 'transformers', 
#                                 'sklearn', 'tensorflow', 'torch', 'keras'],
#             'Vector Databases': ['faiss', 'pinecone', 'weaviate', 'chromadb', 'qdrant'],
#             'LLM Frameworks': ['langchain', 'llamaindex', 'llama-index'],
#             'LLM APIs': ['openai', 'anthropic', 'groq', 'cohere'],
#             'Web Frameworks': ['fastapi', 'flask', 'django', 'starlette'],
#             'Data Processing': ['pandas', 'numpy', 'scipy', 'polars']
#         }
        
#         categorized = {cat: [] for cat in categories}
        
#         for imp in set(all_imports):
#             for category, libs in categories.items():
#                 if any(lib in imp.lower() for lib in libs):
#                     categorized[category].append(imp)
#                     break
        
#         for category, libs in categorized.items():
#             if libs:
#                 section += f"### {category}\n"
#                 for lib in sorted(libs):
#                     section += f"- `{lib}`\n"
#                 section += "\n"
        
#         return section
    
#     def _generate_architecture_section(self, analysis: Dict[str, Any]) -> str:
#         section = "## 🏗️ Architecture\n\n"
        
#         arch = analysis.get('architectural_style', 'Monolithic')
#         section += f"**Pattern**: {arch}\n\n"
        
#         files = analysis.get('files', [])
#         total_classes = sum(len(f.get('classes', [])) for f in files)
#         total_functions = sum(len(f.get('functions', [])) for f in files)
        
#         section += f"- **Files**: {len(files)}\n"
#         section += f"- **Classes**: {total_classes}\n"
#         section += f"- **Functions**: {total_functions}\n\n"
        
#         patterns = analysis.get('semantic_patterns', {})
#         if patterns.get('uses_async'):
#             section += "**Programming Style**: Asynchronous\n\n"
        
#         return section
    
#     def _generate_complexity_analysis(self, details: Dict[str, Any]) -> str:
#         section = "## 📈 Complexity Assessment\n\n"
        
#         reasons = details.get('reasons', [])
#         if reasons:
#             for reason in reasons:
#                 section += f"- {reason}\n"
#             section += "\n"
        
#         return section
    
#     def _generate_key_capabilities(self, analysis: Dict[str, Any]) -> str:
#         section = "## ✨ Key Capabilities\n\n"
        
#         features = set()
        
#         for file in analysis.get('files', []):
#             logic = file.get('business_logic', {})
#             if logic.get('has_authentication'):
#                 features.add("🔐 Authentication & Authorization")
#             if logic.get('has_database_ops'):
#                 features.add("💾 Database Operations")
#             if logic.get('has_api_calls'):
#                 features.add("🌐 External API Integration")
#             if logic.get('has_validation'):
#                 features.add("✅ Data Validation")
        
#         all_imports = []
#         for file in analysis.get('files', []):
#             all_imports.extend(file.get('imports', []))
#         imports_str = ' '.join(all_imports).lower()
        
#         if 'sentence_transformers' in imports_str or 'sentence-transformers' in imports_str:
#             features.add("🧠 Semantic Text Embeddings")
#         if 'faiss' in imports_str:
#             features.add("🔍 Vector Similarity Search")
#         if 'langchain' in imports_str:
#             features.add("⛓️ LLM Chain Orchestration")
#         if any(llm in imports_str for llm in ['openai', 'anthropic', 'groq']):
#             features.add("🤖 Large Language Model Integration")
#         if 'fastapi' in imports_str:
#             features.add("⚡ High-Performance REST API")
        
#         algorithms = set()
#         for file in analysis.get('files', []):
#             algorithms.update(file.get('algorithms', []))
        
#         if algorithms:
#             features.add(f"🧮 Algorithm Implementation: {', '.join(algorithms)}")
        
#         for feature in sorted(features):
#             section += f"- {feature}\n"
        
#         return section + "\n"


import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class ReadmeGenerator:

    def _compute_stack_breakdown(self, analysis):
        all_imports = []
        for file in analysis.get('files', []):
            all_imports.extend(file.get('imports', []))

        categories = {
            'ML / AI': ['sklearn', 'tensorflow', 'torch', 'keras', 'xgboost', 'transformers', 'sentence_transformers'],
            'Vector DB': ['faiss', 'pinecone', 'chromadb', 'weaviate', 'qdrant'],
            'LLM / NLP': ['langchain', 'llamaindex', 'openai', 'anthropic', 'groq', 'cohere', 'nltk', 'spacy'],
            'Web Framework': ['flask', 'fastapi', 'django', 'starlette', 'aiohttp'],
            'Data Processing': ['pandas', 'numpy', 'scipy', 'polars', 'pyarrow'],
            'Computer Vision': ['cv2', 'PIL', 'pillow', 'skimage', 'imageio'],
            'Database': ['sqlalchemy', 'pymongo', 'psycopg2', 'redis', 'pymysql'],
            'DevOps / Cloud': ['boto3', 'docker', 'kubernetes', 'airflow', 'celery'],
            'Testing': ['pytest', 'unittest', 'mock'],
            'Utilities': ['os', 'sys', 'json', 'requests', 'httpx', 'dotenv', 'pydantic']
        }

        counts = {cat: 0 for cat in categories}
        for imp in set(all_imports):
            imp_lower = imp.lower()
            for cat, libs in categories.items():
                if any(lib in imp_lower for lib in libs):
                    counts[cat] += 1
                    break

        total = sum(counts.values()) or 1
        breakdown = {cat: round((count / total) * 100, 1) for cat, count in counts.items() if count > 0}
        return dict(sorted(breakdown.items(), key=lambda x: x[1], reverse=True))

    def generate_readme(self, analysis, project_name, domains, summary, complexity):
        metrics = analysis.get('complexity_metrics', {})
        patterns = analysis.get('semantic_patterns', {})
        context = analysis.get('project_context', {})
        files = analysis.get('files', [])

        stack_breakdown = self._compute_stack_breakdown(analysis)
        total_files = len(files)
        total_functions = sum(len(f.get('functions', [])) for f in files)
        total_classes = sum(len(f.get('classes', [])) for f in files)
        avg_complexity = metrics.get('avg_complexity', 0)
        total_loc = metrics.get('total_nloc', 0)
        uses_async = patterns.get('uses_async', False)

        prompt = f"""
        Generate a professional GitHub README in Markdown.

        Project Name: {project_name}
        Summary: {summary}
        Domains: {domains}

        === DIFFICULTY & COMPLEXITY ===
        Difficulty Level: {complexity}
        Average Cyclomatic Complexity: {avg_complexity:.1f}
        Total Lines of Code: {total_loc}
        Files: {total_files} | Classes: {total_classes} | Functions: {total_functions}
        Uses Async: {uses_async}

        === TECH STACK BREAKDOWN (by usage share) ===
        {stack_breakdown}
        Show each category as a percentage bar like: ML/AI ████████░░ 62%

        === PROJECT CONTEXT ===
        Detected frameworks/tech: {context.get('tech_signals')}
        Dependencies: {context.get('dependencies')}
        Imports: {context.get('imports')}
        API Endpoints: {context.get('api_endpoints')}
        Code Patterns: {context.get('code_patterns')}

        The README must include these sections in order:
        1. Project title and one-line description
        2. Overview (what it does, who it's for)
        3. Difficulty Level — show the level ({complexity}) with a brief explanation of why
        4. Tech Stack Breakdown — show each category with a visual percentage bar
        5. Features
        6. Architecture & Code Metrics (files, classes, functions, async, patterns)
        7. API Endpoints (if any)
        8. Use Cases
        """

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content