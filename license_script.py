# Create this as a separate script: migrate_licenses.py
# Run this to fix existing license documents in your database

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from bson import ObjectId

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_license_documents():
    """Fix existing license documents to ensure they have all required fields"""
    
    # Connect to MongoDB (replace with your connection string)
    client = AsyncIOMotorClient("mongodb+srv://aiprojects789:IP1NwVwaBM0TosQI@drm.cmnzpag.mongodb.net/art_drm?retryWrites=true&w=majority")  # Replace with your MongoDB URL
    db = client.artdrm_db  # Replace with your database name

    try:
        # Get all license documents
        licenses_cursor = db.licenses.find({})
        licenses = await licenses_cursor.to_list(length=None)
        
        logger.info(f"Found {len(licenses)} license documents to check")
        
        updated_count = 0
        error_count = 0
        
        for license_doc in licenses:
            try:
                license_id = license_doc.get("license_id", "unknown")
                logger.info(f"Processing license {license_id}")
                
                # Check and fix missing fields
                updates = {}
                
                # Ensure datetime fields are properly formatted
                datetime_fields = ["start_date", "end_date", "created_at", "updated_at"]
                for field in datetime_fields:
                    if field in license_doc and license_doc[field]:
                        if isinstance(license_doc[field], str):
                            try:
                                # Try to parse the datetime string
                                dt = datetime.fromisoformat(license_doc[field].replace('Z', '+00:00'))
                                updates[field] = dt
                            except ValueError:
                                logger.warning(f"Could not parse datetime for {field}: {license_doc[field]}")
                
                # Add default values for missing optional fields
                if "is_active" not in license_doc:
                    updates["is_active"] = True
                    
                if "created_at" not in license_doc:
                    updates["created_at"] = datetime.utcnow()
                    
                if "updated_at" not in license_doc:
                    updates["updated_at"] = datetime.utcnow()
                
                # Ensure fee_paid is a float
                if "fee_paid" in license_doc and not isinstance(license_doc["fee_paid"], (int, float)):
                    try:
                        updates["fee_paid"] = float(license_doc["fee_paid"])
                    except (ValueError, TypeError):
                        updates["fee_paid"] = 0.1  # Default fee
                
                # Apply updates if any
                if updates:
                    logger.info(f"Updating license {license_id} with: {list(updates.keys())}")
                    await db.licenses.update_one(
                        {"_id": license_doc["_id"]},
                        {"$set": updates}
                    )
                    updated_count += 1
                else:
                    logger.info(f"License {license_id} is already valid")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing license {license_doc.get('license_id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Migration complete: {updated_count} updated, {error_count} errors")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(migrate_license_documents())