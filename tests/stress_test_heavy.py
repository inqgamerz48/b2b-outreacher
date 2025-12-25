
import asyncio
import aiohttp
import time
import random
import sys

BASE_URL = "http://localhost:8000"
NUM_USERS = 50       # Number of concurrent users
OPS_PER_USER = 20    # Operations per user
concurrency_limit = asyncio.Semaphore(100) # Limit max concurrent connections

async def register_and_login(session, user_id):
    username = f"stress_test_{user_id}_{int(time.time())}"
    password = "password123"
    
    # Register
    try:
        async with session.post(f"{BASE_URL}/register", data={"username": username, "password": password}) as resp:
            if resp.status != 200 and resp.status != 303:
                # print(f"Register failed for {username}: {resp.status}")
                return None
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

    # Login
    try:
        async with session.post(f"{BASE_URL}/login", data={"username": username, "password": password}, allow_redirects=False) as resp:
            if resp.status == 303:
                # Cookie is handled by session cookie jar automatically
                return username
            else:
                # print(f"Login failed for {username}: {resp.status}")
                return None
    except:
        return None

async def user_workflow(user_id):
    async with concurrency_limit:
        async with aiohttp.ClientSession() as session:
            username = await register_and_login(session, user_id)
            if not username:
                return {"errors": 1, "ops": 0}
            
            errors = 0
            ops = 0
            
            # Mix of reads and writes
            for i in range(OPS_PER_USER):
                try:
                    # Write Operation (Add to Brain)
                    data = {
                        "category": "stress_test",
                        "content": f"High load content piece {i} from {username}"
                    }
                    async with session.post(f"{BASE_URL}/brain/add", data=data) as resp:
                        if resp.status not in [200, 303]:
                            errors += 1
                        else:
                            ops += 1
                            
                    # Read Operation (Dashboard)
                    async with session.get(f"{BASE_URL}/dashboard") as resp:
                        if resp.status != 200:
                            errors += 1
                        else:
                            ops += 1
                            
                except Exception as e:
                    errors += 1
            
            return {"errors": errors, "ops": ops}

async def main():
    print(f"Starting Stress Test: {NUM_USERS} Users, {OPS_PER_USER * 2} Ops each")
    print(f"Target URL: {BASE_URL}")
    
    start_time = time.time()
    
    tasks = []
    for i in range(NUM_USERS):
        tasks.append(user_workflow(i))
        
    results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    total_ops = sum(r["ops"] for r in results)
    total_errors = sum(r["errors"] for r in results)
    
    print("\n" + "="*40)
    print(f"STRESS TEST RESULTS")
    print("="*40)
    print(f"Time Taken:     {total_time:.2f} seconds")
    print(f"Total Requests: {total_ops + total_errors}")
    print(f"Successful Ops: {total_ops}")
    print(f"Failed Ops:     {total_errors}")
    rps = (total_ops + total_errors) / total_time if total_time > 0 else 0
    print(f"RPS (Req/Sec):  {rps:.2f}")
    print("="*40)
    
    if total_errors > 0:
        print("System showed instability under load.")
    else:
        print("System handled load with 0 errors.")

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
             asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
