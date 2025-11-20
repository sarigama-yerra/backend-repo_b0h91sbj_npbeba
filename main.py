import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import (
    BannerCreate,
    BannerUpdate,
    StatusUpdate,
    VendorCreate,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utilities
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)


def serialize_doc(doc):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    # Convert datetimes to isoformat strings for JSON safety
    for k, v in list(doc.items()):
        if isinstance(v, datetime):
            doc[k] = v.isoformat()
        if isinstance(v, list):
            new_list = []
            for item in v:
                if isinstance(item, dict):
                    for kk, vv in list(item.items()):
                        if isinstance(vv, datetime):
                            item[kk] = vv.isoformat()
                new_list.append(item)
            doc[k] = new_list
    return doc


@app.get("/")
def read_root():
    return {"message": "CMS Backend Running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# ------------------------- Vendors ---------------------------
@app.post("/api/vendors")
def create_vendor(vendor: VendorCreate):
    vendor_dict = vendor.model_dump()
    vendor_id = create_document("vendor", vendor_dict)
    return {"id": vendor_id}


@app.get("/api/vendors")
def list_vendors(q: Optional[str] = Query(None, description="Search by name or code"), premium: Optional[bool] = None, limit: int = 20):
    filter_dict = {}
    if q:
        filter_dict["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"code": {"$regex": q, "$options": "i"}},
        ]
    if premium is not None:
        filter_dict["is_premium"] = premium

    docs = get_documents("vendor", filter_dict, limit)
    return [serialize_doc(d) for d in docs]


# ------------------------- Banners ---------------------------
@app.post("/api/banners")
def create_banner(payload: BannerCreate):
    banner_dict = payload.model_dump()
    banner_id = create_document("banner", banner_dict)
    return {"id": banner_id}


@app.get("/api/banners")
def list_banners(
    q: Optional[str] = None,
    status: Optional[str] = None,
    review_status: Optional[str] = None,
    vendor: Optional[bool] = None,
    shinr: Optional[bool] = None,
    show_in_home_page: Optional[bool] = None,
    vendor_id: Optional[str] = None,
    category: Optional[str] = None,
    published_from: Optional[datetime] = None,
    published_to: Optional[datetime] = None,
    limit: int = 50,
):
    filter_dict = {}

    if q:
        filter_dict["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"text": {"$regex": q, "$options": "i"}},
            {"vendor_name": {"$regex": q, "$options": "i"}},
        ]

    if status:
        filter_dict["status"] = status
    if review_status:
        filter_dict["review_status"] = review_status
    if vendor is not None:
        filter_dict["vendor"] = vendor
    if shinr is not None:
        filter_dict["shinr"] = shinr
    if show_in_home_page is not None:
        filter_dict["show_in_home_page"] = show_in_home_page
    if vendor_id:
        filter_dict["vendor_id"] = vendor_id
    if category:
        filter_dict["category"] = category

    # Date filter by timing.start_time as publish date
    date_filter = {}
    if published_from:
        date_filter["$gte"] = published_from
    if published_to:
        date_filter["$lte"] = published_to
    if date_filter:
        filter_dict["timing.start_time"] = date_filter

    docs = get_documents("banner", filter_dict, limit)
    return [serialize_doc(d) for d in docs]


@app.get("/api/banners/{banner_id}")
def get_banner(banner_id: str):
    from bson import ObjectId

    if not ObjectId.is_valid(banner_id):
        raise HTTPException(status_code=400, detail="Invalid id")

    doc = db.banner.find_one({"_id": ObjectId(banner_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return serialize_doc(doc)


@app.patch("/api/banners/{banner_id}")
def update_banner(banner_id: str, payload: BannerUpdate):
    from bson import ObjectId

    if not ObjectId.is_valid(banner_id):
        raise HTTPException(status_code=400, detail="Invalid id")

    update = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    if not update:
        return {"updated": False}

    update["updated_at"] = datetime.utcnow()
    res = db.banner.update_one({"_id": ObjectId(banner_id)}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"updated": res.modified_count > 0}


@app.patch("/api/banners/{banner_id}/status")
def update_banner_status(banner_id: str, payload: StatusUpdate):
    from bson import ObjectId

    if not ObjectId.is_valid(banner_id):
        raise HTTPException(status_code=400, detail="Invalid id")

    update = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    if not update:
        return {"updated": False}

    update["updated_at"] = datetime.utcnow()
    res = db.banner.update_one({"_id": ObjectId(banner_id)}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"updated": res.modified_count > 0}


@app.delete("/api/banners/{banner_id}")
def delete_banner(banner_id: str):
    from bson import ObjectId

    if not ObjectId.is_valid(banner_id):
        raise HTTPException(status_code=400, detail="Invalid id")

    res = db.banner.delete_one({"_id": ObjectId(banner_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"deleted": True}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
