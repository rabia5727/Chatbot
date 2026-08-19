"""
Mock API Layer — Frontend Integration Placeholders.

EVERY function in this file is a FRONTEND PLACEHOLDER / MOCK FUNCTION.
They return hard-coded / randomized responses to simulate backend behavior
so the frontend UI can be fully built, demoed, and tested independently.

NO backend models, database, face_recognition, SQLite, bcrypt, RAG, LLM,
STT, or TTS are implemented here.

Clear TODO comments show where your backend teammate will connect their real APIs.
"""

import time
import random


# ---------------------------------------------------------------------
# AUTHENTICATION & FACE RECOGNITION PLACEHOLDERS
# ---------------------------------------------------------------------

def signup_user(full_name: str, email: str, password: str, face_image_bytes=None) -> dict:
    """
    Mock user signup with optional face enrollment image.

    # TODO (backend teammate):
    # Replace this mock response with your real API request, e.g.:
    #   POST /api/auth/signup
    #   body: {
    #       "full_name": full_name,
    #       "email": email,
    #       "password": password,
    #       "face_image": face_image_bytes  # send captured image to backend for enrollment
    #   }
    # Your backend should process the face, generate embeddings, hash password,
    # and save to database.
    # Return shape expected by frontend:
    #   {"success": bool, "message": str}
    """
    time.sleep(0.6)  # simulate network latency

    if not full_name or not email or not password:
        return {"success": False, "message": "Please fill in all required fields."}

    return {
        "success": True,
        "message": "Account created successfully. Face profile saved." if face_image_bytes else "Account created successfully. You can now log in.",
    }


def enroll_face(image_bytes) -> dict:
    """
    Mock face enrollment during signup.

    # TODO (backend teammate):
    # Replace this mock function with your real facial enrollment endpoint, e.g.:
    #   POST /api/auth/face-enroll
    #   multipart/form-data: {"image": image_bytes}
    # Your backend will extract facial features/embeddings and associate them
    # with the user profile in the database.
    # Return shape expected by frontend:
    #   {"success": bool, "message": str}
    """
    time.sleep(0.5)

    if image_bytes is None:
        return {"success": False, "message": "No face image captured."}

    return {
        "success": True,
        "message": "Face captured ✓",
    }


def login_user(email: str, password: str) -> dict:
    """
    Mock normal email + password login.

    # TODO (backend teammate):
    # Replace this mock response with your real login API call, e.g.:
    #   POST /api/auth/login
    #   body: {"email": email, "password": password}
    # Return shape expected by frontend:
    #   {"success": bool, "message": str, "user": {"name": str, "email": str}}
    """
    time.sleep(0.6)

    if not email or not password:
        return {"success": False, "message": "Please enter your email and password."}

    display_name = email.split("@")[0].replace(".", " ").title() or "User"

    return {
        "success": True,
        "message": "Logged in successfully.",
        "user": {"name": display_name, "email": email},
    }


def verify_face(image_bytes) -> dict:
    """
    Mock facial recognition authentication for "Login with Face".

    `image_bytes` is the raw camera image captured from st.camera_input.

    # TODO (backend teammate):
    # Send captured image to backend for face authentication, e.g.:
    #   POST /api/auth/face-verify
    #   multipart/form-data: {"image": image_bytes}
    # Your backend will compare the captured face embedding against stored database
    # embeddings and return success/failure.
    # Return shape expected by frontend:
    #   {"success": bool, "message": str, "user": {"name": str, "email": str} | None}
    """
    time.sleep(1.2)  # simulate model inference latency

    if image_bytes is None:
        return {"success": False, "message": "No face image captured.", "user": None}

    # Demo mock response: always succeeds once camera photo is captured.
    return {
        "success": True,
        "message": "Face verified ✓",
        "user": {"name": "Alex Morgan", "email": "alex.morgan@example.com"},
    }


# ---------------------------------------------------------------------
# CHATBOT & TOOL PLACEHOLDERS
# ---------------------------------------------------------------------

def send_chat_message(message: str, uploaded_file=None) -> dict:
    """
    Mock chatbot response dispatcher.

    # TODO (backend teammate):
    # Replace with your RAG / LLM / Tool-Calling backend endpoint, e.g.:
    #   POST /api/chat
    #   body: {"message": message, "file": uploaded_file}
    # Return shape expected by frontend:
    #   {
    #     "type": "normal" | "rag" | "weather",
    #     "answer": str,
    #     "source": str,
    #     "location": str,
    #     "temperature": str,
    #     "condition": str,
    #     "humidity": str
    #   }
    """
    time.sleep(0.8)
    lowered = (message or "").lower()

    if uploaded_file is not None or "document" in lowered or "pdf" in lowered:
        return {
            "type": "rag",
            "source": uploaded_file.name if uploaded_file else "project_document.pdf",
            "answer": (
                "The uploaded document covers system requirements, architectural "
                "overview, and deployment timelines. Ask a specific question to query further."
            ),
        }

    if "weather" in lowered:
        return {
            "type": "weather",
            "location": "Lahore, Pakistan",
            "temperature": "34°C",
            "condition": "Sunny",
            "humidity": "41%",
        }

    sample_replies = [
        "This is a frontend mock reply. Once connected, your backend LLM will generate real answers here.",
        "Great query! In production, this response will come from the language model pipeline.",
        "Here's a placeholder reply showing the clean message bubble formatting.",
    ]
    return {"type": "normal", "answer": random.choice(sample_replies)}


def upload_document(file) -> dict:
    """
    Mock document uploader.

    # TODO (backend teammate):
    # Replace with real document upload API request, e.g.:
    #   POST /api/documents/upload
    #   multipart/form-data: {"file": file}
    """
    time.sleep(0.4)
    if file is None:
        return {"success": False, "filename": None}
    return {"success": True, "filename": file.name}
