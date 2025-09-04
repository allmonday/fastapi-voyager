from fastapi_router_viz.graph import Analytics
from pydantic import BaseModel
from fastapi import FastAPI
from typing import Optional

# 定义数据模型
class Base(BaseModel):
    id: int

class X(Base):
    id: int

class B(BaseModel):
    id: int
    value: str
    x: X

class A(BaseModel):
    id: int
    name: str
    b: B

class C(BaseModel):
    id: int
    name: str
    b: B
    x: X

class SubD(BaseModel):
    id: int
    
class D(BaseModel):
    id: int
    name: str
    sub_d: SubD

# 创建FastAPI应用实例
app = FastAPI(title="Demo API", description="A demo FastAPI application for router visualization")

@app.get("/test", response_model=Optional[A])
def get_a():
    """Get A model data"""
    return None

@app.get("/test2", response_model=Optional[C])
def get_c():
    """Get C model data"""
    return None

@app.get("/test3", response_model=Optional[D])
def get_d1():
    """Get D model data (endpoint 1)"""
    return None

@app.get("/test4", response_model=Optional[D])
def get_d2():
    """Get D model data (endpoint 2)"""
    return None


def test_analysis():
    """Test function to demonstrate the analytics"""
    analytics = Analytics()
    analytics.analysis(app)
    print(analytics.generate_dot())


if __name__ == "__main__":
    test_analysis()