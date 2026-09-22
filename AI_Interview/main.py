import os
# Override HuggingFace global cache variables to prevent it from using the missing F:\ drive
os.environ["HF_HOME"] = os.path.join(os.getcwd(), "models")
os.environ["HUGGINGFACE_HUB_CACHE"] = os.path.join(os.getcwd(), "models")

import asyncio
from integration.full_pipeline import FullInterviewPipeline

async def main_async():
    pipeline = FullInterviewPipeline()
    await pipeline.run()

if __name__ == "__main__":
    asyncio.run(main_async())
