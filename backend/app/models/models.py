from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from typing import Any
from pydantic_core import core_schema

class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, value) -> ObjectId:
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")
        return ObjectId(value)

class MongoBaseModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class BusinessBase(BaseModel):
    name: str
    owner_email: EmailStr
    settings: dict = Field(default_factory=dict, description="Custom settings for the business")

class BusinessCreate(BusinessBase):
    password: str

class Business(MongoBaseModel, BusinessBase):
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    stock: int = 0

class ProductCreate(ProductBase):
    pass

class Product(MongoBaseModel, ProductBase):
    business_id: str # Reference to business (could be ObjectId if stringent)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class OrderItem(BaseModel):
    product_id: str
    quantity: int
    price_at_purchase: float

class OrderBase(BaseModel):
    customer_name: str
    customer_phone: Optional[str] = None
    items: List[OrderItem]
    total_amount: float
    status: str = "pending" # pending, confirmed, shipped, delivered, cancelled

class OrderCreate(OrderBase):
    pass

class Order(MongoBaseModel, OrderBase):
    business_id: str
    order_date: datetime = Field(default_factory=datetime.utcnow)
