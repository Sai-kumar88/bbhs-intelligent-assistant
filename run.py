import uvicorn

if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("🚀 Starting BBHS AI ASSISTANT...")
    print("👉 Click here to open in your browser: http://127.0.0.1:8000/")
    print("=" * 65 + "\n")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
