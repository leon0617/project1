#!/usr/bin/env python3
"""
Example script demonstrating the debug capture functionality.
This script creates a debug session, starts it, waits for some capture,
and then retrieves the captured events.

Usage:
    python example_debug_session.py https://example.com
"""
import asyncio
import sys
import httpx


async def run_debug_session(target_url: str, duration: int = 15):
    """Run a debug session for the given URL"""
    base_url = "http://localhost:8000/api/debug"
    
    async with httpx.AsyncClient() as client:
        # 1. Create session
        print(f"Creating debug session for {target_url}...")
        response = await client.post(
            f"{base_url}/sessions",
            json={
                "target_url": target_url,
                "duration_limit": duration
            }
        )
        
        if response.status_code != 200:
            print(f"Error creating session: {response.text}")
            return
            
        session = response.json()
        session_id = session["id"]
        print(f"✓ Session created (ID: {session_id})")
        
        # 2. Start session
        print(f"Starting debug session...")
        response = await client.post(f"{base_url}/sessions/{session_id}/start")
        
        if response.status_code != 200:
            print(f"Error starting session: {response.text}")
            return
            
        print(f"✓ Session started, capturing network events...")
        print(f"  Waiting {duration} seconds for capture...")
        
        # 3. Wait for capture
        await asyncio.sleep(duration)
        
        # 4. Stop session
        print(f"Stopping debug session...")
        response = await client.post(f"{base_url}/sessions/{session_id}/stop")
        
        if response.status_code != 200:
            print(f"Error stopping session: {response.text}")
            return
            
        print(f"✓ Session stopped")
        
        # 5. Get session details
        print(f"\nRetrieving captured events...")
        response = await client.get(f"{base_url}/sessions/{session_id}")
        
        if response.status_code != 200:
            print(f"Error getting session: {response.text}")
            return
            
        details = response.json()
        
        print(f"\n{'='*70}")
        print(f"Debug Session Summary")
        print(f"{'='*70}")
        print(f"Target URL: {details['target_url']}")
        print(f"Status: {details['status']}")
        print(f"Started: {details['started_at']}")
        print(f"Stopped: {details['stopped_at']}")
        print(f"\nNetwork Events Captured: {len(details['network_events'])}")
        print(f"Console Errors Captured: {len(details['console_errors'])}")
        
        # Show some network events
        if details['network_events']:
            print(f"\n{'='*70}")
            print(f"Network Events (first 10)")
            print(f"{'='*70}")
            
            for i, event in enumerate(details['network_events'][:10], 1):
                print(f"\n{i}. {event['event_type'].upper()}: {event['method'] or 'N/A'} {event['url'][:80]}")
                if event['status_code']:
                    print(f"   Status: {event['status_code']}")
                if event['resource_type']:
                    print(f"   Type: {event['resource_type']}")
        
        # Show console errors
        if details['console_errors']:
            print(f"\n{'='*70}")
            print(f"Console Errors")
            print(f"{'='*70}")
            
            for i, error in enumerate(details['console_errors'], 1):
                print(f"\n{i}. [{error['level'].upper()}] {error['message'][:100]}")
        
        print(f"\n{'='*70}")
        print(f"Session complete! View full details at:")
        print(f"http://localhost:8000/api/debug/sessions/{session_id}")
        print(f"{'='*70}\n")


async def main():
    if len(sys.argv) < 2:
        print("Usage: python example_debug_session.py <URL> [duration_seconds]")
        print("\nExample:")
        print("  python example_debug_session.py https://example.com 15")
        sys.exit(1)
    
    target_url = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    
    try:
        await run_debug_session(target_url, duration)
    except httpx.ConnectError:
        print("\n✗ Error: Could not connect to API server.")
        print("  Make sure the server is running at http://localhost:8000")
        print("  Start it with: uvicorn app.main:app --reload")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
