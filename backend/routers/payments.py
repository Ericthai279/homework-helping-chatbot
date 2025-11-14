# from fastapi import APIRouter, Depends, HTTPException, Request, Response
# from sqlalchemy.orm import Session
# import stripe

# from db.database import get_db, SessionLocal
# from models import user as user_model
# from routers.auth import get_current_user
# from core.config import settings

# # --- Configure Stripe ---
# stripe.api_key = settings.STRIPE_SECRET_KEY
# # ------------------------

# router = APIRouter(
#     prefix="/payments",
#     tags=["payments"]
# )

# # This is the base URL for your frontend
# # FOR LOCAL: "http://127.0.0.1:8001"
# # FOR PROD: "https://your-live-website.com"
# FRONTEND_URL = "http://127.0.0.1:8001" 

# @router.post("/create-checkout-session")
# async def create_checkout_session(
#     current_user: user_model.User = Depends(get_current_user)
# ):
#     """
#     Creates a new Stripe checkout session for the logged-in user.
#     Redirects them to Stripe to pay.
#     """
#     try:
#         session = stripe.checkout.Session.create(
#             payment_method_types=['card'],
#             line_items=[
#                 {
#                     'price': settings.STRIPE_PRICE_ID, # Your Price ID from .env
#                     'quantity': 1,
#                 },
#             ],
#             mode='payment',
#             success_url=f"{FRONTEND_URL}?payment_status=success",
#             cancel_url=f"{FRONTEND_URL}?payment_status=cancel",
#             # We add the user's ID to the metadata so we know
#             # who to make "premium" when the webhook comes in.
#             client_reference_id=current_user.id 
#         )
#         return {"checkout_url": session.url}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")

# @router.post("/webhook")
# async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
#     """
#     Listens for the 'checkout.session.completed' event from Stripe.
#     When received, it verifies the request and updates the user
#     in the database to be a premium user.
#     """
#     payload = await request.body()
#     sig_header = request.headers.get('stripe-signature')
#     endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

#     try:
#         event = stripe.Webhook.construct_event(
#             payload, sig_header, endpoint_secret
#         )
#     except ValueError as e:
#         # Invalid payload
#         raise HTTPException(status_code=400, detail=str(e))
#     except stripe.error.SignatureVerificationError as e:
#         # Invalid signature
#         raise HTTPException(status_code=400, detail=str(e))

#     # Handle the checkout.session.completed event
#     if event['type'] == 'checkout.session.completed':
#         session = event['data']['object']
        
#         # Get the user_id we stored in the metadata
#         user_id = session.get('client_reference_id')

#         if user_id:
#             # Find the user in our database
#             user = db.query(user_model.User).filter(user_model.User.id == int(user_id)).first()
#             if user:
#                 # --- THIS IS THE GOAL ---
#                 # Update the user to be premium
#                 user.is_premium = True
#                 db.commit()
#                 print(f"User {user.email} (ID: {user_id}) has been upgraded to Premium.")
#                 # ------------------------
#             else:
#                 print(f"Webhook Error: User with ID {user_id} not found.")
#         else:
#             print("Webhook Error: client_reference_id not found in session.")

#     return Response(status_code=200)