from pydantic import BaseModel

class CreateCheckoutSessionRequest(BaseModel):
    # Add fields if we need to pass specific price or quantity, 
    # but for now it's a fixed recharge amount so maybe empty or just user_id (which we get from auth)
    pass
