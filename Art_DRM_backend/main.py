


# # Version 3 CNN

# from fastapi import FastAPI, UploadFile, File, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from database import db
# from datetime import datetime
# from motor.motor_asyncio import AsyncIOMotorGridFSBucket
# from bson import ObjectId
# import hashlib
# from PIL import Image
# import imagehash
# import io
# import numpy as np
# from ml_utils import get_embedding, cosine_similarity 

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], 
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# fs = AsyncIOMotorGridFSBucket(db)

# # Exact duplicate hash
# def get_file_hash(file_bytes: bytes) -> str:
#     return hashlib.sha256(file_bytes).hexdigest()

# # Perceptual hash
# def get_perceptual_hash(file_bytes: bytes):
#     image = Image.open(io.BytesIO(file_bytes))
#     return imagehash.phash(image)


# @app.post("/api/images/upload")
# async def upload_image(file: UploadFile = File(...)):
#     try:
#         contents = await file.read()

#         #  SHA256 Hash
#         file_hash = get_file_hash(contents)

#         #  Perceptual Hash
#         perceptual_hash = get_perceptual_hash(contents)

#         #  CNN Embedding
#         embedding = get_embedding(contents).tolist()

#         #  Exact SHA256 duplicate check 
#         existing = await db["images"].find_one({"hash": file_hash})
#         if existing:
#             return {"status": "duplicate_exact", "imageId": str(existing["_id"])}

#         #  Perceptual duplicate check 
#         cursor = db["images"].find({}, {"phash": 1})
#         async for doc in cursor:
#             if "phash" in doc:
#                 stored_phash = imagehash.hex_to_hash(doc["phash"])
#                 distance = perceptual_hash - stored_phash
#                 if distance <= 5:
#                     return {
#                         "status": "duplicate_perceptual",
#                         "imageId": str(doc["_id"]),
#                         "distance": distance
#                     }

#         #  AI Embedding duplicate check 
#         cursor = db["images"].find({}, {"embedding": 1})
#         async for doc in cursor:
#             if "embedding" in doc:
#                 stored_emb = np.array(doc["embedding"])
#                 sim = cosine_similarity(np.array(embedding), stored_emb)
#                 if sim >= 0.9:  
#                     return {
#                         "status": "duplicate_ai",
#                         "imageId": str(doc["_id"]),
#                         "similarity": sim
#                     }

         
#         gridfs_id = await fs.upload_from_stream(file.filename, contents)

#         doc = {
#             "filename": file.filename,
#             "hash": file_hash,
#             "phash": str(perceptual_hash),
#             "embedding": embedding,
#             "gridfs_id": gridfs_id,
#             "uploaded_at": datetime.utcnow().isoformat(),
#         }
#         result = await db["images"].insert_one(doc)

#         return {"status": "created", "imageId": str(result.inserted_id)}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))






# Version 4 AI Detector

from fastapi import FastAPI, UploadFile, File,Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import db
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from bson import ObjectId
import hashlib
from PIL import Image
import imagehash
import io
import numpy as np
from ml_utils import get_embedding, cosine_similarity 
from classifier_service import classify_image
import tempfile

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fs = AsyncIOMotorGridFSBucket(db)

# Exact duplicate hash
def get_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()

# Perceptual hash
def get_perceptual_hash(file_bytes: bytes):
    image = Image.open(io.BytesIO(file_bytes))
    return imagehash.phash(image)


@app.post("/api/images/upload")
async def upload_image(file: UploadFile = File(...),
                       model_name: str = Form("auto")):
    try:
        contents = await file.read()

        #  SHA256 Hash
        file_hash = get_file_hash(contents)
        #  Exact SHA256 duplicate check 
        existing = await db["images"].find_one({"hash": file_hash})
        if existing:
            return {"status": "duplicate_exact", "imageId": str(existing["_id"])}

        #  Perceptual Hash
        perceptual_hash = get_perceptual_hash(contents)

        #  Perceptual duplicate check 
        cursor = db["images"].find({}, {"phash": 1})
        async for doc in cursor:
            if "phash" in doc:
                stored_phash = imagehash.hex_to_hash(doc["phash"])
                distance = perceptual_hash - stored_phash
                if distance <= 5:
                    return {
                        "status": "duplicate_perceptual",
                        "imageId": str(doc["_id"]),
                        "distance": distance
                    }

        #  CNN Embedding
        embedding = get_embedding(contents).tolist()

        #  AI Embedding duplicate check 
        cursor = db["images"].find({}, {"embedding": 1})
        async for doc in cursor:
            if "embedding" in doc:
                stored_emb = np.array(doc["embedding"])
                sim = cosine_similarity(np.array(embedding), stored_emb)
                if sim >= 0.9:  
                    return {
                        "status": "duplicate_ai",
                        "imageId": str(doc["_id"]),
                        "similarity": sim
                    }
                
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        classification = await classify_image(tmp_path, model_choice=model_name)
        print(classification)
        if classification["result"][0].lower() == "ai":
            return {
                "status": "rejected_ai",
                "reason": "Image classified as AI-generated",
                "description": classification["result"][1]
            }        

         
        gridfs_id = await fs.upload_from_stream(file.filename, contents)

        doc = {
            "filename": file.filename,
            "hash": file_hash,
            "phash": str(perceptual_hash),
            "embedding": embedding,
            "gridfs_id": gridfs_id,
            "uploaded_at": datetime.utcnow().isoformat(),
        }

        result = await db["images"].insert_one(doc)

        return {"status": "created", "imageId": str(result.inserted_id)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



