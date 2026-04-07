import uvicorn
from fastapi import FastAPI
from src.env import CyberEnvironment
from src.models import Action

app = FastAPI()
env = CyberEnvironment()

@app.get("/")
def read_root():
    return {"status": "Cyber-Sentinel Environment is live!"}

@app.post("/reset")
def reset():
    return env.reset()

@app.post("/step")
def step(action: Action):
    obs, reward, done, info = env.step(action)
    return {
        "observation": obs,
        "reward": reward,
        "done": done,
        "info": info
    }

@app.post("/state")
def state_post():
    return env.state()

@app.get("/state")
def state_get():
    return env.state()

def main():
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
