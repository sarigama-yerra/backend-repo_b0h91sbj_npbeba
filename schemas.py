from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl

# Collection: banner
class LocationPoint(BaseModel):
    lat: float
    long: float
    distance: Optional[float] = None
    district: Optional[str] = None

class Timing(BaseModel):
    start_time: datetime
    end_time: Optional[datetime] = None
    continuous: bool = False

class BannerBase(BaseModel):
    title: str
    category: Optional[str] = None  # e.g., festival

    # Type of banner content
    variant: Literal["banner", "text"] = "banner"

    # Common fields
    button_name: Optional[str] = None
    target_value: Optional[str] = None

    # Banner variant fields
    banner_image_url: Optional[str] = None

    # Text variant fields
    text: Optional[str] = None
    bg_color: Optional[str] = Field(default="#ffffff", description="Background color in hex")

    # Authenticity / ownership
    vendor: bool = False
    shinr: bool = False

    vendor_id: Optional[str] = None
    vendor_name: Optional[str] = None
    is_premium_vendor: Optional[bool] = None

    # Placement
    show_in_home_page: bool = False

    # Audience
    whom_to_show: Literal[
        "all",
        "customers_set",
        "new_joinee",
        "location_based"
    ] = "all"
    customers_file_name: Optional[str] = None
    locations: Optional[List[LocationPoint]] = None

    # Timing
    timing: Timing

    # Workflow
    status: Literal["active", "draft", "inactive"] = "draft"
    review_status: Literal["approved", "rejected", "pending"] = "pending"

class BannerCreate(BannerBase):
    pass

class BannerUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    variant: Optional[Literal["banner", "text"]] = None
    button_name: Optional[str] = None
    target_value: Optional[str] = None
    banner_image_url: Optional[str] = None
    text: Optional[str] = None
    bg_color: Optional[str] = None
    vendor: Optional[bool] = None
    shinr: Optional[bool] = None
    vendor_id: Optional[str] = None
    vendor_name: Optional[str] = None
    is_premium_vendor: Optional[bool] = None
    show_in_home_page: Optional[bool] = None
    whom_to_show: Optional[Literal["all", "customers_set", "new_joinee", "location_based"]] = None
    customers_file_name: Optional[str] = None
    locations: Optional[List[LocationPoint]] = None
    timing: Optional[Timing] = None
    status: Optional[Literal["active", "draft", "inactive"]] = None
    review_status: Optional[Literal["approved", "rejected", "pending"]] = None

class StatusUpdate(BaseModel):
    status: Optional[Literal["active", "draft", "inactive"]] = None
    review_status: Optional[Literal["approved", "rejected", "pending"]] = None

# Collection: vendor
class Vendor(BaseModel):
    name: str
    code: Optional[str] = None
    is_premium: bool = False

class VendorCreate(Vendor):
    pass
